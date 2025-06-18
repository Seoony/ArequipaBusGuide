import json

def check_missing_osm_ids(file_path):
    # Read the routes file
    with open(file_path, 'r') as f:
        companies = json.load(f)
    
    # Check each company
    for company_name, company_data in companies.items():
        for route in company_data.get('routes', []):
            route_name = route.get('route_name', 'Unknown Route')
            coordinates = route.get('coordinates', {})
            # Check path1
            if 'path1' in coordinates:
                for i, node in enumerate(coordinates['path1']):
                    if ('osm_id' not in node) or (node.get('osm_id') is None) or (node.get('osm_id') == ""):
                        print(f"Company: {company_name}")
                        print(f"Route: {route_name}")
                        print(f"Path: path1")
                        print(f"Node index: {i}")
                        print(f"Node coordinates: lat={node.get('lat')}, lng={node.get('lng')}")
                        print(f"Node: {node}")
                        print("-" * 50)
            # Check path2
            if 'path2' in coordinates:
                for i, node in enumerate(coordinates['path2']):
                    if ('osm_id' not in node) or (node.get('osm_id') is None) or (node.get('osm_id') == ""):
                        print(f"Company: {company_name}")
                        print(f"Route: {route_name}")
                        print(f"Path: path2")
                        print(f"Node index: {i}")
                        print(f"Node coordinates: lat={node.get('lat')}, lng={node.get('lng')}")
                        print(f"Node: {node}")
                        print("-" * 50)

if __name__ == "__main__":
    # You can change this to the path of your routes file
    routes_file = "routes_with_coordinates_updated.json"
    check_missing_osm_ids(routes_file) 