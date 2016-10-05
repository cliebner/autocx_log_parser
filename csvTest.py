__author__ = 'christina'

import glob, csv

def get_files():
    # get directory from user
    file_dir = raw_input('what folder? use \ instead of /: ')+'/*'

    # get list of filenames
    filenames = glob.glob(file_dir)
    filenames_clean = []
    for i in range(len(filenames)):
        front, sep, end = filenames[i].rpartition('\\')
        filenames_clean.append(end)
    return filenames, filenames_clean
    # parse filenames

def count_lines(filehandle):
    count = 0
    for f in filehandle:
        count += 1
    return count

def unpack_file(reader_obj):
    #initialize a list that contains all lines:
    lines_list = []
    for row in reader_obj:
        lines_list.append(row)
    return lines_list

def get_file_info(filename):
    '''
    input: file name object
    output: tuple of useful info about the file:
        list containing lines in the file (cleaned of newlines)
        length of list (number of lines/rows in the file)
        width of list (number of columns in the file)
    '''
    with open(filename, 'rb') as f:
        reader_obj = csv.reader(f)
        file_list = unpack_file(reader_obj)
        num_rows = len(file_list)
        if num_rows > 0:
            num_cols = len(file_list[0])
        else: num_cols = 0
    return file_list, num_rows, num_cols

def get_col_list(file_list,i_col):
    '''
    :param file_list: list from csv reader
    :param i_col: index of column that this function should isolate
    :return: list containing values from column specified by i_col
    '''
    col_list = []
    for n in file_list:
        col_list.append(n[i_col])
    return col_list

def get_file_lengths(filenames):
    lengths = []
    count = 0
    for f in filenames:
        print count
        a, length, c = get_file_info(f)
        lengths.append(length)
        count += 1
    return lengths

def find_empty(lengths, filenames):
    '''
    use this function to find empty files
    :param lengths: list of lengths of all file in the source folder
    :param filenames: list of all file names in the source folder
    :return: tuple: list of filenames that are empty
            list of indices where the empty filenames are
    '''
    filename_list = []
    index_empty = []
    for i in range(len(lengths)):
        if lengths[i] == 0:
            filename_list.append(filenames[i])
            index_empty.append(i)
    return filename_list, index_empty

def get_unique_list(filenames, separator_list):
    '''
    use this function to find unique list
    :param filenames:
    :return:
    '''
    unique_list = []
    for f in filenames:
        # split the filename around the first separator
        top, sep, btm = f.rpartition(separator_list[0])
        # pass the btm to the next partition call, around the second separator
        # we want to keep the top of the second partition
        top, sep, btm = btm.partition(separator_list[1])
        # if it's not there yet, add it to the list.
        # else, don't add it
        if top not in unique_list:
            unique_list.append(top)
    return unique_list

