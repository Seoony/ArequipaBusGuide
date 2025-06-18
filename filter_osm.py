import xml.etree.ElementTree as ET

def filter_osm_ways(input_file, output_file):
    # Parse the XML file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Find all ways
    ways_to_remove = []
    for way in root.findall('.//way'):
        # Check if way has address interpolation tag or building=yes tag
        for tag in way.findall('tag'):
            if (tag.get('k') == 'addr:interpolation' and tag.get('v') in ['even', 'odd', 'all']) or \
                (tag.get('k') == 'substance' and tag.get('v') == 'water') or \
                (tag.get('k') == 'footway' and tag.get('v') in ['sidewalk', 'crossing']) or \
                (tag.get('k') == 'highway' and tag.get('v') in ['steps', 'footway']) or\
                (tag.get('k') in ['landuse', 'natural', 'building', 'leisure', 'barrier', 'tourism', 'waterway']):
                ways_to_remove.append(way)
                break
    
    # Remove the ways
    for way in ways_to_remove:
        root.remove(way)
    
    # Write the filtered data to a new file
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

# Input and output file names
input_file = 'ways.xml'
output_file = 'filtered_ways.xml'

try:
    filter_osm_ways(input_file, output_file)
    print(f"Successfully filtered OSM file. Output written to {output_file}")
except Exception as e:
    print(f"Error processing file: {str(e)}") 