from urlparse import urlparse
from bs4 import BeautifulSoup
import boto3
import time
import hashlib
import json
import base64



class ViadeoScrapper(object):

    data = {}
    bs = None
    md5 = None
    url = None
    start = None
    kinesis_batch=None

    def __init__(self, html, url):
        self.bs = BeautifulSoup(html, 'html.parser')
        self.url = url
        self.md5 = hashlib.md5(self.url).hexdigest()

        self.parse_profil()
        self.parse_jobs()
        self.parse_educations()
        self.parse_skills()
        self.get_lang()


        self.data['user']['url'] = self.url
        self.data['user']['md5'] = self.md5
        self.data['user']['lang'] = self.lang

        self.push_urls_to_dynamomdb()
        self.push_to_kinesis()



    def get_lang(self):
        url = urlparse(self.url)
        self.lang = url.netloc.split(".")[0]


    def push_to_kinesis(self):
        topush = []
        self.kinesis_batch = {
            'Data' : json.dumps(self.data),
            'PartitionKey' : str(self.md5)
        }
        #kinesis = boto3.client('kinesis', region_name='us-west-2')
        #kinesis.put_record(StreamName="receive-data-to-parse", Data=json.dumps(self.data), PartitionKey=str(self.md5))


    def push_urls_to_dynamomdb(self):
        bs_browse_map = self.bs.find('ul', id='alsoVisitedTarget')
        if bs_browse_map:
            batch_item = []
            client = boto3.resource('dynamodb', region_name='us-west-2')
            table = client.Table('url-to-handle')

            with table.batch_writer() as batch:
                for bs_profile_card in bs_browse_map.find_all('li', class_='contact'):
                    url = self.transform_url(bs_profile_card.find('a').get('href'))
                    batch.put_item(
                        Item={
                                "md5" : hashlib.md5(url).hexdigest(),
                                "url" : url
                            }
                    )
                
    def transform_url(self, url):
        url = urlparse(url)
        return 'http://' + url.netloc + url.path


    def parse_profil(self):
        self.data['user'] = {}

        name = self.bs.find(class_="name")
        title = self.bs.find(class_="rc-card-content")
        description = self.bs.find(class_="detailResume")
        location = self.bs.find(class_="location")

        if name :
            self.data['user']['firstname'] = name.find(class_="firstname").get_text().strip()
            self.data['user']['lastname'] = name.find(class_="lastname").get_text().strip()

        if title :
            title = title.find('h3')
            if title:
                self.data['user']['title'] = title.get_text().strip()

        if description :
            self.data['user']['resume'] = description.get_text().strip()

        if location : 
            self.data['user']['location'] = location.get_text().strip()
        

    def parse_jobs(self):
        """ Parse jobs """
        self.data['jobs'] = []

        bs_jobs = self.bs.find('ul', id='memberContent')
        if bs_jobs:
            for bs_job in bs_jobs.find_all('li', class_='blockitemEmployment'):
                job = {}

                bs_job_title = bs_job.find('p', class_='titre')
                bs_job_company = bs_job.find('span', {'itemprop':'name'})
                bs_job_summary = bs_job.find(class_="description")

                bs_date = bs_job.find(class_="date")

                if bs_job_company:
                    job['company'] = bs_job_company.get_text().strip()
                elif bs_job_title.nextSibling:
                    job['company'] = bs_job_title.nextSibling.get_text()


                if bs_date :
                    date = {}
                    df = bs_date.find(class_="end-date")
                    dd = bs_date.find(class_="start-date")
                    if dd :
                        date['start-date'] = dd.get_text().strip()
                    if df :
                        date['end-date'] = df.get_text().strip()
                    job['periode'] = date

                if bs_job_title:
                    job['title'] = bs_job_title.get_text().strip().lower()

                if bs_job_summary:
                    job['description'] = bs_job_summary.get_text().strip()

                self.data['jobs'].append(job)


    def parse_skills(self):
        """ Parse skills """
        self.data['skills'] = []

        bs_skills = self.bs.find('div', id='sectionPublicSkill')
        if bs_skills:
            for bs_skill in bs_skills.find_all('li', class_='isMemberSkill'):
                self.data['skills'].append(bs_skill.get_text().lower())


    def parse_educations(self):
        """ Parse jobs """
        self.data['educations'] = []

        bs_jobs = self.bs.find('ul', id='memberContent')
        if bs_jobs:
            for bs_job in bs_jobs.find_all('li', class_='blockitemEducation'):
                educ = {}

                school= bs_job.find(class_="itemName")
                degree= bs_job.find(class_="type")

                if school :
                    educ['school'] = school.get_text().strip()

                if degree :
                    educ['degree'] = degree.get_text().strip()

                bs_date = bs_job.find(class_="date")

                if bs_date :
                    date = {}
                    df = bs_date.find(class_="end-date")
                    dd = bs_date.find(class_="start-date")
                    if dd :
                        date['start-date'] = dd.get_text().strip()
                    if df :
                        date['end-date'] = df.get_text().strip()
                    educ['periode'] = date

                self.data['educations'].append(educ)


def lambda_handler(event, context):
    batch=[]
    kinesis = boto3.client('kinesis', region_name='us-west-2')

    for record in event['Records']:
        payload=base64.b64decode(record["kinesis"]["data"])
        data = json.loads(payload)
        v = ViadeoScrapper(data['html'], data['url'])
        batch.append(v.kinesis_batch)

    kinesis.put_records(StreamName="receive-data-to-parse", Records=batch)

    print('-- Processed %s records' % str(len(event['Records'])))
