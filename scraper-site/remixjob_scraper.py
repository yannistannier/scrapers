#-*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from scraper import Scraper
import re, datetime, locale, urlparse
from sys import exit



class RemixJobScraper(Scraper):

	url = "https://remixjobs.com/?page="

	def parse(self):
		for x in xrange(1,50):
			if self.stop > self.nb_script_max:
				#print "stop script"
				break
			try:
				self.browser.open(str(self.url)+str(x))
				#print "================================"
				#print str(self.url)+str(x)
				#print "================================"
				self.bs = BeautifulSoup(self.browser.response().read(), 'html.parser')
				self.parse_urls()
			except Exception,e:
				break

	def parse_urls(self):
		self.data['url'] = []
		bs_urls = self.bs.find(id='search_results')
		locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
		now = datetime.datetime.now()
		now = now.strftime("%B")[0:5]
		now_n1 = datetime.datetime.now() - datetime.timedelta(days=30)
		now_n1 = now_n1.strftime("%B")[0:5]

		if bs_urls:
			i = 0
			for bs_url in bs_urls.find_all(class_='job-item'):
				url = bs_url.find(class_='job-title').find('a', href=True)
				date_publish = bs_url.find(class_="job-details-right").get_text()

				self.url_job="https://remixjobs.com"+str(url['href'])
				self.job_id = self.url_job.split("/")[-1]
				if self.job_id == "35133":
					continue

				self.list_id.append(self.job_id)

				if self.only_id:
					#print self.job_id
					continue

				if self.nb_api_call > 2000:
					#print "quota api depasse"
					continue

				if self.stop > self.nb_script_max:
					#print "stop script"
					break

				if now not in date_publish.encode("UTF-8") and "heures" not in date_publish and "minutes" not in date_publish and now_n1 not in date_publish.encode("UTF-8"):
					#print "date depasse"
					continue

				
				self.parse_link(self.url_job)
				#print "-------------------------------------------------------------"
				#print "Entreprise : %s" % self.data['pro']['pro_company'].strip()
				#print "Job : %s " % self.data['job']['job_title'].strip()
				#print self.url_job
				self.save()

	def parse_link(self, url):
		self.browser.open(url)
		self.bs = BeautifulSoup(self.browser.response().read(), 'html.parser')
		self.parse_job()
		self.parse_company()

	def parse_job(self):
		job = {}
		infos = self.bs.find(class_='job-infos').find_all('li')

		job['job_title']=self.bs.find(class_='job-title').find('h1').get_text()
		job['job_description']=self.bs.find(class_='job-description').prettify()
		job['job_contrats'] = self._get_contrat(infos[2].get_text().strip()[:-1])
		job['job_location'] = infos[3].get_text().strip()[:-1]
		job['job_study'] = self._get_study(self.parse_study(job['job_description']))
		job['job_activityarea']=self._get_secteur_activite("Web")
		job['job_scraper_site']="remixjob"
		job['job_scraper_url']=self.url_job

		tags = self.bs.find(class_="tags-occupation")
		if tags:
			job['job_tags']=[]
			for tag in tags.find_all('li'):
				t = tag.get_text()
				job['job_tags'].append( t.replace('\n', ' ').replace('\r', '').strip() )

		self.data['job'] = job

	def parse_company(self):
		pro={}

		infos = self.bs.find(class_='job-infos').find_all('li')

		pro['pro_company']=infos[0].get_text().strip()[:-1]

		url = self.bs.find(class_='job-infos').find_all('li')[0].find('a', href=True)['href'].split("/")
		url[-1] = "informations"
		url = "https://remixjobs.com"+"/".join(url)

		page_profil = self.browser.open(url)
		page_profil = BeautifulSoup(self.browser.response().read(), 'html.parser')

		if page_profil.find(class_="company-infos description"):
			pro['pro_description'] = page_profil.find(class_="company-infos description").get_text().strip()

		if page_profil.find(class_="company-infos location"):
			pro['pro_siege'] = page_profil.find(class_="company-infos location").get_text().strip()

		if page_profil.find(class_="info-block") :
			infos = page_profil.find(class_="info-block").find('div')
			if infos:
				website = infos.find('a', href=True)
				pro['pro_website'] = website['href']

		if page_profil.find(class_="keyfigure"):
			for key in page_profil.find(class_="keyfigure").find_all('div'):
				lk=key.find_all('span')
				if "Nombre" in lk[0].get_text():
					pro['pro_employes'] = self._get_employees(lk[1].get_text().strip()) 
				if "Chiffre" in lk[0].get_text():
					pro['pro_ca'] = lk[1].get_text().strip()

		bs_image = page_profil.find(class_='employer-logo-wrap')
		if bs_image:
			bs_image = bs_image.find('img')
			pro['pro_image'] = bs_image['src']
		else:
			img=self.bs.find(class_="company-logo")
			if img:
				pro['pro_image'] = img.find('img')['src']

		self.data['pro'] = pro



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
			pro = self.get_or_create_pro(**self.data['pro'])
			self.create_job(pro, job_image=pro.image, job_company=pro.company, job_web_site=pro.web_site, job_id=self.job_id, **self.data['job'])
			#print "SUCCES"
		except Exception,e:
			print "FAIL : "
			print str(e)     