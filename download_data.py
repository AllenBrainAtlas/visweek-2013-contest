import api
import csv
import errno
import os

DEVELOPING_MOUSE_PRODUCT_ID = 3
DEVELOPING_MOUSE_GRAPH_ID = 4
REFERENCE_SPACE_AGE_NAMES = ['E13.5', 'E15.5', 'E18.5', 'P4', 'P14', 'P56']
PLANE_OF_SECTION_ID = 2 # sagittal
OUTPUT_DIRECTORY = 'data/'
DATA_SETS_CSV = OUTPUT_DIRECTORY + 'data_sets.csv'
STRUCTURES_CSV = OUTPUT_DIRECTORY + 'structures.csv'

# make the output directory if it doesn't exist already
try:
    os.makedirs(OUTPUT_DIRECTORY)
except OSError as exc:
    if exc.errno == errno.EEXIST:
        pass
    else:
        raise

# Query the API for meta data on probes and structures in the developing mouse data set.
data_sets = api.download_data_sets(DEVELOPING_MOUSE_PRODUCT_ID, REFERENCE_SPACE_AGE_NAMES, PLANE_OF_SECTION_ID)

data_sets.sort(key=lambda d: d['reference_space_id'])

structures = api.download_structures(DEVELOPING_MOUSE_GRAPH_ID)

structures.sort(key=lambda s: s['graph_order'])

# Download the annotation volumes for the requested reference spaces
reference_space_ids = set([d['reference_space_id'] for d in data_sets])

for rsid in reference_space_ids:
    mhd, raw = api.download_annotation_volume(rsid, OUTPUT_DIRECTORY)

    for data_set in data_sets:
        if data_set['reference_space_id'] == rsid:
            data_set['reference_space_file_name'] = mhd
            
    print mhd

# Download gene classification meta data 
gene_ids = set([d['genes'][0]['id'] for d in data_sets])
gene_classifications = api.download_gene_classifications(gene_ids)

# Download the expression energy files for each probe recieved.
for data_set in data_sets:
    mhd, raw = api.download_grid_file(data_set['id'], OUTPUT_DIRECTORY)
    data_set['energy_file_name'] = mhd
    print mhd

# Save probe meta data into a CSV.
with open(DATA_SETS_CSV, 'w') as f:
    headers = ["section data set database id", 
               "gene name", "gene acronym", "gene entrez id", "gene database id", 
               "probe name", "probe database id", 
               "energy file name", 
               'reference space database id',
               'reference space name',
               'reference space file name',
               'classifications']

    writer = csv.writer(f)
    writer.writerow(headers)

    for data_set in data_sets:
        probe = data_set['probes'][0]
        gene = data_set['genes'][0]
        refspace = data_set['reference_space']
        classification_string = '/'.join(c for c in gene_classifications[gene['id']])

        writer.writerow([data_set['id'], 
                         gene['name'], gene['acronym'], gene['entrez_id'], gene['id'], 
                         probe['name'], probe['id'], 
                         data_set['energy_file_name'], 
                         refspace['id'],
                         refspace['name'],
                         data_set['reference_space_file_name'],
                         classification_string])

# Save structure meta data into a CSV.
with open(STRUCTURES_CSV, 'w') as f:
    headers = ['database id', 'name', 'acronym', 'order', 'level', 'color', 'structure database id path']

    writer = csv.writer(f)
    writer.writerow(headers)

    for s in structures:
        writer.writerow([s['id'], s['name'], s['acronym'], s['graph_order'], s['st_level'], s['color_hex_triplet'], s['structure_id_path']])



