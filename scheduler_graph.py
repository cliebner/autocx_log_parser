__author__ = 'christina'

"""
This script is intended to create a visual representation (bar graph) of what the scheduler is doing.
You can run this from any test set report that has been converted to a plaintext file. (copy to Word, then save
as .txt).
x-axis is test set time line.
y-axis is for each box in the test set.
Each state (e.g. DPC test, Cold Duct pressure safety set) is represented by a unique bar.

Info we need from Test Set Report file:
list of boxes in test set : unique list of "Found unlocked zone:"
list of tests on each box: from first occurence of "to run = "
list of unique prereqs : available in first occurrence of "updating prereq"
start and end date time stamps for each test on each box : "new test = 2set CXTest state machine running <test name> on
<box ref name>"
start and end datetime stamps for each safety set: parse "{<PrereqMachine: ColdDuctPressure 2954>:
[<ModeledEquipment: #nvh_at_4-15_VAVR_site_85>, <ModeledEquipment: #nvh_at_4-
16_VAVR_site_85>, <ModeledEquipment: #nvh_at_4-17_VAVR_site_85>,
<ModeledEquipment: #nvh_at_4-18_VAVR_site_85>],"

approach:
parse whole text file at once and create lists, then close file and analyze lists and graph.
probably want to get dateutil library (pip install in virtualenv?) to convert date strings to UTC date objects
does it make sense to convert this to pandas to make a pandas dataframe?
create dictionary entries on the fly, don't bother making the structure in advance!

create a class for the text file
create methods to access data from the text file
getPrereqs
getTestList
getSafetySetMembers
getBoxList
getTestTimeline
"""
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np

TEST_LOG_FILENAME = "vsp_hq2.txt"
UNLOCKED = "Found unlocked zone: "  # note final whitespace
PREREQ_ID = "updating prereq "
PREREQ_MACH_LIST = "{<PrereqMachine: "  # used to identify log entries that print the prereq sets
PREREQ_MACH = "<PrereqMachine: "  # used to parse prereq log entry into each prereq provider
NEXT = "to run = "
CURRENT = "running = "
DONE = "complete = "
PLOT_FORMAT_SAFETY_SET = ['b.', 'g.', 'r.', 'c.', 'm.', 'y.']
"""
# for production:
STATE_MACHINE = "2set CXTest state machine running "
MODELED_EQ = "<ModeledEquipment: "
"""
# for development:
STATE_MACHINE = "2SCXTest running "
MODELED_EQ = "<Equipment: "


def loadTestLog(filename):
    with open(filename,'r',0) as f:
        test_log_list = f.read().splitlines()
    return test_log_list


def getPrereqIDs(test_log_list):
    """
    finds all the unique prereq ids in the test set and returns them as a list
    """
    prereqIDs = []
    for entry in test_log_list:
        if entry.find(PREREQ_ID) >= 0:
            prereq = entry[(entry.find(PREREQ_ID) + len(PREREQ_ID)):]
            if prereq not in prereqIDs:
                prereqIDs.append(prereq)
    return prereqIDs

def getBoxList(pDict, tDict):
    """
    this could parse short ref names and equipment types, or just get long ref names
    will knowing the equipment type be useful?
    short ref names will be useful for graphing.
    maybe keep long ref names for keeping track of unique boxes, and only parse to short names when ready to graph
    """
    ref_names = pDict.keys()

    for entry in tDict.keys():
        if entry not in ref_names:
            ref_names.append(entry)
    # force numeric sorting by vav numbers -- watch out for different prefix! e.g. vav-co, vav-rh, etc

    sorted_ref_names = sorted(ref_names)
    return sorted_ref_names

def getSafetySet(test_log_list):
    """
    For each log entry with prereq data:
    1. read the line
    parse line into prereq machine segments
    parse prereq machine segments into equipment ref names
    convert the datetime text to datetime value
    append the datetime value to each list

    for each prereq machine (e.g. ColdDuctPressure, etc), creates a dict where:
    dict key = box name
    dict value = list of datevalues
    """
    prereqDict = {}
    for entry in test_log_list:
        if entry.find(PREREQ_MACH_LIST) >= 0:
            # remove curly braces and parse line into prereq machine segments
            segments = entry.lstrip('{').rstrip('}').split(PREREQ_MACH)
            this_datetime = getDateTime(segments[0])  # first segment has datetime value that we want
            for seg in segments[1:]:
                (prereqID, box_names) = getRefNames(seg)  # parse segments into equipment refnames

                for box in box_names:
                    try:
                        prereqDict[box]
                    except KeyError:  # need to initialize a dict for the new prereqID
                        prereqDict[box] = {}

                    try:
                        prereqDict[box][prereqID]
                    except KeyError:  # need to initialize a list for the new box
                        prereqDict[box][prereqID] = []
                    prereqDict[box][prereqID].append(this_datetime)
    return prereqDict

def getTestSet(test_log_list):
    testsetDict = {}
    for entry in test_log_list:
        if entry.find(CURRENT) >= 0:
            segments = entry.lstrip('[').rstrip(']').replace(', ', '').split(STATE_MACHINE)  # remove square brackets and parse line into test segments
            this_datetime = getDateTime(segments[0])  # first segment has datetime value that we want
            for seg in segments[1:]:
                (test, sep, box) = seg.partition(' on ')  # parse segments into equipment refnames
                try:
                    testsetDict[box]
                except KeyError:  # need to initialize a dict for the new box
                    testsetDict[box] = {}

                try:
                    testsetDict[box][test]
                except KeyError:  # need to initialize a list for the new test
                    testsetDict[box][test] = []
                testsetDict[box][test].append(this_datetime)
    return testsetDict

def getDateTime(aStr):
    dt_string = aStr.split(' - ')[1][:-6]  # clip off the last 6 chars to drop the java time zone format
    dt_value = dt.datetime.strptime(dt_string,'%Y-%m-%d %H:%M:%S')
    return dt_value

def getStartStopTime(test_log_list):
    start_time = getDateTime(test_log_list[0])
    stop_time = getDateTime(test_log_list[-10])
    return (start_time, stop_time)

def getRefNames(seg):
    (prereqID, sep, equip) = seg.partition('>: ')
    equipments = equip.rstrip(', ')[1:-1]
    if len(equipments) == 0:
        refnames_list = ['Manual']
    else:
        refnames_list = equipments.replace(MODELED_EQ, '').replace('>', '').replace(' ', '').split(',')
    return prereqID, refnames_list

def countBoxInstances(ref_names, pDict, tDict):
    instancesDict = dict(zip(ref_names, [0] * len(ref_names)))
    for box_p in pDict.keys():
        instancesDict[box_p] += len(pDict[box_p])
    for box_t in tDict.keys():
        instancesDict[box_t] += len(tDict[box_t])
    return instancesDict

def mapBoxesToAxis(sorted_ref_names, pDict, tDict):
    """
    yticks_num[name] = count of instances that the box appears in the test set, type int
    yticks_vals[name] = linspace array converted to a list that assigns each instance to a unique ytick value
    """

    # initiate a dict to hold the count of instances and ytick values:
    yticks_vals = {}
    yticks_num = dict(zip(sorted_ref_names, [0] * len(sorted_ref_names)))

    # update the dict values with the count of instances that the box appears in the test set:
    for box_p in pDict.keys():
        yticks_num[box_p] += len(pDict[box_p])
    for box_t in tDict.keys():
        yticks_num[box_t] += len(tDict[box_t])

    max_ticks = max(yticks_num.values())

    # create a linspace array based on the number of instances that the box appears:
    MIN_VAL = 0.2
    MAX_VAL = 0.8
    counter = 1
    for name in sorted_ref_names:
        # easy way:
        yticks_vals[name] = (counter + np.linspace(MIN_VAL, MAX_VAL, max_ticks)).tolist()
        # complicated way:
        #  yticks_vals[name] = (counter + np.linspace(MIN_VAL, MAX_VAL, yticks_num[name])).tolist()
        counter += 1
    return yticks_vals

def mapPrereqsToPlotColor(prereqIDs):
    extend = len(prereqIDs) / len(PLOT_FORMAT_SAFETY_SET)
    color_list = PLOT_FORMAT_SAFETY_SET + extend * PLOT_FORMAT_SAFETY_SET
    color_map = dict(zip(prereqIDs, color_list))
    return color_map

def plotTimeline(sorted_ref_names, prereqIDs, prereqDict, testDict, time_range):
    yticks_vals = mapBoxesToAxis(sorted_ref_names, prereqDict, testDict)
    color_map = mapPrereqsToPlotColor(prereqIDs)

    # format plot
    plt.yticks(range(1, 1+ len(sorted_ref_names)), sorted_ref_names)
    plt.ylim(0, 2+ len(sorted_ref_names))

    plt.xlabel('Timezone = UTC')
    plt.grid(b=True, which='major', axis='both', color='#CCCCCC', linestyle='-', zorder=0)
    plt.title(TEST_LOG_FILENAME.rstrip('.txt'))

    for box in sorted_ref_names:
        y_tick_index = 0
        if box in prereqDict.keys():
            # plot prerequisites:
            for prereq in prereqDict[box].keys():
                plt.plot(prereqDict[box][prereq], len(prereqDict[box][prereq]) * [yticks_vals[box][y_tick_index]], color_map[prereq])
                y_tick_index += 1
        if box in testDict.keys():
            # plot tests
            for test in testDict[box].keys():
                plt.plot(testDict[box][test], len(testDict[box][test]) * [yticks_vals[box][y_tick_index]], 'k-')
                plt.text(testDict[box][test][0], yticks_vals[box][y_tick_index]+0.05, test, fontsize=7)
                y_tick_index += 1

    print color_map
    plt.savefig(TEST_LOG_FILENAME[0:-4]+'.png')
    plt.show()

watch = loadTestLog(TEST_LOG_FILENAME)
pDict = getSafetySet(watch)
tDict = getTestSet(watch)
sorted_names = getBoxList(pDict, tDict)
prereqIDs = getPrereqIDs(watch)
time_tuple = getStartStopTime(watch)
print "Elapsed time: (hh:mm:ss)"
print (time_tuple[1] - time_tuple[0])
plotTimeline(sorted_names, prereqIDs, pDict, tDict, time_tuple)
"""

TODO:
graph number of simultaneous tests occuring at the time
print test set stats: elapsed time, avg runtime per test, avg dead time, (what else?)
print log of any other issues (locked zones, what else?)
incorporate data availability into state machine status data
force better numeric sorting on ref names
format time axis
thematically color prereqs
put labels at the start of each line for prereqs and tests
convert to class structure
add ability to plot only one box, or one prereq, or one test
DONE:
be resilient when prereqs are run manually - done
make sure multiple prereqs don't plot on top of themselves - done
plot gridlines - done
put box names on y axis ticks - done
use boxes as keys for both dicts - done
"""

'''
def getShortRefName(long_ref_names):
    a = entry[len(UNLOCKED):] # box ref name with autocx equipment type and autocx site id
    b = a[:a.rfind('_site')]  # stripping autocx site id
    (ref_name, sep, equip) = b.rpartition('_')  # partitioning ref name from autocx equipment type
    return short_ref_names
'''
'''
def getTestDict(log, ref_names):
    """
    create a dict for each box, where the keys are themselves dicts, whose values are lists of datetime data.
    this is where it might be more useful to use pandas dataframes.
    """
    i = 0
    while NEXT not in log[i]:
        i += 1
        if i > len(log):  # check if end of log is reached to prevent inf loop
            break
    to_run = log[i][len(NEXT)+1:-1]
    items = to_run.replace(STATE_MACHINE,'').split(', ')

    box_dict = {r: [] for r in ref_names}

    for it in items:
        test_dict = {}
        (test, sep, name) = it.partition(' on ')
        test_dict[test] = []
        box_dict[name].append(test_dict)
    return box_dict

def setTestDict(datetime, entry, test_dict):
    """
    this method goes through the log entry, unpacks the boxes and test being run, then appends the datetime
    to value corresponding to the box and test keys.
    """
    running_now = entry[len(CURRENT)+1:-1].replace(STATE_MACHINE,'').split(', ')
    for r in running_now:
        (test, sep, name) = r.partition(' on ')
        test_dict[name].index(test)  # TODO need to check data types! you have a dict of lists instead of dict of dicts!
    return test_dict

def getRunningTestIndex(entry_num, log):
    running_test_index = []
    i = 0
    while i < len(log):
        if CURRENT in log[i] and len(log[i]) > len(CURRENT)+2:
            running_test_index.append(int(entry_num[i]))
        i += 1
    return running_test_index

def updateTestDict(test_dict, running_test_index, datetimes, log):
    for rti in running_test_index:
        new_test_dict = setTestDict(datetimes[rti], log[rti], test_dict)
        test_dict = new_test_dict

    return test_dict
'''