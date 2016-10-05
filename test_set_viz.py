__author__ = 'christina'


"""
This class defines a set of text files as an object that describes a test set.
Methods in this class read the text files and allow the user to create visual representations of what the scheduler did,
when prerequisites become in/valid, and to print basic statistics about the test set.

Features:
Read in Test Set Log file. (minimum requirement)
Read in n Prereq Validity text file(s).
Read in n Test Log text file(s).

Get basic test set stats: start/end time, avg test run time
Get graph of tests and prereqs on timeline (optionally: with prereq validity data superimposed)
Get graph of num tests run simultaneously (count of running =[])

Must be adaptable in both 1.0 and 1.1.

Some methods require certain type of text files be read in. If the required file is not read in, then the method should
return None or [].

User has to define the text file type so that the class can tell which methods apply.

"""
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np

RESULT = 'result'
TIME = 'time'
VALUE = 'value'

class TestSet(object):
    def __init__(self, filename, version):
        self.state_machine_dict = {
            'v1.0': "2set CXTest state machine running ",
            'v1.1': "2SCXTest running "
        }
        self.modeled_eq_dict = {
            'v1.0': "<ModeledEquipment: ",
            'v1.1': "<Equipment: "
        }
        self.prereq_validity_data = {}
        self.test_result_dict = {}

        self.MAX_SIMUL_TESTS = 26
        self.MODELED_EQ = self.modeled_eq_dict[version]
        self.PREREQ_COLORS = ['b', 'g', 'r', 'c', 'm', 'y']
        self.PREREQ_ID = "updating prereq "
        self.PREREQ_MACH = "<PrereqMachine: "  # used to parse prereq log entry into each prereq provider
        self.PREREQ_MACH_LIST = "{<PrereqMachine: "  # used to identify log entries that print the prereq sets
        self.RUNNING = "running = "
        self.STATE_MACHINE = self.state_machine_dict[version]
        self.TEST_MESSAGE = ["Test analysis complete.", "Setting final result to : "]
        self.TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        self.TO_RUN = 'to run = '
        self.PREREQ_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
        self.RESULT_FORMAT = {
            "Result: passed": '#00e402',
            "Result: failed": '#e51e05',
            "2": '#ffcf12'
        }
        self.TEST_COLORS = ['b', 'g', 'r', 'c', 'm', 'y']
        self.TEST_LOG_FILENAME = filename  # TODO: throw error if file is not plaintext type
        self.TO_RUN = "to run = "
        self.UNLOCKED = "Found unlocked zone: "  # note final whitespace
        self.VERSION = version

        with open(self.TEST_LOG_FILENAME,'r',0) as f:
            self.test_log_list = f.read().splitlines()

        # now, do all parsing!
        # initialize safety set dict, test set dict, test counters, index counters, etc.
        # for each line in log : parse line with if/elif statements
        # make methods (static methods?) that simply call for keys or values or plot or assign
        # assignment could be useful as a class method instead of static method?

    def __str__(self):
        return self.VERSION + " Test Set: " + self.TEST_LOG_FILENAME.rstrip('.txt')

    # def read_log(self, filename):
    #     with open(filename,'r',0) as f:
    #         log = f.read().splitlines()
    #     return log

    def get_prereq_IDs(self):
        """
        finds all the unique prereq ids in the test set and returns them as a list
        """
        prereq_IDs = []
        prereq_entries = filter(lambda x: self.PREREQ_ID in x, self.test_log_list)
        for entry in prereq_entries:
                prereq = entry[(entry.find(self.PREREQ_ID) + len(self.PREREQ_ID)):]
                if prereq not in prereq_IDs:
                    prereq_IDs.append(prereq)
        return prereq_IDs

    def get_safety_set(self, validity_data=False):
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

        if there is prereq validity data, then that is used to create safety set dict
        """
        safety_set_dict = {}
        index_counter_dict = {}        
        prereq_entries = [x for x in self.test_log_list if self.PREREQ_MACH_LIST in x]
        split_entries = [x.lstrip('{').rstrip('{').split(self.PREREQ_MACH) for x in prereq_entries]
        for entry in split_entries:
            # remove curly braces and parse line into prereq machine segments
            # segments = entry.lstrip('{').rstrip('}').split(self.PREREQ_MACH)
            this_datetime = self.getDateTime(entry[0].split(' - ')[1])  # first segment has datetime value that we want            
            (prereq_ID, box_names) = self.get_ref_names(entry[1:])  # parse segments into equipment refnames

            # initialize index_counter:
            try:
                index_counter_dict[prereq_ID]
            except KeyError:
                index_counter_dict[prereq_ID] = 0

            for box in box_names:
                try:
                    safety_set_dict[box]
                except KeyError:  # need to initialize a dict for the new prereq_ID
                    safety_set_dict[box] = {}

                try:
                    safety_set_dict[box][prereq_ID]
                except KeyError:  # need to initialize a list for the new box
                    safety_set_dict[box][prereq_ID] = []

                # check this_datetime against the validity data for this prereq_ID
                (index_counter_dict, validity) = self.is_prereq_valid(index_counter_dict, this_datetime, prereq_ID)
                if validity_data == False or validity == True:
                    safety_set_dict[box][prereq_ID].append(this_datetime)

        return safety_set_dict

    def is_prereq_valid(self, index_counter_dict, date_time, prereq_ID):
        try:
            self.prereq_validity_data[prereq_ID]
        except KeyError:
            return (index_counter_dict, False)
        # compare date_time to list of timestamps when validity changed value
        # use bisection search to find closest and earliest value, or use an index counter to keep track
        # use the index of that validity timestamp to look up the validity at the time
        # edge case: when there is only one entry (never became valid)
        # closest_time = self.findClosestTime(date_time, self.prereq_validity_data[prereq_ID][0])
        time_list = self.prereq_validity_data[prereq_ID][0]
        if index_counter_dict[prereq_ID] == len(time_list) - 1:
            # keep index_counter the same
            pass
        elif date_time < time_list[index_counter_dict[prereq_ID] + 1]:
            # keep index_counter the same
            pass
        elif date_time >= time_list[index_counter_dict[prereq_ID] + 1]:
            index_counter_dict[prereq_ID] += 1

        validity = self.prereq_validity_data[prereq_ID][1][index_counter_dict[prereq_ID]]
        # print str(index_counter), str(time_list[index_counter]), prereq_ID + " is " + str(validity) + " at " + str(date_time)
        return (index_counter_dict, validity)

    def get_scheduled(self):
        scheduled_dict = {}
        found = False
        while found == False:
            entry = [x for x in self.test_log_list if x]

    def get_test_set(self):
        testsetDict = {}
        # running_entries = filter(lambda x: self.RUNNING in x, self.test_log_list)
        running_entries = [x for x in self.test_log_list if self.RUNNING in x]
        for entry in running_entries:
            segments = entry.lstrip('[').rstrip(']').replace(', ', '').split(self.STATE_MACHINE)  # remove square brackets and parse line into test segments
            this_datetime = self.getDateTime(segments[0])  # first segment has datetime value that we want
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

                # if test_log == True:
                try:
                    self.test_result_dict[box]
                except KeyError:
                    self.test_result_dict[box] = {}
                try:
                    self.test_result_dict[box][test]
                except KeyError:
                    self.test_result_dict[box][test] = {
                        TIME: None,
                        RESULT: None
                    }

        return testsetDict

    def get_test_count(self):
        test_list = self.get_test_list()
        countDict = {"all":[[],[]]}
        running_entries = filter(lambda x: self.RUNNING in x, self.test_log_list)
        for entry in running_entries:
            (time_string, all_tests_string) = entry.split(self.RUNNING)
            date_time = self.getDateTime(time_string)
            countDict['all'][0].append(date_time)
            countDict['all'][1].append(all_tests_string.count(self.STATE_MACHINE))
            # test_list = all_tests_string.split(self.STATE_MACHINE)
            # loop through all tests and count each one
            for a_test in test_list:
                try:
                    countDict[a_test]
                except KeyError:
                    countDict[a_test] = [[],[]]
                countDict[a_test][0].append(date_time)
                countDict[a_test][1].append(all_tests_string.count(a_test))
            # create a new dict, if one exists, it's already been counted, then move on to the end
        return countDict

    def get_test_list(self):
        to_run_entries = filter(lambda x: self.TO_RUN in x, self.test_log_list)
        segments = to_run_entries[0].lstrip('[').rstrip(']').replace(', ', '').split(self.STATE_MACHINE)  # remove square brackets and parse line into test segments
        test_list = []
        for seg in segments[1:]:  # segments[0] contains timestamp -- we don't need it now
            a_test = seg.partition(' on ')[0]  # grab just the test acronym
            if a_test not in test_list:
                test_list.append(a_test)
        return test_list

    def get_start_stop_time(self):
        start_time = self.getDateTime(self.test_log_list[0])
        stop_time = self.getDateTime(self.test_log_list[-10])
        return (start_time, stop_time)

    def get_box_list(self, pDict, tDict):
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
        # TODO: force numeric sorting by vav numbers -- watch out for different prefix! e.g. vav-co, vav-rh, etc

        sorted_ref_names = sorted(ref_names)
        return sorted_ref_names

    def getDateTime(self, aStr):
        # clip off the last 6 chars to drop the java time zone format
        dt_value = dt.datetime.strptime(aStr[:-6], self.TIME_FORMAT)
        return dt_value

    def get_ref_names(self, seg):
        (prereq_ID, sep, equip) = seg.partition('>: ')
        equipments = equip.rstrip(', ')[1:-1]
        if len(equipments) == 0:
            refnames_list = ['Manual']
        else:
            refnames_list = equipments.replace(self.MODELED_EQ, '').replace('>', '').replace(' ', '').split(',')
        return prereq_ID, refnames_list

    def count_box_instances(self, ref_names, pDict, tDict):
        instancesDict = dict(zip(ref_names, [0] * len(ref_names)))
        for box_p in pDict.keys():
            instancesDict[box_p] += len(pDict[box_p])
        for box_t in tDict.keys():
            instancesDict[box_t] += len(tDict[box_t])
        return instancesDict

    def map_boxes_to_y_axis(self, sorted_ref_names, pDict, tDict):
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

    def map_items_to_plot_color(self, items, formats):
        extend = len(items) / len(formats)
        color_list = formats + extend * formats
        color_map = dict(zip(items, color_list))
        return color_map

    def plot_test_timeline(self):
        prereq_IDs = self.get_prereq_IDs()
        safety_set_dict = self.get_safety_set()
        safety_while_valid_dict = self.get_safety_set(validity_data=True)
        testDict = self.get_test_set()
        sorted_ref_names = self.get_box_list(safety_set_dict, testDict)
        yticks_vals = self.map_boxes_to_y_axis(sorted_ref_names, safety_set_dict, testDict)
        color_map = self.map_items_to_plot_color(prereq_IDs,self.PREREQ_COLORS)

        # format plot
        plt.figure()
        plt.yticks(range(1, 1+ len(sorted_ref_names)), sorted_ref_names)
        plt.ylim(0, 2+ len(sorted_ref_names))

        plt.xlabel('Timezone = UTC')
        plt.grid(b=True, which='major', axis='both', color='#CCCCCC', linestyle='-', zorder=0)
        plt.title('Test Set Timeline: ' + self.TEST_LOG_FILENAME.rstrip('.txt'))

        for box in sorted_ref_names:
            y_tick_index = 0

            if box in safety_set_dict.keys():
                # plot boxes in safety set:
                for prereq in safety_set_dict[box].keys():
                    plt.plot(safety_set_dict[box][prereq],
                             len(safety_set_dict[box][prereq]) * [yticks_vals[box][y_tick_index]],
                             color_map[prereq], linewidth=1.0)
                    # if this safety set box  was safety set when prereq became valid, plot on top of previous plot
                    if box in safety_while_valid_dict.keys() and prereq in safety_while_valid_dict[box].keys():
                        plt.plot(safety_while_valid_dict[box][prereq],
                                 len(safety_while_valid_dict[box][prereq]) * [yticks_vals[box][y_tick_index]],
                                 color_map[prereq], marker='o', markeredgecolor=color_map[prereq], markersize=2.0)
                    y_tick_index += 1

            if box in testDict.keys():
                # plot tests
                for test in testDict[box].keys():
                    plt.plot(testDict[box][test], len(testDict[box][test]) * [yticks_vals[box][y_tick_index]], 'k,')
                    if self.test_result_dict[box][test][RESULT] is not None:
                        plt.plot(self.test_result_dict[box][test][TIME],yticks_vals[box][y_tick_index],
                                 color=self.RESULT_FORMAT[self.test_result_dict[box][test][RESULT]],
                                 marker='s',
                                 markersize=5.0)
                    plt.text(testDict[box][test][0], yticks_vals[box][y_tick_index]+0.05, test, fontsize=7)
                    y_tick_index += 1
        print color_map
        plt.savefig('timeline_' + self.TEST_LOG_FILENAME.rstrip('.txt') + '.png')
        plt.show()
        plt.clf()

    def plot_test_count(self):
        test_list = self.get_test_list()
        countDict = self.get_test_count()
        color_map = self.map_items_to_plot_color(test_list, self.TEST_COLORS)

        plt.plot(countDict['all'][0], countDict['all'][1], 'k-,', linewidth=3.0)
        text_label_coords = []

        counter = 0
        for a_test in test_list:
            plt.plot(countDict[a_test][0], countDict[a_test][1], color_map[a_test])
            try:
                text_label_val = filter(lambda x: x > 0, countDict[a_test][1])[0]  # find first non-zero value for label
                text_label_index = countDict[a_test][1].index(text_label_val)
                text_label = a_test
            except IndexError:
                text_label_index = 0
                text_label = a_test + ' could not run'
            text_label_x = countDict[a_test][0][text_label_index]
            text_label_y = countDict[a_test][1][text_label_index] + 0.05
            y_spacer = 0
            if [text_label_x, text_label_y] in text_label_coords:
                counter += 1
                y_spacer += 0.5*counter
            text_label_y += y_spacer
            text_label_coords.append([text_label_x, text_label_y])
            plt.text(text_label_x, text_label_y, text_label, fontsize=10)

        # format + save plot:
        plt.ylim(0, self.MAX_SIMUL_TESTS + 2)
        plt.title('Test Count: ' + self.TEST_LOG_FILENAME.rstrip('.txt'))
        plt.savefig('test count_' + self.TEST_LOG_FILENAME.rstrip('.txt') + '.png')
        plt.show()
        plt.clf()

    def set_prereq_validity_data(self, filename, prereq_ID):
        '''
        This method allows the user to associate a plaintext file to a prereq ID.
        TODO: Includes a check that the prereq_ID exists in the test_log
        1. read file
        2. parse file
        3. save data into dict that was initialized when class was instantiated
        :param filename:
        :param prereq_ID:
        :return:
        '''
        prereq_IDs = self.get_prereq_IDs()
        if prereq_ID not in prereq_IDs:
            raise ValueError('PrereqID not recognized')
        log = self.read_log(filename)
        times = filter(lambda x: 'Z' in x, log)
        validity = map(lambda x: int(x), filter(lambda x: x == '0' or x == '1', log))
        dt_value = map(lambda x: dt.datetime.strptime(x.rstrip('"').lstrip('"')[:-5], self.PREREQ_TIME_FORMAT), times)
        self.prereq_validity_data[prereq_ID] = [dt_value, validity]

    def set_test_result(self, filename, ref_name, test):
        '''
        This method allows the user to set a test result log to a box and test.
        In the future, user should be able to enter a bunch of these at once (as 3-tuples?)
        The result log dict is initialized when the object is defined, and the dict's keys are populated with
         get_test_set method.  The result log dict is left empty of values until set_test_result is called.
        :param filename:
        :param ref_name:
        :return:
        '''
        log = self.read_log(filename)
        result_entry = [x for x in log if self.TEST_MESSAGE[0] in x or self.TEST_MESSAGE[1] in x]
        result_segments = result_entry[0].split(' - ')
        try:
            self.test_result_dict[ref_name]
        except KeyError:
            self.test_result_dict[ref_name]= {}
        try:
            self.test_result_dict[ref_name][test]
        except KeyError:
            self.test_result_dict[ref_name][test] = {}

        self.test_result_dict[ref_name][test] = {
            TIME: dt.datetime.strptime(result_segments[1][:-6], self.TIME_FORMAT),
            RESULT: result_segments[2].lstrip(self.TEST_MESSAGE[0]).lstrip(self.TEST_MESSAGE[1])
        }



some_test = TestSet("pamf-1472.txt", "v1.0")  # test class initiation
safety_set = some_test.get_safety_set()
# some_test.set_prereq_validity_data('pamf-1472_cdp_fl1.txt', 'ColdDuctPressure 3678')
# some_test.set_prereq_validity_data('pamf-1472_cdp_fl2.txt', 'ColdDuctPressure 3674')
#some_test.set_prereq_validity_data('pamf-1472_hwp.txt', 'HotWaterPressure 3676')
#some_test.set_prereq_validity_data('pamf-1472_hwt.txt', 'HotWaterTemperature 3677')
#some_test.set_prereq_validity_data('pamf-1472_cdt_fl1.txt', 'ColdDuctTemperature 3679')
# some_test.set_prereq_validity_data('pamf-1472_cdt_fl2.txt', 'ColdDuctTemperature 3675')
# some_test.plot_test_timeline()
test_set = some_test.get_test_set()  # test test set parsing
# print some_test.get_box_list(safety_set, test_set)
# some_test.plot_test_count()
some_test.set_test_result('pamf-1472_vav2-6_dpc.txt', '#pdc_vav_2_6_VAVR_site_97', 'VVR_DPC')
some_test.set_test_result('pamf-1472_vav2-6_cool.txt', '#pdc_vav_2_6_VAVR_site_97', 'VVR_ZSA')
some_test.set_test_result('pamf-1472_vav1-12_afs.txt', '#pdc_vav_1_12_VAVR_site_97', 'VVR_AFS')
some_test.plot_test_timeline()
"""
print some_test.prereq_validity_data
print some_test  # test pretty print
safety_set = some_test.get_safety_set()  # test safety set parsing
test_set = some_test.get_test_set()  # test test set parsing
test_list = some_test.get_test_list()
prereq_IDs = some_test.get_prereq_IDs()  # test prereq_ID parsing
print test_list
print "Elapsed time: " + str(some_test.get_start_stop_time(log)[1] - some_test.get_start_stop_time(log)[0])  # test date time
some_test.plot_test_timeline()
some_test.plot_test_count()

TODO:
refactor! streamline process so only run through log once.  get__ methods can print keys of dicts or return lists from main fn
for any test that was scheduled to run but never appeared in running = [ by the end of the test set, mark as "could not run"
print test set stats: elapsed time, avg runtime per test, avg dead time, (what else?)
print log of any other issues (locked zones, what else?)
force better numeric sorting on ref names
format time axis
thematically color prereqs
put labels at the start of each line for prereqs
add ability to plot only one box, or one prereq, or one test
DONE:
add ability for user to set individual test log and plot test result(green, red, yellow) at date_time that result is assigned. - done
incorporate data availability into state machine status data - done
graph number of simultaneous tests occuring at the time - done
convert to class structure - done
be resilient when prereqs are run manually - done
make sure multiple prereqs don't plot on top of themselves - done
plot gridlines - done
put box names on y axis ticks - done
use boxes as keys for both dicts - done
"""
