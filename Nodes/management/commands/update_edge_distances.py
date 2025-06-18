from django.core.management.base import BaseCommand
from Nodes.models import Edge
from django.contrib.gis.geos import LineString
from django.contrib.gis.measure import Distance
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update all edges in the database and recalculate distance in meters.'

    def handle(self, *args, **options):
        updated_count = 0
        for edge in Edge.objects.all():
            if edge.geometry is not None:
                # Transform geometry to Web Mercator (meters)
                geom_3857 = edge.geometry.transform(3857, clone=True)
                distance_m = geom_3857.length
                if edge.distance != distance_m:
                    edge.distance = distance_m
                    edge.save(update_fields=['distance'])
                    updated_count += 1
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} edges with recalculated distances in meters.')) 