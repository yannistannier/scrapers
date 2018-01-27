#-*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from scraper import Scraper
import re, datetime, locale, requests
from sys import exit
from django.core.validators import validate_email
import re
from pro.models import Pro



class LetudiantScraper(Scraper):

    url = "http://jobs-stages.letudiant.fr/emploi/offres/operation-business-67.html/page-%d.html"
    valid_email = None
    exclude = ('mazars', 'flatchr', "L'Etudiant", "SNCF", "Sony Music")

    def parse_link(self, url):
        res = requests.get(url)
        self.bs = BeautifulSoup(res.text, 'html.parser')
        self.parse_job()

    def parse(self):
        for x in xrange(1,101):
            print('-------')
            print(x)
            page = self.url % x
            res = requests.get(page)
            self.bs = BeautifulSoup(res.text, 'html.parser')
            self.parse_urls()


    def parse_urls(self):
        self.data['url'] = []
        bs_urls = self.bs.find(class_='l-content')

        if bs_urls:
            i = 0
            for bs_url in bs_urls.find_all(class_='c-block'):

                url = bs_url.find('h3').find('a', href=True)

                self.url_job = "http://jobs-stages.letudiant.fr" + str(url['href'])
                self.parse_link("http://jobs-stages.letudiant.fr" + str(url['href']))

                if self.valid_email :
                    self.save()


    def parse_job(self):
        self.valid_email = False
        if self.bs.find(class_='c-list--def'):
            for email in self.bs.find(class_='c-list--def').find_all(class_='c-list--def__val'):
                try:
                    validate_email(email.get_text().strip())
                    self.valid_email = email.get_text().strip()
                    break
                except Exception:
                    pass

        if self.valid_email == False:
            return None

        job = {}

        id = re.findall('\d+', self.bs.find(class_='c-hero__etablissement__ref').get_text())

        job['job_id'] = id[0]

        print(job['job_id'])

        job['job_email'] = self.valid_email

        title=self.bs.find(class_='c-hero__etablissement__info__name u-typo-h5').get_text().strip().split(',')

        job['job_title']=title[0]
        job['job_contrats_list'] = self._get_contrat(title[-1].strip())

        job['job_company'] = self.bs.find(class_='c-hero__inner__infoplus__item c-hero__inner__infoplus__item--name').get_text().strip().split('(')[0].strip()

        bs_image = self.bs.find(class_='c-hero__etablissement__logo')
        if bs_image:
            job['job_url_image'] = "http://jobs-stages.letudiant.fr"+bs_image.find('img')['src']
        else:
            job['job_url_image'] = "https://xxxx.amazonaws.com/media/pro/default.jpg"


        job['job_description'] = ""

        for elem in self.bs.find(class_='s-editorial').find_all(['h5', 'p']):
            if elem.get_text().strip() == "Postuler" :
                break
            job['job_description'] = job['job_description'] + elem.prettify()


        #job['job_contrats_list'] = self.parse_contract(job['job_description'])
        job['job_contrats_list'] = [3]

        job['job_study'] = self._get_study(self.parse_study(job['job_description']))
        job['job_experience'] = self._get_experience(self.parse_experience(job['job_description']))

        job['job_location'] = self.bs.find(class_='c-hero__inner__infoplus__item c-hero__inner__infoplus__item--localisation').get_text().strip()

        if self.bs.find(class_='c-list--def').find_all(class_='c-list--def__name')[-1].get_text().strip() == "Contact :":
            job['job_contact'] = self.bs.find(class_='c-list--def').find_all(class_='c-list--def__val')[-1].get_text().strip()

        job['job_scraper_site'] = "letudiant"
        job['job_scraper_url'] = self.url_job

        self.data['job'] = job


    def parse_experience(self, text):
        if any(s in text for s in [u"moins d'1 an"]):
            return 2

        if any(s in text for s in [u"De 1 à 2 ans"]):
            return 2

        if any(s in text for s in [u"De 2 à 5 ans"]):
            return 3

        return None

    def parse_secteur(self, text):
        return [tb.strip() for tb in text.split('/') if len(tb) > 3]

    def parse_contract(self, text):
        contrat = []
        if any(s in text for s in ["Interim"]):
            contrat.append(4)
        if any(s in text for s in ["CDD", "6 mois"]):
            contrat.append(2)
        if any(s in text for s in ["CDI", u"Durée indéterminée"]):
            contrat.append(1)

        return contrat

    def parse_study(self, text):
        if any(s in text for s in ["bac+2", "bac +2", "Bac+2", "Bac +2", "BAC+2", "BAC +2", "BTS", "DUT", "bts"]):
            return  9
        if any(s in text for s in ["bac+3", "bac +3", "Bac+3", "Bac +3", "BAC+3", "BAC +3", "Licence", "licence", "Bachelor", "bachelor"]):
            return  10
        if any(s in text for s in ["bac+4", "bac +4", "Bac+4", "Bac +4", "BAC+4", "BAC +4"]):
            return  11
        if any(s in text for s in ["bac+5", "bac +5", "Bac+5", "Bac +5", "BAC+5", "BAC +5"]):
            return  12
        if any(s in text for s in ["bac+7", "bac +7", "Bac+7", "Bac +7", "BAC+7", "BAC +7", "Doctorat", "doctorat"]):
            return  13

        return None

    def save(self):
        try :
                if self.data['job']['job_company'] in self.exclude:
                    print ("%s exclude" % str(self.data['job']['job_company']))
                    return None
                pro = Pro.objects.get(id=24)
                res = self.create_job(pro, **self.data['job'])
                if res :
                    print "SUCCES"
                else:
                    print "no save"
        except Exception,e:
            print "FAIL : "
            print str(e)