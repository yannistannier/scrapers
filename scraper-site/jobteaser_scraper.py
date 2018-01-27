#-*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from scraper import Scraper
import re, datetime, locale
from sys import exit



class JobTeaserScraper(Scraper):

    url = "https://www.jobteaser.com/fr/offres-emploi-stage?page="
    exclude = ('mazars', 'flatchr')

    def parse_link(self, url):
        self.browser.open(url)
        self.bs = BeautifulSoup(self.browser.response().read(), 'html.parser')
        self.parse_job()
        self.parse_company()

    def parse(self):
        for x in xrange(1,270):
            self.browser.open(str(self.url)+str(x))
            #print str(self.url)+str(x)
            #print "--------------"
            self.bs = BeautifulSoup(self.browser.response().read(), 'html.parser')
            self.parse_urls()

        #print self.list_url
       
    def parse_urls(self):
        self.data['url'] = []
        bs_urls = self.bs.find(id='job-offers')
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        now = datetime.datetime.now()
        now_n1 = datetime.datetime.now() - datetime.timedelta(days=30)

        if bs_urls:
            i = 0
            for bs_url in bs_urls.find_all(class_='job-list__offer--description'):
                url = bs_url.find('a', href=True)
                date_publish = bs_url.find(class_='job-list__offer--description--details').find_all('span')
                date_publish=date_publish[-1].get_text().split(":")
                date_publish=date_publish[1].strip().split(" ")
                #self.data['url'].append("https://www.jobteaser.com"+str(url['href']))
                #print "https://www.jobteaser.com"+str(url['href'])
                self.url_job="https://www.jobteaser.com"+str(url['href'])
                self.job_id = re.search('offres-emploi-stage\/([a-zA-Z0-9]+)-',  self.url_job ).group(1)
                self.list_id.append(self.job_id)

                if self.only_id:
                    #print self.job_id
                    continue

                if self.nb_api_call > 2000:
                    #print "quota api depasse"
                    continue

                if date_publish[1].lower().encode("UTF-8") != now_n1.strftime("%B") and date_publish[1].lower().encode("UTF-8") != now.strftime("%B"):
                     #print "date depasse"
                     continue
                
                if self.stop > self.nb_script_max:
                    #print "stop script"
                    break

                self.parse_link("https://www.jobteaser.com"+str(url['href']))
                #print "-------------------------------------------------------------"
                #print "Entreprise : %s" % self.data['pro']['pro_company'].strip()
                #print "Job : %s " % self.data['job']['job_title'].strip()
                #print "https://www.jobteaser.com"+str(url['href'])
                self.save()
       
    def parse_job(self):
        job = {}
        
        infos = self.bs.find(class_='job-offer-top--infos').find_all('span')

        job['job_title']=self.bs.find(class_='job-offer-top--title').get_text()
        job['job_description']=self._get_text_with_br(self.bs.find(class_='job-offer-container--text').prettify())

        job_detail = self.bs.find(class_="job-offer-details").find(class_="list-unstyled").find_all('li')

        for detail in job_detail:
            tt = detail.find("h6").get_text()
            tx = detail.find("p").get_text() 
            if tt == u"Expérience" :
                job['job_experience']=self._get_experience(self.parse_experience(tx))
            if tt == u"Secteurs" :
                job['job_activityarea']=self._get_secteur_activite(self.parse_secteur(tx))

        job_info = self.bs.find(class_="job-offer-top--infos").find_all('span')

        job['job_contrats'] = self._get_contrat(job_info[0].get_text())
        job['job_location'] = job_info[1].get_text()
        job['job_study'] = self._get_study(self.parse_study(job['job_description']))
        job['job_scraper_site']="jobteaser"
        job['job_scraper_url']=self.url_job

        self.data['job'] = job



    def parse_company(self):
        pro={}
        pro['pro_company']=self.bs.find(class_='job-offer-top--company-name').get_text()

        bs_image = self.bs.find(class_='job-offer-top--logo').find('img')
        pro['pro_image'] = bs_image['src']
        if 'job_activityarea' in self.data['job']:
            pro['pro_activityarea'] = self.data['job']['job_activityarea']

        if self.bs.find(class_='job-offer-top--company-name').find('a'):
            pro_plus = self.parse_company_profil()
            #pro_infos = self.bs.find(class_="CompanyLeft__info_block").find_all('li')
        else:
            pro_plus = {}
            pro_plus['pro_siege'] = self.data['job']['job_location']

        dall = {}
        dall.update(pro)
        dall.update(pro_plus)
        self.data['pro'] = dall
        #print pro_infos

    def parse_company_profil(self):
        url_profil = self.bs.find(class_='job-offer-top--company-name').find('a', href=True)
        page_profil = self.browser.open("https://www.jobteaser.com"+str(url_profil['href']))
        page_profil = BeautifulSoup(self.browser.response().read(), 'html.parser')
        pro_infos = page_profil.find(class_="CompanyLeft__info_block").find_all('li')
        company={}
        for pro in pro_infos:
            line = pro.find_all('p')
            if line[0].get_text() == u"Siège":
                company['pro_siege']=line[1].get_text()
            if line[0].get_text() == u"Effectifs (monde)":
                company['pro_employes'] = self._get_employees(line[1].get_text())
            elif line[0].get_text() == u"Effectifs (France)":
                company['pro_employes'] = self._get_employees(line[1].get_text())
            if line[0].get_text() == u"Chiffre d'affaires":
                company['pro_ca'] = line[1].get_text()

        company['pro_description'] = self._get_text_with_br(page_profil.find(class_="CompanyActivity__Content").get_text())

        return company

    def parse_experience(self, text):
        if text == u"Plus de 10 ans":
            return 1
        if text == u"Etudiant / Jeune diplomé":
            return 3
        return 2

    def parse_secteur(self, text):
        return [tb.strip() for tb in text.split('/') if len(tb) > 3]

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
            if self.data['pro']['pro_company'].strip() not in self.exclude :
                pro = self.get_or_create_pro(**self.data['pro'])
                self.create_job(pro, job_image=pro.image, job_company=pro.company, job_id=self.job_id, **self.data['job'])
                #print "SUCCES"
        except Exception,e:
            print "FAIL : "
            print str(e)           