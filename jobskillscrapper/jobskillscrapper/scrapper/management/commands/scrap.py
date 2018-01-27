from django.core.management.base import BaseCommand

from ._fullscrape import ScrapperHandler


class Command(BaseCommand):
    help = 'Parse an profile to retrieve jobs & skills'

    def add_arguments(self, parser):
        pass
        #parser.add_argument('--service', type=str)
        #parser.add_argument('link', type=str)

    def handle(self, *args, **options):
        self.stdout.write('# Starting scrapper')

        #service = options.get('service')
        #link = options.get('link') if options.get('link') else None

        service="viadeo"

        link = "http://fr.viadeo.com/fr/profile/romain.tenailleau"

        ScrapperHandler(service=service, url=link)

        self.stdout.write('\n# Ending scrapper')
