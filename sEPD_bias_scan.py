#! /usr/bin/python3

import datetime
import os
import subprocess
import sys
import time
import json
import telnetlib
import argparse
import logging

import config

def generate_bias_map(voltages: list) -> str:
    '''
    Generates the bias map for a particular voltage.
    Returns the file name of the bias map.

    Parameters:
        voltage: list - The list of voltage to generate the bias map
                        for.  The list should be 6 elements long.

    Returns:
        str - The file name of the bias map.
    '''
    lines = []
    with open('sEPD_HVSet_template.txt', 'r') as f:
        lines = f.readlines()
    file_name = os.path.join(config.BIAS_MAPS_FOLDER, f'sEPD_HVSet_{config.TIMESTAMP}.txt')
    with open(file_name, 'w') as f:
        for i, line in enumerate(lines):
            f.write(line.format(voltages[i]))
    return file_name

def load_bias_map(file_name: str) -> None:
    '''
    Load the bias map into the bias control system.

    Parameters:
        file_name: str - The file name of the bias map to load.

    Returns:
        None
    '''
    # move the file to the bias control folder
    os.rename(file_name, os.path.join(config.BIAS_CONTROL_FOLDER, 'sEPD_HVSet.txt'))
    # load the bias map
    # subprocess.run(['bash', os.path.join(config.BIAS_CONTROL_FOLDER, 'sEPD_Init.sh')])
    # Wait for bias supply to stabilize
    # time.sleep(1)
    print(f'Bias map loaded to {os.path.join(config.BIAS_CONTROL_FOLDER, 'sEPD_HVSet.txt')}.  Run sEPD_init.sh to load the bias map.')

def record_events(n_events: int, ) -> dict:
    '''
    Take a run with n events.

    Parameters:
        n_events: int - The number of events to record.
        test: bool - If True, simulate running the DAQ.

    Returns:
        dict - Information about the run.
    '''
    run_info = {}
    return run_info # SHORT CIRCUIT EVERYTHING.  No longer running in this mode
    if config.SIMULATE:
        run_info['run_number'] = 1
        run_info['file_path'] = 'test_file_path'
        run_info['num_events'] = n_events
        return run_info

    subprocess.run(['jseb2client', 'init', config.SEB])
    
    # Start run 
    logging.info('Starting run')
    run_number = subprocess.check_output(['rcdaq_client', 'daq_begin']).split()[3]
    run_number = int(run_number)
    run_info['run_number'] = run_number

    subprocess.run(['gl1_gtm_client', 'gtm_startrun', config.VGTM])
    # Run until desired number of events are collected
    while (int(subprocess.check_output(['rcdaq_client', 'daq_get_numberevents'])) < n_events):
        time.sleep(5)
    
    # Stop run
    logging.info('Stopping run')
    subprocess.run(['gl1_gtm_client', 'gtm_stop', config.VGTM])
    subprocess.run(['rcdaq_client', 'daq_end'])
    time.sleep(0.5)
    file_name = subprocess.check_output(['rcdaq_client', 'daq_get_lastfilename']).decode()
    run_info['file_path'] = str(file_name).strip()
    number_events = subprocess.check_output(['rcdaq_client', 'daq_get_last_event_number'])
    run_info['num_events'] = int(number_events)
    return run_info
    
def run_scans(voltages: list) -> dict:
    '''
    Run the bias scan for a list of voltages.

    Parameters:
        voltages: list - A list of voltages to scan.

    Returns:
        dict - Information about the scans.
    '''
    # Backup the current bias map with timestamp
    backup_file_name = f'sEPD_HVSet_backup_{config.TIMESTAMP}.txt'
    logging.info(f'Backing up current bias map to {backup_file_name}')
    subprocess.run(['cp', os.path.join(config.BIAS_CONTROL_FOLDER, 'sEPD_HVSet.txt'), os.path.join(config.BIAS_MAPS_FOLDER, backup_file_name)])

    scan_info = {}
    for voltage in voltages:
        voltage = float(voltage)
        bias_map = generate_bias_map(voltage)
        load_bias_map(bias_map)
        scan_info[voltage] = record_events(1000)

    # Save scan info to JSON file
    with open(f'run_info/scan_info_{config.TIMESTAMP}.json', 'w') as f:
        json.dump(scan_info, f, indent=4)

    # Restore the backup bias map, keeping a copy
    logging.info(f'Restoring backup bias map')
    subprocess.run(['cp', os.path.join(config.BIAS_MAPS_FOLDER, backup_file_name), os.path.join(config.BIAS_CONTROL_FOLDER, 'sEPD_HVSet.txt')])

    return scan_info

def send_command(tn: telnetlib.Telnet, command: str) -> str:
    '''
    Send a command to the bias control system and return the response.

    Parameters:
        tn: telnetlib.Telnet - The telnet connection to the bias control system.
        command: str - The command to send.

    Returns:
        str - The response from the bias control system.
    '''
    logging.debug(f'Sending command: {command}')
    tn.write(command.encode('ascii') + b'\n')
    response = tn.read_until(b'>').decode('ascii')
    logging.debug(f'Response: {response}')
    return response

def read_trim_voltage_file(file_name: str) -> tuple:
    '''
    Read the trim voltage file and return the contents as a dictionary.

    Parameters:
        file_name: str - The file name of the trim voltage file.

    Returns:
        dict - The contents of the trim voltage file.
    '''
    trim_voltages = {}
    board_voltages = {}
    # check if the file exists
    if not os.path.exists(file_name):
        logging.critical(f'Error: File {file_name} does not exist')
        sys.exit(1)
    with open(file_name, 'r') as f:
        lines = f.readlines()
    for line in lines[1:]: # skip the header
        line_info = line.split()
        if line_info[0] == 'CHANNEL':
            _, side, ib, i, v = line_info
            ib = int(ib)
            i = int(i)
            v = int(v)
            if side not in trim_voltages:
                trim_voltages[side] = {}
            if ib not in trim_voltages[side]:
                trim_voltages[side][ib] = {}
            if i not in trim_voltages[side][ib]:
                trim_voltages[side][ib][i] = v
            elif line_info[0] == 'BOARD':
                _, side, ib, v = line_info
                ib = int(ib)
                v = int(v)
                if side not in board_voltages:
                    board_voltages[side] = {}
                board_voltages[side][ib] = v
    # Check that all channels are present
    success = True
    for side in ['N', 'S']:
        for ib in range(6):
            for i in range(64):
                if i not in trim_voltages[side][ib]:
                    logging.error(f'Missing channel: Side={side}, IB={ib}, I={i}')
                    success = False

    voltages = []
    for side in ['N', 'S']:
        for ib in range (6):
            if ib not in board_voltages[side]:
                logging.error(f'Missing board voltage: Side={side}, IB={ib}')
                success = False
            else:
                voltages.append(board_voltages[side][ib])

    if not success:
        logging.error('Trim voltage file is invalid.  Exiting.')
        sys.exit(1)
    
    return (trim_voltages, voltages)

def write_trim_voltage_file(file_name: str, trim_voltages: dict, biases: dict) -> None:
    '''
    Write the trim voltages to a file.

    Parameters:
        file_name: str - The file name of the trim voltage file.
        trim_voltages: dict - The trim voltages to write to the file.

    Returns:
        None
    '''
    with open(file_name, 'w') as f:
        # print a header
        f.write('Side IB I Voltage\n')
        for side in ['N', 'S']:
            for ib in trim_voltages[side]:
                f.write(f'BOARD {side} {ib} {biases[side][ib]}\n')
                for i in trim_voltages[side][ib]:
                    v = trim_voltages[side][ib][i]
                    f.write(f'CHANNEL {side} {ib} {i} {v}\n')

def generate_empty_trim_file(base_voltage: float, file_name: str) -> None:
    '''
    Generate an empty trim voltage file.

    Parameters:
        file_name: str - The file name of the trim voltage file.

    Returns:
        None
    '''
    trim_voltages = {}
    bias_voltages = {}
    for side in ['N', 'S']:
        trim_voltages[side] = {}
        bias_voltages[side] = {}
        for ib in range(6):
            trim_voltages[side][ib] = {}
            bias_voltages[side][ib] = base_voltage
            for i in range(64):
                trim_voltages[side][ib][i] = 0
    write_trim_voltage_file(file_name, trim_voltages, bias_voltages)

def get_trim_voltages() -> dict:
    ''' 
    Get the currently loaded trip voltages from the bias control system.

    Parameters:
        None

    Returns:
        dict - The trim voltages.
    '''
    north_tn = None
    south_tn = None
    if not config.SIMULATE:
        north_tn = telnetlib.Telnet(config.NORTH_IP, config.PORT)
        south_tn = telnetlib.Telnet(config.SOUTH_IP, config.PORT)

    trim_voltages = {}
    cmd_prefix = '$GR'
    for side in ['N', 'S']:
        trim_voltages[side] = {}
        for ib in range(6):
            trim_voltages[side][ib] = {}
            # Send command to get the trim voltage
            cmd = '%s%01d\n\r' % (cmd_prefix, ib)
            # Read the response
            if config.SIMULATE:
                response = ' '.join(['0\n' for i in range(64)])
            else:
                if side == 'N':
                    response = send_command(north_tn, cmd)
                else:
                    response = send_command(south_tn, cmd)
            voltages = response.rstrip().lstrip().replace('\r', ' ').split('\n')
            logging.debug(f'Voltages: {voltages}')
            for i, voltage in enumerate(voltages[:-1]):
                trim_voltages[side][ib][i] = int(voltage)
    return trim_voltages


def set_trim_voltages(trim_map: dict, ) -> bool:
    '''
    Set the trim voltages on the bias control system.

    Parameters:
        trim_map: dict - The trim voltages to set.

    Returns:
        None
    '''

    cmd_prefix = '$GS'
    north_cmd_list = []
    south_cmd_list = []
    for ib in range(6):
        for i in range(64):
            north_val = trim_map['N'][ib][i]
            south_val = trim_map['S'][ib][i]

            if abs(north_val) > 2500:
                logging.error(f'Invalid trim voltage: Side=N, IB={ib}, I={i}, Voltage={north_val}.  0 will be used instead.')
                north_val = 0
            if abs(south_val) > 2500:
                logging.error(f'Invalid trim voltage: Side=S, IB={ib}, I={i}, Voltage={south_val}.  0 will be used instead.')
                south_val = 0
            
            north_cmd_list.append('%s%01d%02d%s\n\r' % (cmd_prefix, ib, i, str(north_val)))
            south_cmd_list.append('%s%01d%02d%s\n\r' % (cmd_prefix, ib, i, str(south_val)))
    
    if config.SIMULATE:
        logging.info('Generated command list')
        logging.info('North:')
        logging.info(north_cmd_list)
        logging.info('South:')
        logging.info(south_cmd_list)
        return True
    
    with telnetlib.Telnet(config.NORTH_IP, config.PORT) as north_tn:
        for cmd in north_cmd_list:
            send_command(north_tn, cmd)
    with telnetlib.Telnet(config.SOUTH_IP, config.PORT) as south_tn:
        for cmd in south_cmd_list:
            send_command(south_tn, cmd)

    # Readback the trim voltages to verify they were set correctly
    new_trim_voltages = get_trim_voltages()
    match = True
    for side in ['N', 'S']:
        for ib in range(6):
            for i in range(64):
                if trim_map[side][ib][i] != new_trim_voltages[side][ib][i]:
                    match = False
                    logging.warning(f'Trim voltage mismatch: Side={side}, IB={ib}, I={i}, Request={trim_map[side][ib][i]}, Readback={new_trim_voltages[side][ib][i]}')
    return match


def main(argv):
    parser = argparse.ArgumentParser(description='sEPD Bias Scan')
    # parser.add_argument('--mode', metavar='mode', type=str, help='mode of operation' , choices=['scan', 'generate_demo', 'set'], required=True)
    # parser.add_argument('--scan', metavar='v1 v2', type=float, nargs='*', default=[], help='Run bias scan for voltages v1 v2 ... vn')
    parser.add_argument('--generate_demo', action='store_true', help='Generate a demo trim voltage file')
    parser.add_argument('--set_base', metavar='voltage', type=float, help='Set the base voltage for the bias scan')
    parser.add_argument('--backup', action='store_true', help='Backup the current bias map')
    parser.add_argument('--set', metavar='file_name', type=str, help='Set the trim voltages to the values in the specified trim voltage file')
    parser.add_argument('--get', metavar='output_file_name', type=str, help='Stores the currently loaded trim voltages in the specified file')

    # Add logging options
    parser.add_argument('--log', metavar='log_level', type=str, default='INFO', help='Set the logging level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log))

    # make all needed folders
    os.makedirs(config.BIAS_MAPS_FOLDER, exist_ok=True)
    os.makedirs('run_info', exist_ok=True)

    if args.backup:
        # backup bias and trim
        subprocess.run(['cp', os.path.join(config.BIAS_CONTROL_FOLDER, 'sEPD_HVSet.txt'), os.path.join(config.BIAS_MAPS_FOLDER, f'sEPD_HVSet_backup_{config.TIMESTAMP}.txt')])
        original_trim_voltages = get_trim_voltages()
        write_trim_voltage_file(os.path.join(config.BIAS_MAPS_FOLDER, f'trim_voltages_{config.TIMESTAMP}.txt'), original_trim_voltages)
        logging.info(f'Backup complete: timestamp {config.TIMESTAMP}')


    # if args.scan:
    #     # Save current trim voltages
    #     original_trim_voltages = get_trim_voltages()
    #     write_trim_voltage_file(os.path.join(config.BIAS_MAPS_FOLDER, f'trim_voltages_{config.TIMESTAMP}.txt'), original_trim_voltages)
        
    #     # Generate 0 trim map file
    #     generate_empty_trim_file(os.path.join(config.BIAS_MAPS_FOLDER, 'trim_zero.txt'))
    #     set_trim_voltages(read_trim_voltage_file(os.path.join(config.BIAS_MAPS_FOLDER, 'trim_zero.txt')), )
    #     run_scans(args.scan)

    #     # Restore original trim voltages
    #     set_trim_voltages(original_trim_voltages)

    if args.generate_demo:
        logging.info('Generating demo trim voltage file')
        generate_empty_trim_file(os.path.join(config.BIAS_MAPS_FOLDER, 'trim_voltages.txt'))

    elif args.set_base:
        # Set a bias voltage
        if args.set_base < 0 or args.set_base > 60:
            logging.error('Invalid base voltage.  Must be between 0 and 60')
            sys.exit(1)
        base_voltage = args.set_base

        # Set the trim voltages to 0
        generate_empty_trim_file(base_voltage, os.path.join(config.BIAS_MAPS_FOLDER, 'trim_zero.txt'))
        trim_voltages, board_voltages = read_trim_voltage_file(os.path.join(config.BIAS_MAPS_FOLDER, 'trim_zero.txt'))
        set_trim_voltages(trim_voltages)
        bias_map = generate_bias_map(board_voltages)
        load_bias_map(bias_map)

    elif args.set:
        trim_voltages, board_voltages = read_trim_voltage_file(args.set)
        set_trim_voltages(trim_voltages)
        bias_map = generate_bias_map(board_voltages)
        load_bias_map(bias_map)

    elif args.get:
        trim_voltages = get_trim_voltages()
        write_trim_voltage_file(args.get, trim_voltages)

if __name__ == '__main__':
    main(sys.argv)
