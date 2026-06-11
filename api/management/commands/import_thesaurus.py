from django.core.management.base import BaseCommand
from api.importers.arches import load_instance_thesauri, import_thesaurus
from api.models.arches import ArchesInstance, Thesaurus

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("-i", "--instance", action="store", dest="instance", default="")

    def handle(self, *args, **kwargs):

        instance_url = kwargs['instance']
        if instance_url == '':
            instances = ArchesInstance.objects.all()
        else:
            instances = ArchesInstance.objects.filter(url=instance_url)

        for arches in instances:
            load_instance_thesauri(arches)
            for thesaurus in arches.thesauri.all():
                import_thesaurus(thesaurus)
