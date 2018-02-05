# SUPER SCRAPER

## technologie stack :

python, tor, aws lambda, aws kinesis, aws s3, aws athena


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

