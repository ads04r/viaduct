from django.core.management.base import BaseCommand
from api.models.arches import Thesaurus
from api.importers.arches import import_thesaurus

class Command(BaseCommand):
    help = "Imports (or re-imports) all the known thesauri from their respective Arches servers."

    def handle(self, *args, **options):
        for thesaurus in Thesaurus.objects.all():
            import_thesaurus(thesaurus, quiet=False)
