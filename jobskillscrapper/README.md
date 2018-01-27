# Job & Skill scrapper

## Installation all package
```
sudo apt-get update 
sudo apt-get install libpq-dev python-dev python
sudo apt-get install build-essential 
sudo apt-get install virtualenv
```


## Installation & configuration Tor / proxy / stem

### installation tor
```
sudo apt-get install tor
/etc/init.d/tor restart
```

Create password 
```
tor --hash-password mypassword
```

So, update the torrc with the port and the hashed password.

/etc/tor/torrc
```
ControlPort 9051
# hashed password below is obtained via `tor --hash-password my_password`
HashedControlPassword 16:E600ADC1B52C80BB6022A0E999A7734571A451EB6AE50FED489B72E3DF
CookieAuthentication 1
```

### installation python-stem

```
sudo apt-get install python-stem
```

### installation Privoxy

```
sudo apt-get install privoxy
```

Now, tell privoxy to use TOR by routing all traffic through the SOCKS servers at localhost port 9050.

/etc/privoxy/config
```
forward-socks5 / localhost:9050 .
```
retart privoxy

```
sudo /etc/init.d/privoxy restart
```

## Installation projet

### Clone `jobskillscrapper` project

```
cd <path/to/clone/project>
git clone git@github.com:pitchmyjob/jobskillscrapper.git
```

### Install Python 3

```
sudo apt-get install python3 # Ubuntu / Debian
brew install python3 # OS X
```

### Install virtualenvwrapper

```
pip3 install virtualenvwrapper
```

Edit your `.profile` :

```
nano ~/.profile
```

Paste the content bellow :

```
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3.6 # Change the path to match your installation
export VIRTUALENVWRAPPER_VIRTUALENV=/usr/local/bin/virtualenv # Change the path to match your installation
source /usr/local/bin/virtualenvwrapper.sh # Change the path to match your installation
```

Execute profile

```
source ~/.profile
```

## Create `jobskillscrapper` virtualenv

```
mkvirtualenv jobskillscrapper -p python3 --no-site-packages
```

### Install all dependencies

```
cd <path_to_your_project>
pip install -r requirements.txt
python manage.py migrate
```

### Scrap profile

```
python manage.py scrap --service (viadeo|linkedin) <http://profile_link_entry_point> --settings=settings

# Examples :
python manage.py scrap --service linkedin https://fr.linkedin.com/in/yannis-tannier-7017a169
python manage.py scrap --service viadeo http://fr.viadeo.com/fr/profile/yannis.tannier
```

