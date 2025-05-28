from django.core.management.base import BaseCommand
from Nodes.models import Node
import xml.etree.ElementTree as ET
from django.contrib.gis.geos import Point
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import OSM data from map.xml file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='map.xml',
            help='Path to the OSM XML file'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        self.stdout.write(self.style.SUCCESS(f'Starting OSM import from {file_path}'))
        
        try:
            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Counter for imported nodes
            imported_count = 0
            
            # Process each node in the OSM file
            for node in root.findall('.//node'):
                try:
                    node_id = node.get('id')
                    lat = float(node.get('lat'))
                    lon = float(node.get('lon'))
                    
                    # Create Point object for the location
                    location = Point(lon, lat, srid=4326)
                    
                    # Create or update the Node
                    Node.objects.update_or_create(
                        osm_id=node_id,
                        defaults={
                            'location': location
                        }
                    )
                    
                    imported_count += 1
                    
                    if imported_count % 1000 == 0:
                        self.stdout.write(f'Imported {imported_count} nodes...')
                        
                except Exception as e:
                    logger.error(f'Error processing node {node_id}: {str(e)}')
                    continue
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_count} nodes'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing OSM data: {str(e)}'))
            raise 