__author__ = 'christina'

def read_names(filename):
    with open(filename,'r',0) as f:
        lines = f.read().splitlines()
    return lines

