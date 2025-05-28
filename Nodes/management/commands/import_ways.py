from django.core.management.base import BaseCommand
from Nodes.models import Node, Edge
import xml.etree.ElementTree as ET
from django.contrib.gis.geos import LineString
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import edges from ways.xml file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='ways.xml',
            help='Path to the OSM ways XML file'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        self.stdout.write(self.style.SUCCESS(f'Starting ways import from {file_path}'))
        
        try:
            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Counter for imported edges
            imported_count = 0
            skipped_count = 0
            
            # Process each way in the OSM file
            for way in root.findall('.//way'):
                try:
                    # Get all node references in this way
                    node_refs = [nd.get('ref') for nd in way.findall('nd')]
                    
                    # Skip ways with less than 2 nodes
                    if len(node_refs) < 2:
                        skipped_count += 1
                        continue
                    
                    # Create edges between consecutive nodes
                    for i in range(len(node_refs) - 1):
                        source_id = node_refs[i]
                        target_id = node_refs[i + 1]
                        
                        try:
                            # Get source and target nodes
                            source_node = Node.objects.get(osm_id=source_id)
                            target_node = Node.objects.get(osm_id=target_id)
                            
                            # Create LineString geometry
                            line = LineString([
                                source_node.location,
                                target_node.location
                            ], srid=4326)
                            
                            # Calculate distance (in degrees)
                            distance = source_node.location.distance(target_node.location)
                            
                            # Create or update edge
                            Edge.objects.update_or_create(
                                source=source_node,
                                target=target_node,
                                defaults={
                                    'distance': distance,
                                    'geometry': line
                                }
                            )
                            
                            imported_count += 1
                            
                            if imported_count % 1000 == 0:
                                self.stdout.write(f'Imported {imported_count} edges...')
                                
                        except Node.DoesNotExist:
                            logger.warning(f'Node not found: {source_id} or {target_id}')
                            skipped_count += 1
                            continue
                            
                except Exception as e:
                    logger.error(f'Error processing way: {str(e)}')
                    continue
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully imported {imported_count} edges. Skipped {skipped_count} edges.'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing ways data: {str(e)}'))
            raise 