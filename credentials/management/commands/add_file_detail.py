import os
from django.core.management.base import BaseCommand
from credentials.models import FileDetail

class Command(BaseCommand):
    help = 'Add file details with tag and location, reading content from a text file'

    def add_arguments(self, parser):
        parser.add_argument('tag', type=str, help='Tag for the file')
        parser.add_argument('location', type=str, help='Location/Path of the file')
        parser.add_argument('text_file', type=str, help='Path to text file containing detailed description')

    def handle(self, *args, **options):
        tag = options['tag']
        location = options['location']
        text_file_path = options['text_file']

        if not os.path.exists(text_file_path):
            self.stdout.write(self.style.ERROR(f"Text file {text_file_path} not found"))
            return

        try:
            with open(text_file_path, 'r') as f:
                content = f.read()
            
            FileDetail.objects.create(
                tag=tag,
                file_location=location,
                detailed_text=content
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully added file detail for '{tag}' at {location}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error adding file detail: {str(e)}"))
