import xml.etree.ElementTree as ET
from datetime import datetime
import os

def process_xml_file(input_file, output_file):
    # Parse the XML file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Define the cutoff date (May 1st, 2025)
    cutoff_date = datetime(2025, 5, 1)
    
    # Find all nodes and filter them
    nodes_to_remove = []
    for node in root.findall('node'):
        timestamp_str = node.get('timestamp')
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
        if timestamp < cutoff_date:
            nodes_to_remove.append(node)
    
    # Remove nodes that are before the cutoff date
    for node in nodes_to_remove:
        root.remove(node)
    
    # Write the modified XML to a new file
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    # Print statistics
    print(f"Total nodes in original file: {len(root.findall('node')) + len(nodes_to_remove)}")
    print(f"Nodes removed: {len(nodes_to_remove)}")
    print(f"Nodes remaining: {len(root.findall('node'))}")

if __name__ == "__main__":
    input_file = "street_nodes_2.xml"
    output_file = "filtered_street_nodes.xml"
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
    else:
        process_xml_file(input_file, output_file) 