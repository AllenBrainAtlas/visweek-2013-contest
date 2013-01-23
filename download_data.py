import api
import csv
import errno
import os

# This script will download the entirety of the VisWeek 2013 contest data. 
# Files will be exported into three directories:
#
#    - ENERGY_OUTPUT_DIRECTORY: where the expression energy files will go.
#    - META_OUTPUT_DIRECTORY: where the structure and probe meta data will go.
#    - ANNOTATION_OUTPUT_DIRECTORY: where the annotation volumes wil go.
#    - ATLAS_OUTPUT_DIRECTORY: where the atlas volumes wil go.
#    - STRUCTURE_UNIONIZES_OUTPUT_DIRECTORY: where the structure unionizes will go.
#
# For an explanation of terminology and the data set in general, see README.md.

# Database ID of the developing mouse data set, as stored in the API.
DEVELOPING_MOUSE_PRODUCT_ID = 3

# ID of the structure ontology graph for this project.
DEVELOPING_MOUSE_GRAPH_ID = 13

# Age names for the different time points. E = embryonic, P = postnatal, # = days.
REFERENCE_SPACE_AGE_NAMES = ['E13.5', 'E15.5', 'E18.5', 'P4', 'P14']

# Only select data image sagittally.  There is a s
PLANE_OF_SECTION_ID = 2 # sagittal

# Hard-coded directories and file paths.
ENERGY_OUTPUT_DIRECTORY = 'energy/'
META_OUTPUT_DIRECTORY = 'meta/'
ANNOTATION_OUTPUT_DIRECTORY = 'annotation/'
ATLAS_OUTPUT_DIRECTORY = 'atlas/'
STRUCTURE_UNIONIZES_OUTPUT_DIRECTORY = 'structure_unionizes/'

DATA_SETS_CSV = META_OUTPUT_DIRECTORY + 'data_sets.csv'
STRUCTURES_CSV = META_OUTPUT_DIRECTORY + 'structures.csv'

# make the output directory if it doesn't exist already
for directory in [ENERGY_OUTPUT_DIRECTORY, META_OUTPUT_DIRECTORY, ANNOTATION_OUTPUT_DIRECTORY, ATLAS_OUTPUT_DIRECTORY, STRUCTURE_UNIONIZES_OUTPUT_DIRECTORY]:
    try:
        os.makedirs(directory)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

# Query the API for meta data on probes and structures in the developing mouse data set.
data_sets = api.download_data_sets(DEVELOPING_MOUSE_PRODUCT_ID, REFERENCE_SPACE_AGE_NAMES, PLANE_OF_SECTION_ID)
data_set_ids = set([d['id'] for d in data_sets])

data_sets.sort(key=lambda d: d['reference_space_id'])

structures = api.download_structures(DEVELOPING_MOUSE_GRAPH_ID)

structures.sort(key=lambda s: s['graph_order'])

# Download the annotation volumes and atlas volumesfor the requested reference spaces
reference_space_ids = set([d['reference_space_id'] for d in data_sets])

for rsid in reference_space_ids:
    mhd, raw = api.download_annotation_volume(rsid, ANNOTATION_OUTPUT_DIRECTORY)

    for data_set in data_sets:
        if data_set['reference_space_id'] == rsid:
            data_set['annotation_file_name'] = mhd
            
    print mhd

    mhd, raw = api.download_atlas_volume(rsid, ATLAS_OUTPUT_DIRECTORY)

    for data_set in data_sets:
        if data_set['reference_space_id'] == rsid:
            data_set['atlas_file_name'] = mhd
            
    print mhd

# Download gene classification meta data 
gene_ids = set([d['genes'][0]['id'] for d in data_sets])
gene_classifications = api.download_gene_classifications(gene_ids)

# Download the expression energy files for each probe recieved.
for data_set in data_sets:
    mhd, raw = api.download_grid_file(data_set['id'], ENERGY_OUTPUT_DIRECTORY)
    data_set['energy_file_name'] = mhd
    print mhd

# Save probe meta data into a CSV.
with open(DATA_SETS_CSV, 'w') as f:
    headers = ["section_data_set_database_id", 
               "gene_name", "gene_acronym", "gene_entrez id", "gene_database id", 
               "probe_name", "probe_database_id", 
               "energy_file_name", 
               'reference_space_database_id',
               'reference_space_name',
               'annotation_file_name',
               'atlas_file_name',
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
                         data_set['annotation_file_name'],
                         data_set['atlas_file_name'],
                         classification_string])

# Save structure meta data into a CSV.
with open(STRUCTURES_CSV, 'w') as f:
    headers = ['database_id', 'name', 'acronym', 'order', 'level', 'color', 'structure_database_id_path']

    writer = csv.writer(f)
    writer.writerow(headers)

    for s in structures:
        writer.writerow([s['id'], s['name'], s['acronym'], s['graph_order'], s['st_level'], s['color_hex_triplet'], s['structure_id_path']])

# The structure unionize query requests all of the structure-level statistics
# for a probe.  There are a large number of unionizes (roughly speaking one
# row per structure in the stage of the data set), so the results are stored
# in one file per gene.  
for data_set_id in data_set_ids:
    
    # Make the query.
    unionizes = api.download_unionizes(data_set_id)

    file_name = "%s%d.csv" % (STRUCTURE_UNIONIZES_OUTPUT_DIRECTORY, data_set_id)

    if os.path.exists(file_name):
        continue

    # Save structure unionizes into a CSV.
    with open(file_name, 'w') as f:
        headers = ['section_data_set_id', 'structure_id', 'expression_energy', 'sum_expressing_pixel_intensity', 'sum_pixels']
        
        writer = csv.writer(f)
        writer.writerow(headers)

        for u in unionizes:
            writer.writerow([u['section_data_set_id'], u['structure_id'], u['expression_energy'], u['sum_expressing_pixel_intensity'], u['sum_pixels']])


