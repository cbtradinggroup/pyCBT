

def exist(filename):
    """Check if a given file path exist

    Returns
    -------
        True if filename exist, False if do not.
    """
    try:
        with open(filename, "r") as _file: pass
    except IOError:
        return False
    else:
        return True
