import boto3
from _tor import tor_request
from viadeo.parse_html import ViadeoScrapper
import hashlib
import json
import requests
import time


def get_number_message():
    client = boto3.client('sqs', region_name='us-west-2')
    res = client.get_queue_attributes(QueueUrl='https://sqs.us-west-2.amazonaws.com/xxxxx/url-to-parse', AttributeNames=['ApproximateNumberOfMessages'])
    return res['Attributes']['ApproximateNumberOfMessages']


sqs = boto3.resource('sqs', region_name='us-west-2')
queue = sqs.get_queue_by_name(QueueName='url-to-parse')
kinesis = boto3.client('kinesis', region_name='us-west-2')

re = tor_request()


print re.get("http://ipinfo.io/ip")

for message in queue.receive_messages(MaxNumberOfMessages=10):
    start = time.time()
    url = message.body  
    html = re.get(url)
    key = hashlib.md5(url).hexdigest()
    print url
    message.delete()
    ViadeoScrapper(html, url)


