import os

SIDES = ('N', 'S')
SECTORS = 12
TILES = 32
IB = 6
CHANNELS = 64

OFF = -2200
ON = 2200

def load_mapping(file: str) -> dict:
    '''
    Load the mapping from the file and return a dictionary

    Parameters:
        file (str): File containing the mapping information

    Returns:
        dict: Dictionary containing the mapping information
    '''

    mapping = {}
    with open(file, 'r') as f:
        next(f)  # Skip the first line of the file
        for line in f:
            side, sector,tile, _, _, _, ib, channel = line.strip().split(',')
            side = side.strip().upper()
            sector = int(sector.strip())
            tile = int(tile.strip())
            ib = int(ib.strip())
            channel = int(channel.strip())
            if side == 'S':
                ib -= 6
            if side not in mapping:
                mapping[side] = {}
            if sector not in mapping[side]:
                mapping[side][sector] = {}
            if tile not in mapping[side][sector]:
                mapping[side][sector][tile] = (side, int(ib), int(channel))

    return mapping

def make_pattern(pattern: int, mapping: dict) -> tuple:
    '''
    Generate the pattern

    Parameters:
        pattern (int): Pattern number
        mapping (dict): Dictionary containing the mapping information

    Returns:
        list: List containing the pattern information
    '''
    trim = {}
    for side in SIDES:
        trim[side] = {}
        for ib in range (IB):
            trim[side][ib] = {}
            for channel in range(CHANNELS):
                trim[side][ib][channel] = 0

    trim_check = {}
    for side in SIDES:
        trim_check[side] = {}
        for sector in range (SECTORS):
            trim_check[side][sector] = {}
            for tile in range(TILES):
                trim_check[side][sector][tile] = 0

    # All off
    if pattern == 1:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    side, ib, channel = mapping[side][sector][tile]
                    trim[side][ib][channel] = OFF
                    trim_check[side][sector][tile] = OFF

    # All on
    if pattern == 2:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    side, ib, channel = mapping[side][sector][tile]
                    trim[side][ib][channel] = ON
                    trim_check[side][sector][tile] = ON

    # North off, south on
    if pattern == 3:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if side == 'N':
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON

    # Odd sectors off, even on
    if pattern == 4:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if sector % 2 == 0:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON

    # Sectors 1-6 off, 7-12 on
    if pattern == 5:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if sector < 6:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON
    
    # Sectors 0, 1, 6, and 7 off, rest on
    if pattern == 6:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if sector in [0, 1, 6, 7]:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON

    # Sectors 2, 3, 8, 9 off, rest on
    if pattern == 7:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if sector in [2, 3, 8, 9]:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON

    # Odd tiles off, even on
    if pattern == 8:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if tile % 2 == 0:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON

    # Tiles 0-15 off, 16-31 on
    if pattern == 9:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if tile < 16:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON

    # Tiles 0-7 off, 8-15 on, 16-23 off, 24-31 on
    if pattern == 10:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if tile in range(8) or tile in range(16, 24):
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON

    # tiles 0-3 off, 4-7 on, 8-11 off, 12-15 on, 16-19 off, 20-23 on, 24-27 off, 28-31 on
    if pattern == 11:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if tile in range(4) or tile in range(8, 12) or tile in range(16, 20) or tile in range(24, 28):
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON

    # tiles 0-1 off, 2-3 on, 4-5 off, 6-7 on, 8-9 off, 10-11 on, 12-13 off, 14-15 on, 16-17 off, 18-19 on, 20-21 off, 22-23 on, 24-25 off, 26-27 on, 28-29 off, 30-31 on
    if pattern == 12:
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    if tile in range(2) or tile in range(4, 6) or tile in range(8, 10) or tile in range(12, 14) or tile in range(16, 18) or tile in range(20, 22) or tile in range(24, 26) or tile in range(28, 30):
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = OFF
                        trim_check[side][sector][tile] = OFF
                    else:
                        side, ib, channel = mapping[side][sector][tile]
                        trim[side][ib][channel] = ON
                        trim_check[side][sector][tile] = ON

    return (trim, trim_check)

def write_pattern(file: str, trims: tuple):
    '''
    Write the pattern to a file

    Parameters:
        pattern (int): Pattern number
        trim (dict): Dictionary containing the pattern information
        mapping (dict): Dictionary containing the mapping information
    '''
    trim, trim_check = trims

    with open(file, 'w') as f:
        print(f'Writing pattern {file}')
        f.write(f'side ib channel trim\n')
        for side in SIDES:
            for ib in range (IB):
                f.write(f'BOARD {side} {ib} 55\n')
                for channel in range(CHANNELS):
                    f.write(f'CHANNEL {side} {ib} {channel} {trim[side][ib][channel]}\n')

    with open(file.replace('.txt', '_check.txt'), 'w') as f:
        print(f'Writing pattern {file.replace(".txt", "_check.txt")}')
        for side in SIDES:
            for sector in range (SECTORS):
                for tile in range(TILES):
                    f.write(f'{side} {sector} {tile} {trim_check[side][sector][tile]}\n')

def main():
    mapping = load_mapping('sEPDMapping.txt')
    # make a folder for the patterns
    os.makedirs('patterns', exist_ok=True)
    for pattern in range(1, 13):
        trim = make_pattern(pattern, mapping)
        write_pattern(os.path.join('patterns', f'pattern_{pattern}.txt'), trim)

if __name__ == '__main__':
    main()
