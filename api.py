import json
import os
import re
import urllib
import zipfile
import StringIO

API_HOST = 'http://api.brain-map.org/'
API_QUERY_BASE_URL = API_HOST + 'api/v2/data/query.json'
GRID_URL_FORMAT = API_HOST + "grid_data/download/%d"

# Make a query to the api, downloading all rows and packaging them into an array.
def query(query_string, rows_per_query=2000):
    start_row = 0
    total_rows = -1
    
    rows = []
    done = False

    # Read rows until we have all of the results.  We will know how many rows
    # that is by checking the response of the first query.
    while not done:

        # Append start_row and num_row arguments to the query.
        data = { 'criteria': query_string,
                 'start_row': start_row,
                 'num_rows': rows_per_query }

        print data

        # Convert the response to JSON
        response = urllib.urlopen(API_QUERY_BASE_URL, urllib.urlencode(data)).read()
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
    # Decide what to call the mhd/raw when we save them.
    energy_mhd_file_name = '%s%d_energy.mhd' % (file_prefix, section_data_set_id)
    energy_raw_file_name = '%s%d_energy.raw' % (file_prefix, section_data_set_id)

    if os.path.exists(energy_raw_file_name) and os.path.exists(energy_raw_file_name):
        return os.path.basename(energy_mhd_file_name), os.path.basename(energy_raw_file_name)

    url = GRID_URL_FORMAT % (section_data_set_id)
    print url
    zf = zipfile.ZipFile(read_url(url))
    
    header = zf.read('energy.mhd')
    raw = zf.read('energy.raw')

    # Update the mhd to use the new raw file name.
    header = header.replace('energy.raw', os.path.basename(energy_raw_file_name))

    with open(energy_mhd_file_name, 'w') as f:
        f.write(header)

    with open(energy_raw_file_name, 'wb') as f:
        f.write(raw)

    return os.path.basename(energy_mhd_file_name), os.path.basename(energy_raw_file_name)

# Download all of the section data sets from a particular product
def download_data_sets(product_id, reference_space_age_names, plane_of_section_id):
    age_str = ','.join(("'%s'" % age_name) for age_name in reference_space_age_names)
    results = query(("model::SectionDataSet" +
                     ",rma::criteria,[failed$eq'false'][plane_of_section_id$eq%d][storage_directory$nenull]" +
                     ",specimen(donor(age[name$in%s])),products[id$eq%s]" +
                     ",treatments[name$eq'ISH']" +
                     ",rma::include,probes,genes,reference_space") % (plane_of_section_id, age_str, product_id))
    return results

# Download all of the structures in a graph
def download_structures(graph_id):
    results = query("model::Structure,rma::criteria,[graph_id$eq%d]" % (graph_id))
    return results

# Download the annotated volume file for a gien reference space.
def download_annotation_volume(reference_space_id, file_prefix):

    # Decide what to call the mhd/raw when we save them.
    annot_mhd_file_name = '%s%d_annotation.mhd' % (file_prefix, reference_space_id)
    annot_raw_file_name = '%s%d_annotation.raw' % (file_prefix, reference_space_id)

    if os.path.exists(annot_raw_file_name) and os.path.exists(annot_mhd_file_name):
        return os.path.basename(annot_mhd_file_name), os.path.basename(annot_raw_file_name)
    
    # Each reference space has a well known file called 'gridAnnotation.zip'. 
    # Query the API for the link to that file.
    results = query("model::ReferenceSpace,rma::criteria,[id$eq%d],rma::include,well_known_files[path$li'*gridAnnotation.zip']" % reference_space_id)
    refspace = results[0]
    reffile = refspace['well_known_files'][0]

    # Download the zip file.
    url = API_HOST + reffile["download_link"]    
    zf = zipfile.ZipFile(read_url(url))

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


    # Update the mhd to use the new raw file name.
    header = header.replace('gridAnnotation.raw', os.path.basename(annot_raw_file_name))

    # Save them.
    with open(annot_mhd_file_name, 'w') as f:
        f.write(header)

    with open(annot_raw_file_name, 'wb') as f:
        f.write(raw)

    return os.path.basename(annot_mhd_file_name), os.path.basename(annot_raw_file_name)

# Download the annotated volume file for a gien reference space.
def download_atlas_volume(reference_space_id, file_prefix):

    # Decide what to call the mhd/raw when we save them.
    atlas_mhd_file_name = '%s%d_atlas.mhd' % (file_prefix, reference_space_id)
    atlas_raw_file_name = '%s%d_atlas.raw' % (file_prefix, reference_space_id)

    if os.path.exists(atlas_raw_file_name) and os.path.exists(atlas_mhd_file_name):
        return os.path.basename(atlas_mhd_file_name), os.path.basename(atlas_raw_file_name)
    
    # Each reference space has a well known file called 'atlasVolume.zip'. 
    # Query the API for the link to that file.
    results = query("model::ReferenceSpace,rma::criteria,[id$eq%d],rma::include,well_known_files[path$li'*atlasVolume.zip']" % reference_space_id)
    refspace = results[0]
    reffile = refspace['well_known_files'][0]

    # Download the zip file.
    url = API_HOST + reffile["download_link"]    
    zf = zipfile.ZipFile(read_url(url))

    # Unzip it and pull out the header and raw file.  Due to inconsistent naming conventions, this could
    # either be just atlasVolume.{mhd|raw} or atlasVolume/atlasVolume.{mdh|raw}
    header = None
    raw = None
    for atlas_prefix in ["atlasVolume","atlasVolume/atlasVolume"]:
        try:
            header = zf.read('%s.mhd' % atlas_prefix)
            raw = zf.read('%s.raw' % atlas_prefix)
            break
        except:
            pass
    
    assert header, "Failed to unzip atlas volume header file"
    assert raw, "Failed to unzip atlas volume raw file"


    # Update the mhd to use the new raw file name.
    header = header.replace('atlasVolume.raw', os.path.basename(atlas_raw_file_name))

    # Save them.
    with open(atlas_mhd_file_name, 'w') as f:
        f.write(header)

    with open(atlas_raw_file_name, 'wb') as f:
        f.write(raw)   

    return os.path.basename(atlas_mhd_file_name), os.path.basename(atlas_raw_file_name)

def download_gene_classifications(gene_ids):
    gene_id_str = ",".join(str(gid) for gid in gene_ids)
    results = query("model::GeneClassification,rma::include,genes[id$in%s]" % gene_id_str)

    classifications = { gene_id: [] for gene_id in gene_ids }

    for classification in results:
        for gene in classification['genes']:
            classifications[gene['id']].append(classification['name'])
    
    return classifications

# Download all of the expression statistics for structures labeled in 
# the developmental stage of a single data set.
def download_unionizes(data_set_id, graph_id):
    return query("model::StructureUnionize,rma::criteria,[section_data_set_id$eq%d],structure[graph_id$eq%d]" % (data_set_id, graph_id) )
    
def read_url(url):
    usock = urllib.urlopen(url)
    data = StringIO.StringIO(usock.read())
    return data
