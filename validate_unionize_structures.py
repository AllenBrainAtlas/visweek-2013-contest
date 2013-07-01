import csv
import os

# Check to make sure that all of the structures listed in the
# structure_unionizes folder are in the master structure list.
# Run this script from within the directory where you downloaded
# the data set.  

# read in the list of structures 
with open('meta/structures.csv','rb') as f:
    r = csv.DictReader(f)
    structures = list(r)

    # strip out the structure database ids
    all_structure_ids = [ int(s['database_id']) for s in structures ]

    # read in each structure unionize file, pull out the structure ids
    # for each listed unionize, and shove them all into a hash
    print "reading unionizes"
    unionize_structures = {}
    for dirname, dirnames, filenames in os.walk('structure_unionizes'):
        for filename in filenames:
            with open(dirname + '/' + filename, 'rb') as uf:
                ur = csv.DictReader(uf)
                unionizes = list(ur)

                structure_ids = [ int(u['structure_id']) for u in unionizes ]

                for sid in structure_ids:
                    unionize_structures[sid] = 1

    # make sure that all of the structures listed in the unionize files exist
    print "checking master list"
    for sid in unionize_structures.keys():
        if sid not in all_structure_ids:
            print "%s missing" % (sid)

    
