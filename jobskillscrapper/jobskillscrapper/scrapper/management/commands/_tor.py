'''
Python script to connect to Tor via Stem and Privoxy, requesting a new connection (hence a new IP as well) as desired.
'''
import urllib2
import json

from stem import Signal
from stem.control import Controller


class tor_request(object):

    proxy_handler = urllib2.ProxyHandler({'http': '127.0.0.1:8118'})
    proxy_auth_handler = None
    opener = None 
    response_header = None
    cookie = "referer=https%3A%2F%2Fduckduckgo.com; webapp.sid=s%3Apfr3a098sXhHueu31XC5vitavZ_FV1Rf.sTfydITcR19UX7y97kmXglli0qDCjBJjyEHSePeuMg8; __utma=1.684385913.1486576848.1486576848.1486576848.1; __utmb=1.4.10.1486576848; __utmc=1; __utmz=1.1486576848.1.1.utmcsr=duckduckgo.com|utmccn=(referral)|utmcmd=referral|utmcct=/; _sp_viad_ses.e48a=*; _sp_viad_id.e48a=0673e237d1dba769.1486576849.1.1486577832.1486576849.0b14aa2c-42c2-482c-a579-ef185d2e24eb; stayConnected=008wqllvh1traq1; rememberMe=0031aalr6dvuqj1h; __utmt=1"
    header = {
        "cookie" : "referer=https%3A%2F%2Fduckduckgo.com; webapp.sid=s%3Apfr3a098sXhHueu31XC5vitavZ_FV1Rf.sTfydITcR19UX7y97kmXglli0qDCjBJjyEHSePeuMg8; __utma=1.684385913.1486576848.1486576848.1486576848.1; __utmb=1.4.10.1486576848; __utmc=1; __utmz=1.1486576848.1.1.utmcsr=duckduckgo.com|utmccn=(referral)|utmcmd=referral|utmcct=/; _sp_viad_ses.e48a=*; _sp_viad_id.e48a=0673e237d1dba769.1486576849.1.1486577832.1486576849.0b14aa2c-42c2-482c-a579-ef185d2e24eb; stayConnected=008wqllvh1traq1; rememberMe=0031aalr6dvuqj1h; __utmt=1",
        "Host" : "www.viadeo.com"
    }

    def __init__(self):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password='xxxxxx')
            controller.signal(Signal.NEWNYM)
            controller.close()

    
        self.opener = urllib2.build_opener(self.proxy_handler)
        #self.opener.addheaders = [('Cookie',self.cookie)]


    def connexion(self):
        self.proxy_auth_handler = urllib2.ProxyBasicAuthHandler()
        self.proxy_auth_handler.add_password('realm', 'https://secure.viadeo.com/fr/signin', 'xxxxx@hotmail.fr', 'xxxxx')    



    def get(self, url):
        res = self.opener.open(url)
        #self.response_header = res.info().getheader("cookie")
        
        return res.read()


# request a URL
def request(url, header=None, data=None):
    renew_connection()

    header = {
        "cookie" : "referer=https%3A%2F%2Fduckduckgo.com; webapp.sid=s%3Apfr3a098sXhHueu31XC5vitavZ_FV1Rf.sTfydITcR19UX7y97kmXglli0qDCjBJjyEHSePeuMg8; __utma=1.684385913.1486576848.1486576848.1486576848.1; __utmb=1.4.10.1486576848; __utmc=1; __utmz=1.1486576848.1.1.utmcsr=duckduckgo.com|utmccn=(referral)|utmcmd=referral|utmcct=/; _sp_viad_ses.e48a=*; _sp_viad_id.e48a=0673e237d1dba769.1486576849.1.1486577832.1486576849.0b14aa2c-42c2-482c-a579-ef185d2e24eb; stayConnected=008wqllvh1traq1; rememberMe=0031aalr6dvuqj1h; __utmt=1",
        "Host" : "www.viadeo.com"
    }

    # communicate with TOR via a local proxy (privoxy)
    def _set_urlproxy():
        proxy_support = urllib2.ProxyHandler({'http': '127.0.0.1:8118'})
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)

    # request a URL
    # via the proxy
    _set_urlproxy()
    request = urllib2.Request(url=url)
    request.add_header(header)

    return urllib2.urlopen(request).read()


# signal TOR for a new connection
def renew_connection():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='xxxxxx')
        controller.signal(Signal.NEWNYM)
        controller.close()
