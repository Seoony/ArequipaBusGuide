from django.core.management.base import BaseCommand
from Routes.import_routes import import_routes_from_json

class Command(BaseCommand):
    help = 'Import routes from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing routes data')

    def handle(self, *args, **options):
        json_file = options['json_file']
        self.stdout.write(self.style.SUCCESS(f'Starting import from {json_file}'))
        import_routes_from_json(json_file)
        self.stdout.write(self.style.SUCCESS('Import completed')) 