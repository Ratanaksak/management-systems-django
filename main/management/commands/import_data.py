import json
from django.core.management.base import BaseCommand
from main.models import Province, District, Commune, Village

class Command(BaseCommand):
    help = 'Import data from JSON files'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str, help="Paths to JSON files")

    def handle(self, *args, **options):
        files = options['files']

        for file_path in files:
            self.stdout.write(self.style.NOTICE(f"Processing file: {file_path}"))

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"Invalid JSON in file {file_path}: {e}"))
                continue

            # Determine the type of data
            if 'provinces' in data:
                self.import_provinces(data['provinces'])
            elif 'districts' in data:
                self.import_districts(data['districts'])
            elif 'communes' in data:
                self.import_communes(data['communes'])
            elif 'villages' in data:
                self.import_villages(data['villages'])
            else:
                self.stdout.write(self.style.ERROR(f"Unknown data type in file: {file_path}"))

    def import_provinces(self, provinces):
        for province_data in provinces:
            province, created = Province.objects.get_or_create(
                id=province_data['id'],
                defaults={
                    'name': province_data['name'],
                    'kh_name': province_data.get('khmer_name', ''),
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Province {province.name} {'created' if created else 'already exists'}"))

    def import_districts(self, districts):
        for district_data in districts:
            district, created = District.objects.get_or_create(
                id=district_data['id'],
                province_id=district_data['province_id'],
                defaults={
                    'name': district_data['name'],
                    'kh_name': district_data.get('khmer_name', ''),
                }
            )
            self.stdout.write(self.style.SUCCESS(f"District {district.name} {'created' if created else 'already exists'}"))

    def import_communes(self, communes):
        for commune_data in communes:
            commune, created = Commune.objects.get_or_create(
                id=commune_data['id'],
                district_id=commune_data['district_id'],
                defaults={
                    'name': commune_data['name'],
                    'kh_name': commune_data.get('khmer_name', ''),
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Commune {commune.name} {'created' if created else 'already exists'}"))

    def import_villages(self, villages):
        for village_data in villages:
            village, created = Village.objects.get_or_create(
                id=village_data['id'],
                commune_id=village_data['commune_id'],
                defaults={
                    'name': village_data['name'],
                    'kh_name': village_data.get('khmer_name', ''),
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Village {village.name} {'created' if created else 'already exists'}"))
