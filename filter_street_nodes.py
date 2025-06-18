import xml.etree.ElementTree as ET
from tqdm import tqdm

def get_way_node_ids(ways_file):
    """Extract all node IDs referenced in ways.xml"""
    print("Reading ways.xml to collect node IDs...")
    tree = ET.parse(ways_file)
    root = tree.getroot()
    
    # Create a set for faster lookups
    node_ids = set()
    
    # Iterate through all way elements
    for way in tqdm(root.findall('.//way')):
        # Get all nd (node) references in this way
        for nd in way.findall('nd'):
            node_ids.add(nd.get('ref'))
    
    print(f"Found {len(node_ids)} unique node IDs in ways")
    return node_ids

def filter_nodes(nodes_file, output_file, node_ids):
    """Filter nodes.xml to keep only nodes that are in node_ids"""
    print("Filtering nodes.xml...")
    
    # Parse the input file
    context = ET.iterparse(nodes_file, events=('start', 'end'))
    
    # Get the root element
    _, root = next(context)
    
    # Create a new root for the output
    new_root = ET.Element(root.tag)
    # Copy all attributes from the original root
    for key, value in root.attrib.items():
        new_root.set(key, value)
    
    # Counter for kept nodes
    kept_nodes = 0
    
    # Process nodes
    for event, elem in tqdm(context):
        if event == 'end' and elem.tag == 'node':
            # Check if this node's ID is in our set
            if elem.get('id') in node_ids:
                new_root.append(elem)
                kept_nodes += 1
            else:
                # Clear the element to free memory
                elem.clear()
    
    print(f"Kept {kept_nodes} nodes out of total nodes")
    
    # Write the filtered XML
    print("Writing filtered nodes to output file...")
    tree = ET.ElementTree(new_root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    print("Done!")

def main():
    ways_file = 'filtered_ways.xml'
    nodes_file = 'map_15-6-25.xml'
    output_file = 'street_nodes_2.xml'
    
    # Get node IDs from ways
    node_ids = get_way_node_ids(ways_file)
    
    # Filter nodes
    filter_nodes(nodes_file, output_file, node_ids)

if __name__ == "__main__":
    main() 