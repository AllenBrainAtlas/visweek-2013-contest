import csv

# A simple class for managing ontology structures.  It supports
# a couple simple queries like:
#    - does structure A descend from structure B?
#    - what are the children of structure A?
class Ontology(object):
    
    # A good place to keep track of the what the root structure ID is for the 
    # developing mouse product.
    DEVELOPING_MOUSE_ROOT_STRUCTURE_ID = 2000

    def __init__(self, rows, headers, root_database_id):
        self.structure_list = rows
        self.structures = { int(row['database_id']): row for row in rows }
        self.root = self.structures[root_database_id]

        for structure_id, structure in self.structures.iteritems():

            # convert strings to integers where appropriate.
            for key,value in structure.iteritems():
                try:
                    structure[key] = int(structure[key])
                except ValueError:
                    pass

            # pre-initialize all of the parent/child relationships.
            structure['children'] = []
            structure['parent'] = None

        # build the parent/child relationships
        for structure_id, structure in self.structures.iteritems():
            
            # parse the structure_database_id_path member of the structure.
            lineage = [int(sid) for sid in structure['structure_database_id_path'].strip('/').split('/')]

            try:
                # the parent id is the second-to-last element of this array
                parent_structure_id = lineage[-2]
                parent_structure = self.structures[parent_structure_id]
                
                structure['parent'] = parent_structure
                parent_structure['children'].append(structure)
            except IndexError:
                pass

    # Get the structure meta data for a particular structure_id.
    def get_structure(self, structure_id):
        return self.structures[structure_id]

    # Does one structure_id descend from another?
    def is_descendent(self, child_structure_id, parent_structure_id):
        structure = self.structures[child_structure_id]
        
        while structure:
            if structure['database_id'] == parent_structure_id:
                return True
            else:
                structure = structure['parent']

        return False
                
# Read an ontology from a CSV file, as written by download_data.py
def read_from_csv(file_name, root_id):
    with open(file_name, 'r') as f:
        reader = csv.DictReader(f)
        return Ontology([ row for row in reader ], reader.fieldnames, root_id)

# Run this script as is to read in the ontology from the default location and 
# run a couple simple queries.
if __name__ == "__main__":
    ontology = read_from_csv('meta/structures.csv', Ontology.DEVELOPING_MOUSE_ROOT_STRUCTURE_ID)

    print "Root structure name:", ontology.root['name']
    print "Structure 2049 name:", ontology.get_structure(2049)['name']
    print "Does 2049 descend from root?", ontology.is_descendent(2049, Ontology.DEVELOPING_MOUSE_ROOT_STRUCTURE_ID)
    print "What are 2049's children?", [child['name'] for child in ontology.get_structure(2048)['children']]
