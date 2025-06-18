import json
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ArequipaBusGuide.settings')
django.setup()

from Nodes.models import Node

def update_node_coordinates(file_path):
    # Read the routes file
    with open(file_path, 'r') as f:
        companies = json.load(f)
    
    # Track statistics
    total_nodes = 0
    updated_nodes = 0
    failed_nodes = 0
    
    # Process each company
    for company_name, company_data in companies.items():
        for route in company_data.get('routes', []):
            coordinates = route.get('coordinates', {})
            
            # Update path1 nodes
            if 'path1' in coordinates:
                for node in coordinates['path1']:
                    total_nodes += 1
                    if 'osm_id' in node:
                        try:
                            # Get node from database
                            db_node = Node.objects.get(osm_id=node['osm_id'])
                            # Update coordinates in JSON
                            node['lat'] = db_node.location.y  # latitude is y coordinate
                            node['lng'] = db_node.location.x  # longitude is x coordinate
                            updated_nodes += 1
                        except Node.DoesNotExist:
                            print(f"Node with osm_id {node['osm_id']} not found in database")
                            failed_nodes += 1
            
            # Update path2 nodes
            if 'path2' in coordinates:
                for node in coordinates['path2']:
                    total_nodes += 1
                    if 'osm_id' in node:
                        try:
                            # Get node from database
                            db_node = Node.objects.get(osm_id=node['osm_id'])
                            # Update coordinates in JSON
                            node['lat'] = db_node.location.y  # latitude is y coordinate
                            node['lng'] = db_node.location.x  # longitude is x coordinate
                            updated_nodes += 1
                        except Node.DoesNotExist:
                            print(f"Node with osm_id {node['osm_id']} not found in database")
                            failed_nodes += 1
    
    # Save the updated data
    output_file = file_path.replace('.json', '_updated_coordinates.json')
    with open(output_file, 'w') as f:
        json.dump(companies, f, indent=2)
    
    # Print statistics
    print(f"\nUpdate Statistics:")
    print(f"Total nodes processed: {total_nodes}")
    print(f"Successfully updated: {updated_nodes}")
    print(f"Failed updates: {failed_nodes}")
    print(f"\nUpdated data saved to: {output_file}")

if __name__ == "__main__":
    routes_file = "routes_with_coordinates_updated.json"
    update_node_coordinates(routes_file) 