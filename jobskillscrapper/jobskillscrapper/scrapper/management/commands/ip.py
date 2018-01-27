from django.core.management.base import BaseCommand

from ._scrapper import ScrapperHandler
from ._tor import request, tor_request


class Command(BaseCommand):
    help = 'Parse an profile to retrieve jobs & skills'


    def handle(self, *args, **options):
        self.stdout.write('# Check my ip')

        re = tor_request()

        print re.get("http://ipinfo.io/ip")

        self.stdout.write('\n# Check my ip')
