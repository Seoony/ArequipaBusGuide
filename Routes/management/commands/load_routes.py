import json
from django.core.management.base import BaseCommand
from Routes.models import TransportCompany, Route, RouteEdge
from Nodes.models import Node, Edge

class Command(BaseCommand):
    help = 'Load routes data from JSON file into the database'

    def handle(self, *args, **options):
        # Path to the JSON file
        json_file_path = 'src/routes_with_coordinates.json'
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                for route_data in data:
                    # Create or get transport company
                    company, _ = TransportCompany.objects.get_or_create(
                        name=route_data['company_name'],
                        defaults={'business_url': route_data.get('company_url', '')}
                    )
                    
                    # Create or get start and end nodes
                    start_node, _ = Node.objects.get_or_create(
                        name=route_data['start_stop'],
                        latitude=route_data['start_coordinates']['lat'],
                        longitude=route_data['start_coordinates']['lng']
                    )
                    
                    end_node, _ = Node.objects.get_or_create(
                        name=route_data['end_stop'],
                        latitude=route_data['end_coordinates']['lat'],
                        longitude=route_data['end_coordinates']['lng']
                    )
                    
                    # Create route
                    route, created = Route.objects.get_or_create(
                        company=company,
                        name=route_data['route_name'],
                        defaults={
                            'route_url': route_data.get('route_url', ''),
                            'start_node': start_node,
                            'end_node': end_node,
                            'forward_description': route_data.get('forward_description', ''),
                            'return_description': route_data.get('return_description', '')
                        }
                    )
                    
                    # Create route edges
                    if 'edges' in route_data:
                        for order, edge_data in enumerate(route_data['edges']):
                            # Create or get edge
                            edge, _ = Edge.objects.get_or_create(
                                start_node=Node.objects.get_or_create(
                                    name=edge_data['start_stop'],
                                    latitude=edge_data['start_coordinates']['lat'],
                                    longitude=edge_data['start_coordinates']['lng']
                                )[0],
                                end_node=Node.objects.get_or_create(
                                    name=edge_data['end_stop'],
                                    latitude=edge_data['end_coordinates']['lat'],
                                    longitude=edge_data['end_coordinates']['lng']
                                )[0]
                            )
                            
                            # Create route edge
                            RouteEdge.objects.get_or_create(
                                route=route,
                                edge=edge,
                                order=order
                            )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully processed route: {route.name}')
                    )
                    
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'JSON file not found at {json_file_path}')
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR('Invalid JSON file format')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'An error occurred: {str(e)}')
            ) 