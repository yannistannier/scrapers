import boto3
from _tor import tor_request
import hashlib
import json
import time


def get_number_message():
    client = boto3.client('sqs', region_name='us-west-2')
    res = client.get_queue_attributes(QueueUrl='https://sqs.us-west-2.amazonaws.com/xxxxx/url-to-parse', AttributeNames=['ApproximateNumberOfMessages'])
    return res['Attributes']['ApproximateNumberOfMessages']


sqs = boto3.resource('sqs', region_name='us-west-2')
queue = sqs.get_queue_by_name(QueueName='url-to-parse')
kinesis = boto3.client('kinesis', region_name='us-west-2')

re = tor_request()


while get_number_message() > 1 :
    #print re.get("http://ipinfo.io/ip")

    for message in queue.receive_messages(MaxNumberOfMessages=10):
        url = message.body
        print url

        try:
            html = re.get(url)
            key = hashlib.md5(url).hexdigest()

            datas = {
                "url" : url,
                "html" : html
            }
            kinesis.put_record(StreamName="receive-html", Data=json.dumps(datas), PartitionKey=str(key))

            message.delete()
            print("Sucess")
        except Exception as e:
            print("> error : {}".format(str(e)))
            time.sleep(5)
