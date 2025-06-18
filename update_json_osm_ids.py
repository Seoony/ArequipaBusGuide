import os
import django
import json
import math
import xml.etree.ElementTree as ET
from django.contrib.gis.geos import Point, LineString
from django.contrib.gis.db.models.functions import Distance

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ArequipaBusGuide.settings')
django.setup()

from Nodes.models import Node

# Global set to store nodes to exclude
nodes_to_exclude = set()

def load_nodes_to_exclude():
    """Load nodes with highway=crossing tag from XML file into a set."""
    try:
        print("Loading nodes to exclude from XML file...")
        context = ET.iterparse('street_nodes_2.xml', events=('end',))
        
        for event, elem in context:
            if elem.tag == 'node':
                # Check if node has highway=crossing tag
                for tag in elem.findall('tag'):
                    if tag.get('k') == 'highway' and tag.get('v') == 'crossing':
                        # Store the ID as a string and strip any whitespace
                        node_id = str(elem.get('id')).strip()
                        nodes_to_exclude.add(node_id)
                        break
                # Clear element to free memory
                elem.clear()
        
        print(f"Loaded {len(nodes_to_exclude)} nodes to exclude")
        
        # Test if our target node is in the exclude list
        test_node = "9675005111"
        if test_node in nodes_to_exclude:
            print(f"\nTest node {test_node} is in the exclude list")
        else:
            print(f"\nWARNING: Test node {test_node} is NOT in the exclude list!")
            
    except Exception as e:
        print(f"Error loading nodes to exclude: {str(e)}")

def is_node_to_exclude(osm_id):
    """Check if a node should be excluded based on the pre-loaded list."""
    # Convert both to strings and remove any whitespace
    osm_id_str = str(osm_id).strip()
    print(f"Checking if node {osm_id_str} should be excluded = {osm_id_str in nodes_to_exclude}")
    return osm_id_str in nodes_to_exclude

def create_composite_id(lat, lon):
    # Format lat and lon to 7 decimal places and combine them
    return f"{lat:.7f}_{lon:.7f}"

def calculate_distance(lat1, lon1, lat2, lon2):
    # Calculate distance between two points in meters
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def interpolate_point(lat1, lon1, lat2, lon2, fraction):
    # Interpolate a point between two coordinates
    lat = lat1 + (lat2 - lat1) * fraction
    lon = lon1 + (lon2 - lon1) * fraction
    return lat, lon

def is_point_between(start_point, end_point, check_point, tolerance=0.00001):
    # Create vectors
    start = (start_point['lng'], start_point['lat'])
    end = (end_point['lng'], end_point['lat'])
    check = (check_point['lng'], check_point['lat'])
    
    # Calculate distances
    total_distance = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
    if total_distance < tolerance:
        return False
        
    # Calculate distances from check point to start and end
    dist_to_start = ((check[0] - start[0])**2 + (check[1] - start[1])**2)**0.5
    dist_to_end = ((check[0] - end[0])**2 + (check[1] - end[1])**2)**0.5
    
    # Point is between if sum of distances to endpoints is approximately equal to total distance
    return abs((dist_to_start + dist_to_end) - total_distance) < tolerance

def find_nodes_between_points(start_point, end_point, tolerance=0.00001):
    # Create a line between the two points
    line = LineString([(start_point['lng'], start_point['lat']), 
                      (end_point['lng'], end_point['lat'])])
    
    # Find nodes that are close to this line
    nodes = Node.objects.filter(
        location__dwithin=(line, tolerance)
    ).order_by('location')
    
    # Convert to list of dictionaries and filter out start/end points
    between_nodes = []
    for node in nodes:
        node_point = {
            'lat': node.location.y,
            'lng': node.location.x,
            'osm_id': node.osm_id
        }
        # Skip if it's the same as start or end point
        if (node_point['lat'] == start_point['lat'] and node_point['lng'] == start_point['lng']) or \
           (node_point['lat'] == end_point['lat'] and node_point['lng'] == end_point['lng']):
            continue
        between_nodes.append(node_point)
    
    return between_nodes

def sort_nodes_by_distance_from_point(nodes, reference_point):
    """Sort nodes by their distance from a reference point."""
    def distance_to_point(node):
        return calculate_distance(
            reference_point['lat'], reference_point['lng'],
            node['lat'], node['lng']
        )
    
    return sorted(nodes, key=distance_to_point)

def filter_close_nodes(nodes, min_distance=5):
    """Filter out nodes that are too close to each other (less than min_distance meters)."""
    if not nodes:
        return nodes
        
    filtered = [nodes[0]]  # Always keep the first node
    
    for node in nodes[1:]:
        # Check distance to the last kept node
        last_node = filtered[-1]
        distance = calculate_distance(
            last_node['lat'], last_node['lng'],
            node['lat'], node['lng']
        )
        
        # Only add node if it's far enough from the last kept node
        if distance >= min_distance:
            filtered.append(node)
        else:
            print(f"Skipping node {node['osm_id']} as it's too close ({distance:.2f}m) to node {last_node['osm_id']}")
    
    return filtered

def process_path_points(path_points):
    if not path_points:
        return path_points
        
    new_path = []
    # Add first point
    new_path.append(path_points[0])
    
    # Process each consecutive pair
    for i in range(len(path_points) - 1):
        current = path_points[i]
        next_point = path_points[i + 1]
        
        # Find nodes between current and next point
        between_nodes = find_nodes_between_points(current, next_point)
        
        # Add the between nodes, skipping those in the exclude list
        for node in between_nodes:
            print(node['osm_id'])
            if not is_node_to_exclude(node['osm_id']):
                new_path.append(node)
                print(f"Added node {node['osm_id']} between ({current['lat']}, {current['lng']}) and ({next_point['lat']}, {next_point['lng']})")
            else:
                print(f"Skipped node {node['osm_id']} as it has highway=crossing tag")
        
        # Add the next point
        new_path.append(next_point)
    
    return new_path

def update_json_with_osm_ids(json_file_path):
    # Load the routes JSON file
    with open(json_file_path, 'r') as f:
        routes_data = json.load(f)
    
    # Counters
    updated_count = 0
    added_count = 0
    excluded_count = 0
    too_close_count = 0
    
    # Process each company's routes
    for company_data in routes_data.values():
        for route in company_data.get('routes', []):
            # Process markers
            for marker in route.get('coordinates', {}).get('markers', []):
                position = marker.get('position', {})
                lat = position.get('lat')
                lon = position.get('lng')
                
                # If node doesn't have OSM ID, add one
                if lat and lon and not position.get('osm_id'):
                    position['osm_id'] = create_composite_id(lat, lon)
                    updated_count += 1
                    print(f"Added OSM ID to marker at ({lat}, {lon})")
            
            # Process path points and add existing nodes between them
            for path_key in ['path1', 'path2']:
                path_points = route.get('coordinates', {}).get(path_key, [])
                if path_points:
                    # Add OSM IDs to existing points
                    for point in path_points:
                        lat = point.get('lat')
                        lon = point.get('lng')
                        if lat and lon and not point.get('osm_id'):
                            point['osm_id'] = create_composite_id(lat, lon)
                            updated_count += 1
                            print(f"Added OSM ID to path point at ({lat}, {lon})")
                    
                    # Process path points sequentially
                    new_path = []
                    # Add first point
                    new_path.append(path_points[0])
                    
                    # Process each consecutive pair
                    for i in range(len(path_points) - 1):
                        current = path_points[i]
                        next_point = path_points[i + 1]
                        
                        # Find nodes between current and next point
                        between_nodes = find_nodes_between_points(current, next_point)
                        
                        # Filter out nodes that are in the exclude list
                        filtered_nodes = [node for node in between_nodes if not is_node_to_exclude(node['osm_id'])]
                        excluded_count += len(between_nodes) - len(filtered_nodes)
                        
                        # Sort filtered nodes by distance from current point
                        sorted_nodes = sort_nodes_by_distance_from_point(filtered_nodes, current)
                        
                        # Filter out nodes that are too close to each other
                        original_count = len(sorted_nodes)
                        sorted_nodes = filter_close_nodes(sorted_nodes)
                        too_close_count += original_count - len(sorted_nodes)
                        
                        # Add the sorted and filtered nodes
                        for node in sorted_nodes:
                            new_path.append(node)
                            print(f"Added node {node['osm_id']} between ({current['lat']}, {current['lng']}) and ({next_point['lat']}, {next_point['lng']})")
                        
                        # Add the next point
                        new_path.append(next_point)
                    
                    added_count += len(new_path) - len(path_points)
                    route['coordinates'][path_key] = new_path
    
    # Save the updated JSON
    output_file = 'updated.json'
    with open(output_file, 'w') as f:
        json.dump(routes_data, f, indent=2)
    
    return updated_count, added_count, excluded_count, too_close_count, output_file

if __name__ == '__main__':
    routes_file = 'coordinates_updated.json'
    
    print(f"Starting analysis of {routes_file}...")
    
    # Load nodes to exclude first
    load_nodes_to_exclude()
    
    # Update the JSON file with OSM IDs and filtered nodes
    updated, added, excluded, too_close, output_file = update_json_with_osm_ids(routes_file)
    
    print("\nSummary:")
    print(f"Updated {updated} nodes with OSM IDs")
    print(f"Added {added} nodes between points")
    print(f"Excluded {excluded} nodes with highway=crossing tag")
    print(f"Excluded {too_close} nodes that were too close to other nodes")
    print(f"Output saved to {output_file}") 