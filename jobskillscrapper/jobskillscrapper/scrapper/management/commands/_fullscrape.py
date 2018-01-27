from urlparse import urlparse

from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch, RequestsHttpConnection

from scrapper.models import Job, Skill, JobSkill, ParsedProfile, ProfilToParse, ProfilJob
from ._tor import tor_request
import boto3
import time


class ScrapperHandler(object):

    es = None

    def __init__(self, service, url):
        scrapper = LinkedInJobSkillScrapper if service == 'linkedin' else ViadeoJobSkillScrapper

        #toparse = ProfilToParse.objects.filter(site=service).first()
        self.config_es()

        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName='sqs-scraper')

        while self.get_number_message() > 1 :
            for message in queue.receive_messages(MaxNumberOfMessages=10):

                try: 
                    sc = scrapper(message.body)
                    if sc.save:
                        self.save_es(sc.data, sc.profil.id)

                    message.delete()
                except:
                    time.sleep(10)
                    ScrapperHandler(service=service, url=url)

        
        #if not toparse:
        #    sc = scrapper(url)
        #    if sc.save:
                #self.save_es(sc.data, sc.profil.id)
            #toparse = ProfilToParse.objects.filter(site=service).first()

        #while toparse:
            #sc = scrapper(toparse.url)
            #if sc.save:
                #self.save_es(sc.data, sc.profil.id)
            #toparse.delete()
            #toparse = ProfilToParse.objects.filter(site=service).first()

    def get_number_message(self):
        client = boto3.client('sqs')
        res = client.get_queue_attributes(QueueUrl='https://sqs.eu-west-1.amazonaws.com/xxxxx/sqs-scraper', AttributeNames=['ApproximateNumberOfMessages'])
        return res['Attributes']['ApproximateNumberOfMessages']

    def config_es(self):
        self.es = Elasticsearch(
            ["https://xxxxxx.eu-west-1.es.amazonaws.com/"],
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )


    def save_es(self, datas, id_profil):
        self.es.index(index="datas", doc_type="cv", id=id_profil, body=datas)



class JobSkillScrapper(object):
    bs = None
    url = None
    data = {}
    next_url = None
    profil = None
    save=False
    client_sqs = None
    start_time = 0

    def __init__(self, url):
        
        self.url = self.transform_url(url)
        self.save=False
        parsedprofile, created = ParsedProfile.objects.get_or_create(url=self.url)
        self.profil = parsedprofile


        #self.client_sqs =  boto3.client('sqs')
        # Initializing fake browser to bypass LinkedIn security
        
        re = tor_request()
        r = re.get(self.url)


        self.set_html(r)
        self.parse(created)


    def set_html(self, text):
        self.bs = BeautifulSoup(text, 'html.parser')

    def transform_url(self, url):
        url = urlparse(url)
        return 'http://' + url.netloc + url.path

    def parse(self, not_parsed):
        """ Parse LinkedIn profile """
        print('Parsing profile : {}'.format(self.url))

        if not_parsed:
            self.parse_profil()
            self.parse_jobs()
            self.parse_educations()
            self.parse_skills()
            self.persist()
        else:
            print('> Already parsed  --- {}')

        #self.parse_next_profiles()


    def add_profil_to_parse(self, url, service):
        #if not ProfilToParse.objects.filter(url=url).exists() and not ParsedProfile.objects.filter(url=url).exists():
            #if ProfilToParse.objects.count() < 1000000:
        try : 
            ProfilToParse.objects.create(url=url, site=service)
            self.client_sqs.send_message(QueueUrl="https://sqs.eu-west-1.amazonaws.com/xxxxxxxx/sqs-scraper", MessageBody=url)
        except:
            pass
                    #print("> Duplicate stopped")

    def persist(self):
        """ Save jobs and skills into database """

        # Persist profil with at least one job and four skills
        if self.data['jobs'] and len(self.data['skills']) >= 3:

            jobs = []
            for job_name in self.data['jobs']:
                job, created = Job.objects.get_or_create(name=job_name['title'])
                jobs.append(job)

            skills = []
            for skill_name in self.data['skills']:
                skill, created = Skill.objects.get_or_create(name=skill_name)
                skills.append(skill)

            msg = '> Persisted - {} job(s) - {} skill(s)'

            jobskills = []
            for job in jobs:
                for skill in skills:
                    jobskills.append(JobSkill(job=job, skill=skill))
            JobSkill.objects.bulk_create(jobskills)

            jobprofil = []
            for job in jobs:
                jobprofil.append(ProfilJob(job=job, profil=self.profil))
            ProfilJob.objects.bulk_create(jobprofil)

            self.save=True

        else:
            msg = '> Not persisted - {} job(s) - {} skill(s)'
        print(msg.format(len(self.data['jobs']), len(self.data['skills'])))



class ViadeoJobSkillScrapper(JobSkillScrapper):
    """ Allow to parse public Viadeo profile and retrieve data """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:53.0) Gecko/20100101 Firefox/53.0',
        'Accept': '*/*',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-IsAJAXForm': '1',
        'x-requested-with': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }

    def is_valid_url(self, url):
        return url.startswith('http://fr.viadeo.com/fr/')


    def parse_profil(self):
        self.data['profil'] = {}

        name = self.bs.find(class_="name")
        title = self.bs.find(class_="rc-card-content")
        description = self.bs.find(class_="detailResume")
        location = self.bs.find(class_="location")

        if name :
            self.data['profil']['firstname'] = name.find(class_="firstname").get_text().strip()
            self.data['profil']['lastname'] = name.find(class_="lastname").get_text().strip()

        if title :
            title = title.find('h3')
            if title:
                self.data['profil']['title'] = title.get_text().strip()

        if description :
            self.data['profil']['resume'] = description.get_text().strip()

        if location : 
            self.data['profil']['location'] = location.get_text().strip()
        

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

                self.data['educations'].append(educ)


    def parse_next_profiles(self):
        bs_browse_map = self.bs.find('ul', id='alsoVisitedTarget')
        if bs_browse_map:
            for bs_profile_card in bs_browse_map.find_all('li', class_='contact'):
                url = self.transform_url(bs_profile_card.find('a').get('href'))
                if self.is_valid_url(url):
                    self.add_profil_to_parse(url, "viadeo")




class LinkedInJobSkillScrapper(JobSkillScrapper):
    """ Allow to parse public LinkedIn profile and retrieve data """
    headers = {
        'Host': 'www.linkedin.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:53.0) Gecko/20100101 Firefox/53.0',
        'Accept': '*/*',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.linkedin.com/',
        'X-IsAJAXForm': '1',
        'x-requested-with': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }

    def parse_jobs(self):
        """ Parse jobs """
        self.data['jobs'] = []

        bs_jobs = self.bs.find(id='experience')
        if bs_jobs:
            for bs_job in bs_jobs.find_all(class_='position'):
                bs_job_title = bs_job.find('h4')
                if bs_job_title:
                    self.data['jobs'].append(bs_job_title.get_text().lower())

    def parse_skills(self):
        """ Parse skills """
        self.data['skills'] = []

        bs_skills = self.bs.find(id='skills')
        if bs_skills:
            for bs_skill in bs_skills.find_all(class_='skill'):
                self.data['skills'].append(bs_skill.get_text().lower())

    def parse_next_profiles(self):
        bs_browse_map = self.bs.find(class_='browse-map')
        if bs_browse_map:
            for bs_profile_card in bs_browse_map.find_all(class_='profile-card'):
                url = self.transform_url(bs_profile_card.find('a').get('href'))
                self.add_profil_to_parse(url, "linkedin")