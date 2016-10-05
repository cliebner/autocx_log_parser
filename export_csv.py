__author__ = 'colin'
import os
from bbdata.models import *
from auto_cx_I.models import *
from django.db.models import Q
test_set = CXTestSetRunner.objects.get(id=749)
print test_set.run_at
test_types = "VVC_DPC", "VVC_AFS", "VVC_ZSA", "VVR_DPC", "VVR_AFS", "VVR_ZSA", "DDV_DPC", "DDV_AFS", "DDV_ZSA"
test_statuses = [TEST_FAILED, TEST_PASSED]
tests = test_set.tests.filter(result__in=test_statuses, test_type__in=test_types)
print tests
print len(tests)
prereqs = []
for test in tests:
    print 'new test'
    for prereq in test.prerequisites.all():
        if prereq not in prereqs:
            prereqs.append(prereq)
    dcr = test.dcr
    point_paths = list(test.dcr.point_paths.all())
    print 'point paths'
    print point_paths
    for lock_psr in test.lock_psrs.all():
        point_paths.append(lock_psr.point_path)
    for point_path in point_paths:
        if test.equipment.equipment.reference_name in point_path.name:
            print 'new point path'
            fname = str(test.id) + "__" + point_path.name
            print fname
            fstring = ""
            pp_data = point_path.get_series(test.run_at, test.ended_at)
            for timestamp in pp_data.index:
                fstring += str(timestamp) + "," + str(pp_data[timestamp]) + '\n'
                # ASK ABOUT HOW TO FORMAT THE TIMESTAMP!!
            fpath = os.path.join(os.path.join(os.getcwd(), 'test_csv_data'), fname)
            f = open(fpath, 'w')
            f.write(fstring)
            f.flush()
            f.close()
            print 'wrote to file ' + fpath
print prereqs
for prereq in prereqs:
    print 'new prereq'
    print prereq
    for point_path in prereq.dcr.point_paths.all():
        print 'new point path'
        fname = str(prereq) + "__" + point_path.name
        print fname
        fstring = ""
        pp_data = point_path.get_series(prereq.dcr.start, prereq.dcr.end)
        for timestamp in pp_data.index:
            fstring += str(timestamp) + "," + str(pp_data[timestamp]) + '\n'
            # ASK ABOUT HOW TO FORMAT THE TIMESTAMP!!
        fpath = os.path.join(os.path.join(os.getcwd(), 'test_csv_data'), fname)
        f = open(fpath, 'w')
        f.write(fstring)
        f.flush()
        f.close()
        print 'wrote to file ' + fpath


