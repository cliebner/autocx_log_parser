__author__ = 'christina'


import glob
import pandas as pd
import matplotlib.dates as dates
import matplotlib.pyplot as plt
import math as math

TRENDS_PER_SUBPLOT = 5
MAX_SUBPLOT_ROWS = 5
ROW_SIZE = 5  # inches
COL_SIZE = 7  # inches
setD = {
    'n': 'INTERSECTION',
    'u': 'UNION'
}

PATHS = [
    'measure_damper_opening_real',
    'measure_mdot_real',
    'actuator_u_damper_opening_real',
    'actuator_u_damper_opening_lock_real',
    'measure_Ts_T',
    'measure_zone_temp',
    'actuator_u_hv_lock_real',
    'measure_hv_real',
    'actuator_u_static_pressure_real',
    'measure_static_pressure_stpt_real',
    'none'
]

PREREQ_PATHS = [
    'ColdDuctPressure',
    'ColdDuctTemperature',
    'HotDuctPressure',
    'HotWaterPressure',
    'HotWaterTemperature'
]

TREND_UNITS = dict(zip(PATHS, [
    '%',
    'cfm',
    '%',
    '1=on, 0=off',
    'deg F',
    'deg F',
    '1=on, 0=off',
    '%',
    'in wg',
    'in wg',
    '[ ]'
]))

TREND_TITLES = dict(zip(PATHS, [
    'Damper Position',
    'Zone Airflow',
    'Damper Position',
    'Damper Position - Lock',
    'Supply Air Temperature',
    'Zone Temperature',
    'HW Valve Position - Lock',
    'HW Valve Position',
    'Duct Static Pressure',
    'Duct Static Pressure',
    '[ ]'
]))

Y_LIMS = dict(zip(PATHS, [
    [0,100],
    [None, None],
    [0,100],
    [0,1.3],
    [None, None],
    [None, None],
    [0,1.3],
    [0,100],
    [None, None],
    [None, None],
    [None, None]
]))

PREREQ_THRESHOLDS = dict(zip(PREREQ_PATHS, [
    0.25,
    70,
    0.25,
    5,
    140
]))

SEPARATORS = dict(zip(PATHS, [
    ['\\','_site'],
    ['\\','_site'],
    ['\\','_site'],
    ['\\','_site'],
    ['__','_site'],
    ['\\','_site'],
    ['\\','_site'],
    ['\\','_site'],
    ['__','_site'],
    ['__','_site'],
    [None, None]
]))


def get_folder_info(fullPath):
    '''
    user input: full path of folder directory where data files are stored
    :return: list containing filenames as strings
            number of files in folder
    '''
    # get directory from user
    file_dir = fullPath+'/*'
    # get list of filenames
    filenames = glob.glob(file_dir)
    return filenames

def get_file_info(filename):
    '''
    This function reads the file into a pandas dataframe
    :param filename to read, assumes no header in file
    :return: a pandas dataframe object
    '''

    # read a file using pandas, with first column as datetime index
    dataFrame = pd.read_csv(filename, sep=',', header=None, index_col=0, parse_dates=True)
    # mutate/convert pandas datetime index to python datetime
    dataFrame.index = dates.date2num(dataFrame.index.to_pydatetime())
    return dataFrame

def get_all_files_info(filenames):
    '''
    This function calls get_file_info on all files in filenames list and returns a list of pandas dataframes
    :param filenames: list of files we care about, e.g. all files in folder, all files that match filter criteria
    :return: all_data_list: each list element is a pandas dataframe containing the file data. It skips empty files
               empty_list: list of filenames where file is empty
               index_empty: index where empty file occurs
    '''
    # initialize lists
    data_list = []
    data_names = []
    empty_list = []
    index_empty = []

    for f in range(len(filenames)):
        try:
            data = get_file_info(filenames[f])
        except ValueError:
            empty_list.append(filenames[f])
            index_empty.append(f)
        else:
            if len(data) == 0:
                empty_list.append(filenames[f])
                index_empty.append(f)
            else:
                data_list.append(data)
                data_names.append(filenames[f])
    # return data_list, data_names, empty_list, index_empty
    return data_list, data_names

def get_parsed_list(filenames, start=(), end=(), unique=False, addSep0=False, addSep1=False):
    '''
    use this function to create a list of filenames parsed by the provided separators.
    use selector to make a unique list, default will make a full list
    :param filenames:
    :return:
    '''
    file_list = []
    for f in filenames:

        for s in start:

        # split the filename around the first separator
        # pass the btm to the next partition call, around the second separator
        # we want to keep the top of the second partition
        top, sep0, btm = f.rpartition(separator_list[0])
        if addSep0:
            btm = sep0+btm
        top, sep1, btm = btm.partition(separator_list[1])
        if addSep1:
            top = top+sep1
        if unique:
            if top not in file_list:
                file_list.append(top)
        else:
            file_list.append(top)
    file_list.sort()
    return file_list

def filter_data(filterListTuple, filenames):
    '''
    This function creates a list of filenames that match all supplied filters.
    First finds intersection set of filters, then finds union set of filters.
    This function is a wrapper for a recursive function.
    :param
        filterListTuple: tuple of lists, defined as
            (
            keywords to use for intersection,
            keywords to use for union
            prereq names to use for intersection,
            prereq names to use for union
            )
    :param filenames: list of filenames to filter on

    :return:
        filtered_filenames
    '''
    # unpack tuple param:
    n_keywordList = filterListTuple[0]
    u_keywordList = filterListTuple[1]
    n_prereqList = filterListTuple[2]
    u_prereqList = filterListTuple[3]

    # initialize:
    n_keywordNames = []
    u_keywordNames = []
    n_prereqNames = []
    u_prereqNames = []

    # For keyword intersection set, iterate through filters recursively so filters build on each other
    if n_keywordList:
        fNames = filenames[:]
        count = 0
        n_keywordNames = filterRecur(count, n_keywordList, fNames)

    # For keyword union set, call filter individually and then extend the list
    if not n_keywordNames:  # no filtering has been done yet
        fNames = filenames[:]
    else:  # some filtering has happened, so use results to date as base for union filtering
        fNames = n_keywordNames
    for u in u_keywordList:
        count = 0
        u_keywordNames += filterRecur(count, [u], fNames)

    # if there were any union filters, result is u_keywords
    if u_keywordList:
        keywordNames = u_keywordNames
    else:
        keywordNames = n_keywordNames

    # Prereqs are optional to include, so must be added to keyword filter list, not compound.
    # For prereq name intersection set, iterate through filters recursively, but start with full set
    fNames = filenames[:]
    if n_prereqList:
        count = 0
        n_prereqNames = filterRecur(count, n_prereqList, fNames)

    # For prereq name union set, call filter individually and then extend the list
    if not n_prereqNames:  # no filtering has been done yet
        fNames = filenames[:]
    else:  # some filtering has happened, so use results to date as base for union filtering
        fNames = n_prereqNames
    for u in u_prereqList:
        count = 0
        u_prereqNames += filterRecur(count, [u], fNames)

    # if there were any union filters, result is u_keywords
    if u_prereqList:
        prereqNames = u_prereqNames
    else:
        prereqNames = n_prereqNames

    resultNames = keywordNames + prereqNames
    return resultNames

def filterRecur(count, filterList, filtered_filenames):
    # initialize local variables:
    new_filenames = []

    # base case: when there is nothing (left) to filter
    if count >= len(filterList):
        return filtered_filenames
    # warning case: list of filenames is empty and there is nothing to filter on
    elif len(filtered_filenames) == 0:
        print 'nothing to filter. review target filenames and filters.'
        return filtered_filenames
    # recursion case:
    else:
        for f in range(len(filtered_filenames)):
            if filterList[count] in filtered_filenames[f]:
                new_filenames.append(filtered_filenames[f])
        # update
        count += 1
        filtered_filenames = new_filenames
        return filterRecur(count, filterList, filtered_filenames)

def get_filter_list(setType):

    #initialize:
    inputList = []

    # interact with user: show available Filter Types, Filters, and get Filter Type:Filter pairs
    while True:
        userInput = raw_input('Enter ' + setD[setType] + ' filters. Use commas to separate. Type "." when done: ')
        if userInput == '.':
            break
        else:
            inputList.append(userInput)

    # break up strings by commas:
    newList = []
    for i in inputList:
        newList.extend(i.split(','))

    return newList

def plot_filtered_data(dataTuple, filtersTuple):

    if len(dataTuple[0]) > 0:
        make_subplot(dataTuple, filtersTuple)
    else:
        print 'No data available to plot. Check filter spelling, mutually exclusive filters, etc.'


def make_subplot(dataTuple, filtersTuple):
    '''
    This function will dynamically create many subplots.
    ** If names are all of one pathName, then they are all the same unit and have the same y axis. Can make any m x n
    subplot grid. Subplot grid is limited to MAX_SUBPLOT_ROWS rows tall.  Columns float to fit trends.
    ** If names are of different pathNames, then we need to make one row per pathName and as many columns as needed
    to fit all trends given TRENDS_PER_SUBPLOT trends.

    :param dataTuple:
    :param filtersTuple:
    :return: a figure containing subplots
    '''

    # unpack tuples
    dataDFList = dataTuple[0]
    dataNames = dataTuple[1]
    n_keywordsList = filtersTuple[0]
    u_keywordsList = filtersTuple[1]
    n_prereqsList = filtersTuple[2]
    u_prereqsList = filtersTuple[3]

    # find num of different pathNames
    numPaths = 0
    pathList = []
    for p in PATHS:
        if p in n_keywordsList + u_keywordsList:
            numPaths += 1
            pathList.append(p)
    numPrereqs = 0
    prereqList = []
    for q in PREREQ_PATHS:
        if q in n_prereqList + u_prereqList:
            numPrereqs += 1
            prereqList.append(0)

    if (numPaths + numPrereqs) > 1:
        isContextPlot = True
    else:
        isContextPlot = False

    if isContextPlot:
        # number of rows is determined by number of paths, and prereqs should be plotted
        pass
        #numRows = len(pathNames)
        # numCols =
    else:
        # only one type of path to plot, so subplot grid is less constrained
        numSubplots = int(math.ceil(len(dataDFList)/float(TRENDS_PER_SUBPLOT)))
        numRows = min(MAX_SUBPLOT_ROWS, numSubplots)
        numCols = int(math.ceil(numSubplots/float(numRows)))
        (xmin, xmax) = get_start_end(dataDFList)
        # get y limit, only if filtering on pathName:
        ymin = Y_LIMS[pathList[0]][0]
        ymax = Y_LIMS[pathList[0]][1]
        parsedNames = get_parsed_list(dataNames, SEPARATORS[pathList[0]],unique=False)  # used for legend labels

        fig = plt.figure(figsize=(COL_SIZE*numCols, ROW_SIZE*numRows))  # figsize = w,h tuple in inches
        # loop over columns, then rows (prioritizing subplot stacking)
        i_end = 0
        for nc in range(numCols):
            for nr in range(numRows):
                ax = plt.subplot2grid((numRows, numCols), (nr, nc))
                labels = []
                i_start = i_end
                i_end = min(i_start + TRENDS_PER_SUBPLOT, len(dataDFList))
                for df in range(i_start, i_end):
                    plt.plot(dates.num2date(dataDFList[df].index), dataDFList[df])
                    plt.hold(True)
                    labels.append(parsedNames[df])
                ax.set_xlim([xmin,xmax])
                if ymin != None:
                    ax.set_ylim([ymin,ymax])
                plt.legend(labels, fontsize='8')  # apply legend labels
                plt.ylabel(TREND_UNITS[pathList[0]])  # apply y axis label
                # plt.gcf().autofmt_xdate()
                if i_end == len(dataDFList):
                    break

        fig.suptitle(TREND_TITLES[pathList[0]], horizontalalignment='center',verticalalignment='top')
        # fig.text(0.5, 0.95, 'Test set started: '+str(dates.num2date(xmin)), horizontalalignment='center',verticalalignment='bottom')

    figName = raw_input('save fig as: __.png ')+'.png'  # get name to save plot as
    plt.savefig(figName)
    plt.show()
    plt.clf()

def get_start_end(DFList):
    startlist = []
    endlist = []
    for df in DFList:
        startlist.append(df.index[0])
        endlist.append(df.index[-1])
    startTime = min(startlist)
    endTime = max(endlist)
    return startTime, endTime

def plot_test_set_data(names):
    '''
    Creates a multi-subplot that spans all trends.
    Useful to understanding the test set environment.
    Can operate on entire test set, or on some boxes
    :param names: filenames
    :return: one figure with subplots
    '''
    NUM_TRENDS = 6

    # damper position
    measureDamperFiles = filter_data(['measure_damper_opening_real'], names)
    measureDamperTuple = get_all_files_info(measureDamperFiles)
    measureDamperDFList = measureDamperTuple[0]
    measureDamperNames = get_parsed_list(measureDamperTuple[1],['\\','_site'], unique=False)  # get legend labels

    actuatorDamperFiles = filter_data(['actuator_u_damper_opening_real'], names)
    actuatorDamperTuple = get_all_files_info(actuatorDamperFiles)
    actuatorDamperDFList = actuatorDamperTuple[0]
    actuatorDamperNames = get_parsed_list(actuatorDamperTuple[1],['\\','_site'], unique=False)  # get legend labels

    actuatorDamper_lockFiles = filter_data(['actuator_u_damper_opening_lock_real'], names)
    actuatorDamper_lockTuple = get_all_files_info(actuatorDamper_lockFiles)
    actuatorDamper_lockDFList = actuatorDamper_lockTuple[0]
    actuatorDamper_lockNames = get_parsed_list(actuatorDamper_lockTuple[1],['\\','_site'], unique=False)  # get legend labels

    plt.figure(1)
    plt.subplot(NUM_TRENDS,1,1)
    labels = []
    for df in range(0,len(measureDamperDFList)):
        plt.plot(measureDamperDFList[df].index, measureDamperDFList[df],'-',
                 actuatorDamperDFList[df].index, actuatorDamperDFList[df],':',
                 actuatorDamper_lockDFList[df].index, actuatorDamper_lockDFList[df],'o',)
        plt.hold(True)
        labels.extend([measureDamperNames[df], actuatorDamperNames[df], actuatorDamper_lockNames[df]])
    plt.legend(labels, fontsize='10')  # apply legend labels
    plt.ylabel(TREND_UNITS['measure_damper_opening_real'])  # apply y axis label
    plt.title('Damper Position')

    # box airflow
    plt.subplot(NUM_TRENDS,1,2)
    cfm = filter_data(['measure_mdot_real'], names)

    # discharge air temp


    # zone temp
    plt.subplot(NUM_TRENDS,1,3)
    'measure_zone_temp'

    # hot water valve
    plt.subplot(NUM_TRENDS,1,4)
    'actuator_u_hv_lock_real'
    'measure_hv_real'

    # ColdDuctPressure
    plt.subplot(NUM_TRENDS,1,5)
    'actuator_u_static_pressure_real'
    'measure_static_pressure_stpt_real'

    # ColdDuctTemperature
    plt.subplot(NUM_TRENDS,1,6)
    'measure_Ts_T'

    # HotWaterTemperature
    # HotWaterPressure


# 1) Read folder contents and then file contents and understand what trends are available
filenames = get_folder_info("C:\Users\christina\Documents\All_BrightBox_Docs\ALPHA TEST\Test Set Analytics\/test_csv_data_851")
# siteIDs = get_parsed_list(filenames, ['site_', '_'], unique=True)
# testIDs = get_parsed_list(filenames, ['\\','__'], unique=True)
refNames = get_parsed_list(filenames, start=['__'],end=['_V'], unique=True)
pathNames = get_parsed_list(filenames, ['VAVR_','_path'], unique=True)  # need a unique separator to make this more general!!
prereqNames = filter_data(([],[],[],PREREQ_PATHS),testIDs)

# show available filter keywords:
print 'Available filter keywords are: '
# print '*****Site ID:*****'
# for s in siteIDs: print s
# print '*****Test ID:*****'
# for t in testIDs: print t
print '*****Equipment reference name:*****'
for r in refNames: print r
print '*****Path name:*****'
for p in pathNames: print p
print 10*'**'

# ask user to provide filter(s)
print 'Filter on keywords. '
n_filterList = get_filter_list('n')
u_filterList = get_filter_list('u')
print 'Available prerequisites are: '
print '*****Prereq ID:*****'
for q in prereqNames: print q
print 'Add prerequisites to plot. '
n_prereqList = get_filter_list('n')
u_prereqList = get_filter_list('u')

# use filters to select relevant filenames from folder
filterListTuple = (n_filterList, u_filterList, n_prereqList, u_prereqList)
filteredFiles = filter_data(filterListTuple, filenames)

# open relevant files and import data to pandas dataframe
# Note: filteredFiles are ALL filenames that match the filters; filteredNames are only filenames that also contain data (are not empty).
filteredDataTuple = get_all_files_info(filteredFiles)  # tuple = (DFList, namesList)

# plotting:
plot_filtered_data(filteredDataTuple, filterListTuple)


# to do:
# get timestamps to plot - done
# allow user to input UTC offset
# allow for plotting prereq threshold
# add subplots and dynamically calculate appropriate number of subplot rows + columns based on len(DFlist) - done
# allow for contextual plots, i.e. sort by pathName
# allow dataframe to be empty and still plot - done
# allow user to filter on OR as well as AND - done
# get start and end time for filtered data - done
# put title on figure, not on subplot - done
# catch invalid filters, e.g. typos
# pretty format for time stamp, ie remove seconds

