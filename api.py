import json
import os
import re
import urllib
import zipfile

API_HOST = 'http://api.brain-map.org/'
API_QUERY_BASE_URL = API_HOST + 'api/v2/data/query.json?'
GRID_URL_FORMAT = API_HOST + "grid_data/download/%d"

# Make a query to the api, downloading all rows and packaging them into an array.
def query(url, rows_per_query=2000):
    start_row = 0
    total_rows = -1
    
    rows = []
    done = False

    # Read rows until we have all of the results.  We will know how many rows
    # that is by checking the response of the first query.
    while not done:

        # Append start_row and num_row arguments to the query.
        paged_url = '%s%s,rma::options[start_row$eq%d][num_rows$eq%d]' % (API_QUERY_BASE_URL, url, start_row, rows_per_query)
        
        print paged_url

        # Convert the response to JSON
        response = urllib.urlopen(paged_url).read()
        response_json = json.loads(response)

        if not response_json['success']:
            raise IOError(response_json['msg'])

        # Appen the response rows.
        rows += response_json['msg']

        # Initialize total_rows if it hasn't been.
        if total_rows < 0:
            total_rows = int(response_json['total_rows'])
            
        start_row += len(response_json['msg'])
        
        if start_row >= total_rows:
            done = True

    return rows
        
# Download a zip file containing the grid data for a section data set.
# Return the results as an array.
def download_grid_file(section_data_set_id, file_prefix=''):
    url = GRID_URL_FORMAT % (section_data_set_id)
    fh = urllib.urlretrieve(url)

    zf = zipfile.ZipFile(fh[0])
    
    header = zf.read('energy.mhd')
    raw = zf.read('energy.raw')

    # Decide what to call the mhd/raw when we save them.
    energy_mhd_file_name = '%s%d_energy.mhd' % (file_prefix, section_data_set_id)
    energy_raw_file_name = '%s%d_energy.raw' % (file_prefix, section_data_set_id)

    # Update the mhd to use the new raw file name.
    header = header.replace('energy.raw', os.path.basename(energy_raw_file_name))

    with open(energy_mhd_file_name, 'w') as f:
        f.write(header)

    with open(energy_raw_file_name, 'wb') as f:
        f.write(raw)

    return os.path.basename(energy_mhd_file_name), os.path.basename(energy_raw_file_name)

# Download all of the section data sets from a particular product
def download_data_sets(product_id):
    rows = query("criteria=model::SectionDataSet,rma::criteria,[failed$eq'false'],[expression$eq'true'],products[id$eq%s],rma::include,probes,genes,reference_space" % product_id)
    return rows[0:10]

# Download all of the structures in a graph
def download_structures(graph_id):
    rows = query("criteria=model::Structure,rma::criteria,[graph_id$eq%d]" % (graph_id))
    return rows

# Download the annotated volume file for a gien reference space.
def download_annotation_volume(reference_space_id, file_prefix):

    # Each reference space has a well known file called 'gridAnnotation.zip'. 
    # Query the API for the link to that file.
    rows = query("criteria=model::ReferenceSpace,rma::criteria,[id$eq%d],rma::include,well_known_files[path$li'*gridAnnotation.zip']" % reference_space_id)
    refspace = rows[0]
    reffile = refspace['well_known_files'][0]

    # Download the zip file.
    fh = urllib.urlretrieve(API_HOST + reffile["download_link"])
    zf = zipfile.ZipFile(fh[0])

    # Unzip it and pull out the header and raw file.  Due to inconsistent naming conventions, this could
    # either be just gridAnnotation.{mhd|raw} or gridAnnotation/gridAnnotation.{mdh|raw}
    header = None
    raw = None
    for annot_prefix in ["gridAnnotation","gridAnnotation/gridAnnotation"]:
        try:
            header = zf.read('%s.mhd' % annot_prefix)
            raw = zf.read('%s.raw' % annot_prefix)
            break
        except:
            pass
    
    assert header, "Failed to unzip grid annotation header file"
    assert raw, "Failed to unzip grid annotation raw file"

    # Decide what to call the mhd/raw when we save them.
    annot_mhd_file_name = '%s%d_annotation.mhd' % (file_prefix, reference_space_id)
    annot_raw_file_name = '%s%d_annotation.raw' % (file_prefix, reference_space_id)

    # Update the mhd to use the new raw file name.
    header = header.replace('gridAnnotation.raw', os.path.basename(annot_raw_file_name))

    # Save them.
    with open(annot_mhd_file_name, 'w') as f:
        f.write(header)

    with open(annot_raw_file_name, 'wb') as f:
        f.write(raw)

    return os.path.basename(annot_mhd_file_name), os.path.basename(annot_raw_file_name)
