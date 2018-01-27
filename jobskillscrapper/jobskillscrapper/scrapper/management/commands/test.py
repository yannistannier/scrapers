from django.core.management.base import BaseCommand

from ._scrapper import ScrapperHandler
from ._tor import request, tor_request

from scrapper.models import Job, Skill, JobSkill, ParsedProfile, ProfilToParse, ProfilJob


class Command(BaseCommand):
    help = 'Parse an profile to retrieve jobs & skills'


    def handle(self, *args, **options):
        self.stdout.write('# Deleting all records')

        Job.objects.all().delete()
        Skill.objects.all().delete()
        JobSkill.objects.all().delete()
        ParsedProfile.objects.all().delete()
        ProfilToParse.objects.all().delete()
        ProfilJoby.objects.all().delete()

        self.stdout.write('\n# All record deleted')
