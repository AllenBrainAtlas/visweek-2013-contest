import csv
import copy

# Structures may have a parent and some number of children.  This class makes
# it easy to keep track of them and makes the structure printable.
class Structure(dict):

    def __init__(self, *args, **kw):
        super(Structure, self).__init__(*args, **kw)
        self.parent = None
        self.children = []

    def __str__(self):
        return str({ 'children': [c['database_id'] for c in self.children], 
                     'parent': self.parent['database_id'] if self.parent else None,
                     'structure': dict(self) })

    # Does one structure_id descend from another?
    def descendent_of(self, parent):
        structure = self
        while structure:
            if structure['database_id'] == parent['database_id']:
                return True
            else:
                structure = structure.parent

        return False        

        
# A simple class for managing ontology structures.  It supports
# a couple simple queries like:
#    - does structure A descend from structure B?
#    - what are the children of structure A?
class Ontology(object):
    
    # A good place to keep track of the what the root structure ID is for the 
    # developing mouse product.
    DEVELOPING_MOUSE_ROOT_STRUCTURE_ID = 6070

    def __init__(self, rows, headers, root_database_id):
        self.structures = { int(row['database_id']): Structure(row) for row in rows }
        self.root = self.structures[root_database_id]

        for structure_id, structure in self.structures.iteritems():

            # convert strings to integers where appropriate.
            for key,value in structure.iteritems():
                try:
                    structure[key] = int(structure[key])
                except ValueError:
                    pass

        # build the parent/child relationships
        for structure_id, structure in self.structures.iteritems():
            
            # parse the structure_database_id_path member of the structure.
            lineage = [int(sid) for sid in structure['structure_database_id_path'].strip('/').split('/')]

            try:
                # the parent id is the second-to-last element of this array
                parent_structure_id = lineage[-2]
                parent_structure = self.structures[parent_structure_id]
                
                structure.parent = parent_structure
                parent_structure.children.append(structure)
            except IndexError:
                pass

    # Get structure meta data for a structure_id. Dictionary search.
    def get_structure(self, structure_id):
        try:
            return self.structures[structure_id]
        except KeyError:
            return None

    # Get structure meta data for a structure name. Exhaustive search.
    def get_structure_by_name(self, structure_name):
        return next((s for sid, s in self.structures.iteritems() if s['name'] == structure_name), None)

    # Get structure meta data for a structure acronym. Exhaustive search.
    def get_structure_by_acronym(self, structure_acronym):
        return next((s for sid, s in self.structures.iteritems() if s['acronym'] == structure_acronym), None)

# Read an ontology from a CSV file, as written by download_data.py
def read_from_csv(file_name, root_id):
    with open(file_name, 'r') as f:
        reader = csv.DictReader(f)
        return Ontology([ row for row in reader ], reader.fieldnames, root_id)

# Run this script as is to read in the ontology from the default location and 
# run a couple simple queries.
if __name__ == "__main__":
    ontology = read_from_csv('meta/structures.csv', Ontology.DEVELOPING_MOUSE_ROOT_STRUCTURE_ID)

    root = ontology.root
    print "Root structure name:", root

    isthmus = ontology.get_structure_by_acronym('is')
    print "Isthmus name:", isthmus

    print "Does isthmus descend from root?", isthmus.descendent_of(root)
    print "What are ismus's children?", [child for child in isthmus.children]
