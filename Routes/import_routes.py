import json
import logging
from django.db import transaction
from django.contrib.gis.geos import LineString
from django.contrib.gis.measure import Distance
from .models import TransportCompany, Route, RouteEdge, RouteNode
from Nodes.models import Node, Edge

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RouteImportError(Exception):
    """Custom exception for route import errors"""
    pass

def validate_route_data(route_data):
    """Validate route data structure"""
    required_fields = ['route_name', 'route_url', 'coordinates']
    for field in required_fields:
        if field not in route_data:
            raise RouteImportError(f"Missing required field: {field}")
    
    if 'markers' not in route_data['coordinates'] or len(route_data['coordinates']['markers']) < 2:
        raise RouteImportError("Route must have at least 2 markers")
    
    if 'path1' not in route_data['coordinates'] or 'path2' not in route_data['coordinates']:
        raise RouteImportError("Route must have both path1 and path2")
    
    if len(route_data['coordinates']['path1']) < 2 or len(route_data['coordinates']['path2']) < 2:
        raise RouteImportError("Both paths must have at least 2 points")

def import_routes_from_json(json_file_path):
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON file: {json_file_path}")
        return
    
    if not data:
        logger.error("Empty JSON file")
        return
    
    with transaction.atomic():
        for company_name, company_data in data.items():
            try:
                if not company_name or not isinstance(company_name, str):
                    logger.error(f"Invalid company name: {company_name}")
                    continue
                
                if 'business_url' not in company_data:
                    logger.error(f"Missing business_url for company: {company_name}")
                    continue
                
                # Create or get TransportCompany
                company, _ = TransportCompany.objects.get_or_create(
                    name=company_name,
                    defaults={'business_url': company_data['business_url']}
                )
                
                if 'routes' not in company_data or not company_data['routes']:
                    logger.warning(f"No routes found for company: {company_name}")
                    continue
                
                for route_data in company_data['routes']:
                    try:
                        validate_route_data(route_data)
                        
                        # Get start and end nodes from markers
                        start_marker = route_data['coordinates']['markers'][0]
                        end_marker = route_data['coordinates']['markers'][1]
                        
                        try:
                            start_node = Node.objects.get(osm_id=start_marker['position']['osm_id'])
                            end_node = Node.objects.get(osm_id=end_marker['position']['osm_id'])
                        except Node.DoesNotExist as e:
                            logger.error(f"Node not found: {str(e)}")
                            continue
                        
                        # Create Route
                        route = Route.objects.create(
                            company=company,
                            name=route_data['route_name'],
                            route_url=route_data['route_url'],
                            start_node=start_node,
                            end_node=end_node,
                            forward_description=start_marker.get('contenido', ''),
                            return_description=end_marker.get('contenido', '')
                        )
                        
                        # Process path1 (Ida direction)
                        path1 = route_data['coordinates']['path1']
                        for i in range(len(path1) - 1):
                            try:
                                source_node = Node.objects.get(osm_id=path1[i]['osm_id'])
                                target_node = Node.objects.get(osm_id=path1[i + 1]['osm_id'])
                                
                                # Create LineString geometry
                                line = LineString([
                                    source_node.location,
                                    target_node.location
                                ], srid=4326)
                                
                                # Calculate distance in meters
                                distance = Distance(m=line.length)
                                
                                # Create or get Edge with geometry and distance
                                edge, _ = Edge.objects.get_or_create(
                                    source=source_node,
                                    target=target_node,
                                    defaults={
                                        'geometry': line,
                                        'distance': distance.m
                                    }
                                )
                                
                                # Create RouteEdge for Ida
                                RouteEdge.objects.create(
                                    route=route,
                                    edge=edge,
                                    order=i,
                                    direction='I'
                                )
                                
                                # Create RouteNode for Ida
                                RouteNode.objects.create(
                                    route=route,
                                    node=source_node,
                                    order=i,
                                    direction='I'
                                )
                            except Node.DoesNotExist as e:
                                logger.error(f"Node not found in path1: {str(e)}")
                                continue
                            except Exception as e:
                                logger.error(f"Error processing path1 edge: {str(e)}")
                                continue
                        
                        # Add last node of path1
                        try:
                            last_node = Node.objects.get(osm_id=path1[-1]['osm_id'])
                            RouteNode.objects.create(
                                route=route,
                                node=last_node,
                                order=len(path1) - 1,
                                direction='I'
                            )
                        except Node.DoesNotExist as e:
                            logger.error(f"Last node not found in path1: {str(e)}")
                            continue
                        
                        # Process path2 (Vuelta direction)
                        path2 = route_data['coordinates']['path2']
                        for i in range(len(path2) - 1):
                            try:
                                source_node = Node.objects.get(osm_id=path2[i]['osm_id'])
                                target_node = Node.objects.get(osm_id=path2[i + 1]['osm_id'])
                                
                                # Create LineString geometry
                                line = LineString([
                                    source_node.location,
                                    target_node.location
                                ], srid=4326)
                                
                                # Calculate distance in meters
                                distance = Distance(m=line.length)
                                
                                # Create or get Edge with geometry and distance
                                edge, _ = Edge.objects.get_or_create(
                                    source=source_node,
                                    target=target_node,
                                    defaults={
                                        'geometry': line,
                                        'distance': distance.m
                                    }
                                )
                                
                                # Create RouteEdge for Vuelta
                                RouteEdge.objects.create(
                                    route=route,
                                    edge=edge,
                                    order=i + len(path1),  # Continue order from path1
                                    direction='V'
                                )
                                
                                # Create RouteNode for Vuelta
                                RouteNode.objects.create(
                                    route=route,
                                    node=source_node,
                                    order=i,
                                    direction='V'
                                )
                            except Node.DoesNotExist as e:
                                logger.error(f"Node not found in path2: {str(e)}")
                                continue
                            except Exception as e:
                                logger.error(f"Error processing path2 edge: {str(e)}")
                                continue
                        
                        # Add last node of path2
                        try:
                            last_node = Node.objects.get(osm_id=path2[-1]['osm_id'])
                            RouteNode.objects.create(
                                route=route,
                                node=last_node,
                                order=len(path2) - 1,
                                direction='V'
                            )
                        except Node.DoesNotExist as e:
                            logger.error(f"Last node not found in path2: {str(e)}")
                            continue
                            
                        logger.info(f"Successfully imported route: {route.name}")
                        
                    except RouteImportError as e:
                        logger.error(f"Invalid route data: {str(e)}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing route: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error processing company {company_name}: {str(e)}")
                continue

if __name__ == '__main__':
    import_routes_from_json('updated.json') 