import array
import ontology

# This script demonstrates a simple calculation that you can do using an 
# expression energy volume and its corresponding annotation volume.  It
# reads in both volumes, then computes the average expression of the
# probe per structure.

ENERGY_FILE_NAME = 'volumes/100083323_energy.raw'
ANNOTATION_FILE_NAME = 'annotation/2_annotation.raw'
ONTOLOGY_FILE_NAME = 'meta/structures.csv'

# Read in an energy volume as a block of floats.
def read_energy_file(file_name):
    with open(file_name, 'rb') as f:
        raw = f.read()
        return array.array('f', raw)

    return None

# Read in an annotation volume as a block of unsigned shorts.
def read_annotation_file(file_name):
    with open(file_name, 'rb') as f:
        raw = f.read()
        return array.array('H', raw)

    return None

# Read in the volumes.
energy = read_energy_file(ENERGY_FILE_NAME)
annotation = read_annotation_file(ANNOTATION_FILE_NAME)

# Make sure they're the same length.
num_voxels = len(energy)
assert num_voxels == len(annotation), "annotation and energy files have different dimensions"

# Read in the ontology.
o = ontology.read_from_csv(ONTOLOGY_FILE_NAME, ontology.Ontology.DEVELOPING_MOUSE_ROOT_STRUCTURE_ID)

# Initialize the list of energy values for all of the structures in the list.
for structure_id, structure in o.structures.iteritems():
    structure.energy_values = []

# Build a list of energy values for all structures in the annotation volume.
# This only contains leaf nodes, so also append the energy values to parent
# structures recursively.
for i in xrange(num_voxels):
    structure = o.get_structure(annotation[i])
    value = energy[i]

    while structure:
        structure.energy_values.append(value)
        structure = structure.parent

# Sum the list of values in each structure, print out values normalized by volume.
for structure_id, structure in o.structures.iteritems():
    if len(structure.energy_values) > 0:
        structure.sum = reduce(lambda x, y: x+y, structure.energy_values)
        structure.volume = len(structure.energy_values)

        print { "name": structure['name'], 
                "sum": structure.sum,
                "volume": structure.volume,
                "mean": structure.sum/structure.volume }

    else:
        structure.sum = 0
        structure.volume = 0

