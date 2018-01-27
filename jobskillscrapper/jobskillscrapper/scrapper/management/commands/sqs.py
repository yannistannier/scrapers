from django.core.management.base import BaseCommand
import boto3

from scrapper.models import Job, Skill, JobSkill, ParsedProfile, ProfilToParse, ProfilJob



class Command(BaseCommand):
    help = 'Parse an profile to retrieve jobs & skills'


    def handle(self, *args, **options):
        self.stdout.write('# Importe to sqs')
       	client = boto3.client('sqs')

        #for profil in ProfilToParse.objects.all():
        	#print(profil.url)
        	#client.send_message(QueueUrl="https://sqs.eu-west-1.amazonaws.com/xxxxxx/sqs-scraper", MessageBody=profil.url)

        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName='sqs-scraper')
        res = client.get_queue_attributes(QueueUrl='https://sqs.eu-west-1.amazonaws.com/xxxxx/sqs-scraper', AttributeNames=['ApproximateNumberOfMessages'])
        print(res['Attributes']['ApproximateNumberOfMessages']) 

        #for message in queue.receive_messages(MaxNumberOfMessages=10):
        	#print message.body
        
        self.stdout.write('\n# import finish')
