import os
import django
import json
from django.contrib.gis.geos import Point

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ArequipaBusGuide.settings')
django.setup()

from Nodes.models import Node

def create_composite_id(lat, lon):
    # Format lat and lon to 7 decimal places and combine them
    return f"{lat:.7f}_{lon:.7f}"

def process_node(lat, lon):
    try:
        # Create Point object for the location
        location = Point(lon, lat, srid=4326)
        
        # Create composite ID from lat and lon
        osm_id = create_composite_id(lat, lon)
        
        # Create new node
        Node.objects.create(osm_id=osm_id, location=location)
        return "created"
            
    except Exception as e:
        print(f"Error processing node: {str(e)}")
        return "error"

def import_nodes_from_routes(routes_file_path):
    # Load the routes JSON file
    with open(routes_file_path, 'r') as f:
        routes_data = json.load(f)
    
    # Counters
    created_count = 0
    error_count = 0
    
    # Process each company's routes
    for company_data in routes_data.values():
        for route in company_data.get('routes', []):
            # Process markers
            for marker in route.get('coordinates', {}).get('markers', []):
                position = marker.get('position', {})
                lat = position.get('lat')
                lon = position.get('lng')
                osm_id = position.get('osm_id')
                
                # Only process nodes without OSM ID
                if lat and lon and not osm_id:
                    result = process_node(lat, lon)
                    if result == "created":
                        created_count += 1
                        print(f"Created new node at ({lat}, {lon}) with ID {create_composite_id(lat, lon)}")
                    else:
                        error_count += 1
            
            # Process path points
            for path_key in ['path1', 'path2']:
                for point in route.get('coordinates', {}).get(path_key, []):
                    lat = point.get('lat')
                    lon = point.get('lng')
                    osm_id = point.get('osm_id')
                    
                    # Only process nodes without OSM ID
                    if lat and lon and not osm_id:
                        result = process_node(lat, lon)
                        if result == "created":
                            created_count += 1
                            print(f"Created new node at ({lat}, {lon}) with ID {create_composite_id(lat, lon)}")
                        else:
                            error_count += 1
    
    return created_count, error_count

if __name__ == '__main__':
    routes_file = 'routes_with_coordinates_updated.json'
    
    print(f"Starting import from {routes_file}...")
    created, errors = import_nodes_from_routes(routes_file)
    
    print("\nSummary:")
    print(f"Created {created} new nodes")
    print(f"Errors: {errors}") 