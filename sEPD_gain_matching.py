import ROOT

def load_run(run_info: dict) -> ROOT.RDataFrame:
    '''
    Load the run information from the dictionary and return a pandas DataFrame object

    Parameters:
        run_info (dict): Dictionary containing the run information


    Returns:
        pd.DataFrame: DataFrame object
    '''

    # How do I want to do this?  WD409 is the simple option, it spits out a ttree.  I could
    # then read that with an RDataFrame, keeping things in the root ecosystem.  Or I could do it
    # the right way and use the production chain to process the waveforms.  WD409 sounds easy..... 

    # Copy the files somewhere useful
    


    #
