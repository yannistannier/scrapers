#-*- coding: utf-8 -*-
from __future__ import unicode_literals

import re, datetime, json, random, os
import urllib2
from bs4 import BeautifulSoup
from bs4.element import Tag
from pro.models import ActivityArea, Contract, Employes, Pro, Job, ContractTime, JobQuestion, Tag
from members.models import Experience, Study
from django.contrib.auth.models import User
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from django.utils import timezone
from django.template.defaultfilters import slugify
from django.conf import settings
from StringIO import StringIO
from django.core.files.base import ContentFile

class Scraper(object):
    """ Allow to parse public LinkedIn profile and retrieve data """
    data = {}
    dash = '\u2013'
    proficiency = [
            'Notions', 'Compétence professionnelle limitée', 'Compétence professionnelle',
            'Capacité professionnelle complète', 'Bilingue ou langue natale'
        ]
    months = [
            'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
        ]

    agent = [
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; tr-TR) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
            'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
        ]

    headers = [
            ('User-Agent', random.choice(agent)),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3'),
        ]

    browser = None
    url = None
    stop = 0
    nb_script_max = 20
    list_id=[]
    nb_api_call = 0
    only_id=False

    def __init__(self):
        pass
        # Initializing fake browser to bypass LinkedIn security
        #self.browser = mechanize.Browser()
        #self.browser.set_handle_robots(False)
        #self.browser.addheaders = self.headers
       
        #user = User.objects.exclude(id__in=(1,4,3))
        #user.delete()
        
        # Getting data
        #self.parse()

    def _encode_url(self, url):
        if url.find('https://') != -1:
            url = url[8:]
        elif url.find('http://') != -1:
            url = url[7:]
        return 'https://%s' % urllib2.quote(url.encode('utf-8'))

    def _get_text_with_break_lines(self, bs_tag):
        text = ''
        for tag in bs_tag.recursiveChildGenerator():
            if isinstance(tag, Tag) and tag.name in ('br'):
                text += self.break_line_replace
            else:
                text += tag
        return text

    def _get_text_with_br(self, text):
        return text.strip()
        return text.replace('\n', '</br>')

    def _get_experience(self, id):
        exp = Experience.objects.filter(id=id)
        if exp.exists():
            return exp.first()
        else:
            return None

    def _get_secteur_activite(self, tab):
        for sa in tab :
            for t in sa.split(','):
                if t == "Télécoms":
                    return ActivityArea.objects.get(id=39)
                secteur = ActivityArea.objects.filter(name__icontains=t.strip())
                if secteur.exists():
                    return secteur.first()
        return None

    def _get_contrat(self, text):
        ct = Contract.objects.filter(name__icontains=text)
        if ct.exists():
            return ct.first()
        return None

    def _get_study(self, id):
        study = Study.objects.filter(id=id)
        if study.exists():
            return study.first()
        return None

    def _get_employees(self, nb):
        nb = int(nb.replace(" ", ""))
        if nb > 0 and nb <= 9:
            return Employes.objects.get(id=2)
        if nb >= 10 and nb <= 49:
            return Employes.objects.get(id=3)
        if nb >= 50 and nb <= 499:
            return Employes.objects.get(id=4)
        if nb >= 500 and nb <= 999:
            return Employes.objects.get(id=5)
        if nb >= 1000 and nb <= 4999:
            return Employes.objects.get(id=6)
        if nb >= 5000 :
            return Employes.objects.get(id=1)

    def get_gps_coordonnate(self, address):

        address = re.sub(' +',' ', address.strip())
        address = address.replace('\n', ' ').replace('\r', '')

        url = "https://maps.googleapis.com/maps/api/geocode/json?key=xxxx&address=%s" % address
        url = url.replace(" ", "%20")
        self.nb_api_call = self.nb_api_call+1

        response = urllib2.urlopen(url.encode("UTF-8"))
        datas = json.load(response) 

        if datas['status'] == "OK":
            results = datas['results'][0]
            gps = { 'lat' : results['geometry']['location']['lat'] }
            gps['lng'] = results['geometry']['location']['lng']
            gps['address']=results['formatted_address']
            for data in results['address_components']:
                gps[data['types'][0]]=data['long_name']

            return gps
        #print "No address"
        return None

    def get_or_create_pro(self, pro_company=None, pro_activityarea=None, pro_siege=None, pro_employes=None, pro_ca=None, pro_description=None, pro_image=None, pro_website=None):
        pro = Pro.objects.filter(company__iexact=pro_company.strip())
        if pro.exists():
            return pro.first()
        username = slugify(pro_company)
        user = User.objects.create_user(username, None, "xxxxx")
        user.save()

        pro = Pro()
        pro.scraper=True
        pro.user=user
        pro.company=pro_company.strip()
        pro.email="contact@xxxx.com"
       
        if pro_activityarea:
            pro.activity_area=pro_activityarea

        if pro_website:
            pro.web_site=pro_website
        
        if pro_siege:
            pro_siege = self.get_gps_coordonnate(pro_siege)
            if pro_siege:
                if 'country' in pro_siege:
                    pro.country=pro_siege['country']
                if 'administrative_area_level_1' in pro_siege:
                    pro.administrative_area_level_1=pro_siege['administrative_area_level_1']
                if 'administrative_area_level_2' in pro_siege:
                    pro.administrative_area_level_2=pro_siege['administrative_area_level_2']
                if 'locality' in pro_siege:
                    pro.locality=pro_siege['locality']
                if 'postal_code' in pro_siege:
                    pro.cp=pro_siege['postal_code']
                if 'route' in pro_siege:
                    pro.route=pro_siege['route']
                if 'street_number' in pro_siege:
                    pro.street_number=pro_siege['street_number']
                if 'lat' in pro_siege:
                    pro.latitude=pro_siege['lat']
                if 'lng' in pro_siege:
                    pro.longitude=pro_siege['lng']
                if 'address' in pro_siege:
                    pro.headquarters=pro_siege['address']

        if pro_employes:
            pro.employes=pro_employes
        if pro_ca:
            pro.ca=pro_ca
        if pro_description:
            pro.description=pro_description
        pro.save()

        if pro_image:
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urllib2.urlopen(pro_image).read())
            img_temp.flush()
            pro.image.save(str(pro.id)+".jpg", File(img_temp))

            try:
                os.chmod(settings.MEDIA_ROOT+"pro/"+str(pro.id),0777)
                os.chmod(pro.image.path,0777)
            except:
                print "chmod error"

        return pro

    def create_job(self, pro, job_location=None, job_contrats_list=None, job_web_site=None, job_contact = None, job_tags=None, job_email = None, job_company=None, job_title=None, job_activityarea=None, job_contrats=None, job_study=None, job_experience=None, job_description=None, job_image=None, job_url_image =None, job_scraper_site=None, job_scraper_url=None, job_id=None):
        if job_id:
            job_verif=Job.objects.filter(scraper_id=job_id, scraper_site=job_scraper_site)
        else:
            job_verif=Job.objects.filter(scraper_url=job_scraper_url, scraper_site=job_scraper_site)

        if job_verif.exists():
            print "already exist"
            self.stop=self.stop+1
            return True

        job_verif=Job.objects.filter(job_title=job_title, pro=pro, description=job_description)
        if job_verif.exists():
            print "duplicate"
            return True

        self.stop=0
        job = Job()
        job.pro=pro
        if job_company:
            job.company=job_company.strip()
        if job_title:
            job.job_title=job_title

        if job_activityarea:
            job.activity_area=job_activityarea
        else:
            job.activity_area = ActivityArea.objects.get(id=40)

        if job_description:
            job.description=job_description
        if job_web_site:
            job.web_site=job_web_site

        if job_location:
            job_location = self.get_gps_coordonnate(job_location)
            if job_location:
                if 'country' in job_location:
                    job.country=job_location['country']
                if 'administrative_area_level_1' in job_location:
                    job.administrative_area_level_1=job_location['administrative_area_level_1']
                if 'administrative_area_level_2' in job_location:
                    job.administrative_area_level_2=job_location['administrative_area_level_2']
                if 'locality' in job_location:
                    job.locality=job_location['locality']
                if 'postal_code' in job_location:
                    job.cp=job_location['postal_code']
                if 'route' in job_location:
                    job.route=job_location['route']
                if 'street_number' in job_location:
                    job.street_number=job_location['street_number']
                if 'lat' in job_location:
                    job.latitude=job_location['lat']
                if 'lng' in job_location:
                    job.longitude=job_location['lng']
                if 'address' in job_location:
                    job.job_location=job_location['address']

        if job.country != "France" :
            return False
        job.save()

        if job_tags:
            for kw in job_tags:
                try:
                    kw_object, created = Tag.objects.get_or_create(name__iexact=kw, defaults={'name': kw})
                    job.tags.add(kw_object)
                except: 
                    kw_object = Tag.objects.filter(name__icontains=kw)
                    if kw_object.exists():
                        job.tags.add(kw_object.first())

        if job_contrats:
            job.contracts.add(job_contrats)
        if job_study:
            job.studies.add(job_study)
        if job_experience:
            job.experiences.add(job_experience)

        if job_contrats_list:
            for ct in job_contrats_list:
                job.contracts.add(ct)

        job.contract_time.add(ContractTime.objects.get(id=1))
        if job_image:
            job.image = job_image

        if job_scraper_site:
            job.scraper_site = job_scraper_site

        if job_scraper_url:
            job.scraper_url = job_scraper_url

        if job_id:
            job.scraper_id = job_id

        if job_email:
            job.mp_email = job_email

        if job_contact:
            job.contact = job_contact

        if job_url_image:
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urllib2.urlopen(job_url_image).read())
            img_temp.flush()
            job.image.save(str(job.id) + ".jpg", File(img_temp))


        job.date_posted=timezone.now()
        job.scraper=True
        job.is_video=True
        job.is_audio=True
        job.paid=True
        job.complet=True
        job.active=True
        job.save()

        n = random.randint(1,3)

        questions = self.get_questions(nb=n)

        i = 1
        for q in questions:
            job_qt = JobQuestion(question=q, nb=i, job=job)
            job_qt.save()
            i=i+1

        return True

    def get_list_id(self):
        self.only_id=True
        self.parse()
        return self.list_id

    def get_questions(self, nb=3):
        qt = [
               [
                    "Comment travaillez vous en équipe ?",
                    "De quoi êtes vous le plus fier dans votre carrière ?",
                    "Que vous ont apporté vos précédents emplois ?",
                    "Qu'est-ce qui vous amuse le plus et le moins dans votre travail ?",
                ],
                [
                    "Parlez moi de votre formation en quelques mots"
                    "Qu'est ce qui a motivé votre choix d'orientation ?",
                    "De quoi êtes vous le plus fier dans vos études ?",
                    "Quelle matière vous a le plus passionné durant vos études ?",
                    "Quelles compétences avez-vous développé au travers de vos études ? Citez en trois.",
                ],
                [
                    "Parlez moi de vous",
                    "Quelles sont vos principales qualités ?",
                    "Résumez brièvement votre CV",
                    "Pourquoi devrions nous vous engager ?",
                    "Qui admirez vous ?",
                    "Qu'est ce qui vous motive dans la vie ?",
                    "Quels sont vos objectifs dans la vie ?",
                    "Comment équilibrez vous votre vie professionnelle et personnelle ?",
                    "Quel poste aimeriez vous occuper dans 5 ans ?",
                ],
                [

                    "Que pensez vous apporter à une entreprise ?",
                    "Quelles sont selon vous les valeurs les plus importantes en entreprise ?",
                    "Quel est votre projet professionnel ?"
                    "Qu’attendez-vous de votre hiérarchie ?"
                ],
                [
                    "Pourquoi avez-vous répondu à notre annonce ?",
                    "Que connaissez vous de notre entreprise ?",
                    "Qu'attendez vous de ce poste ?",
                    "Pourquoi pensez vous être le candidat idéal ?",
                    "Que pensez vous apporter à une société ?",
                    "Qu'est-ce qui vous motive à venir travailler chez nous ?",
                ]
            ]

        select_qt = []

        rand = random.sample(range(0, 5), nb)
        for x in rand:
            arr = qt[x]
            rand_array = random.randint(0, len(arr)-1)
            select_qt.append(arr[rand_array])

        return select_qt