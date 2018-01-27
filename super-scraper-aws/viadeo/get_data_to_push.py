import base64
import json
import boto3
import copy
from elasticsearch import Elasticsearch, RequestsHttpConnection


def lambda_handler(event, context):
    firehose = boto3.client('firehose', region_name='us-west-2')
    es = Elasticsearch(
        ["https://xxxxxxxx.us-west-2.es.amazonaws.com/"],
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
    for record in event['Records']:
        payload = base64.b64decode(record["kinesis"]["data"])
        datas = json.loads(payload)

        if len(datas['jobs']) > 2 and len(datas['skills']) > 4:
            jobskill = []
            jobs = []
            educations = []
            datas_to_es = copy.deepcopy(datas)

            url = datas['user']['url']
            md5 = datas['user']['md5']
            lang = datas['user']['lang']

            print "{} / {}".format(str(md5), str(url))

            profile = { 'Data' : json.dumps(datas['user'])+"\n" } 

            for job in datas['jobs'] : 
                for skill in datas['skills']:
                    line = { 'Data' : "{},{},{},{}\n".format(md5, job['title'].replace(",", " ").strip(), skill.replace(",", " ").strip(), lang) }
                    jobskill.append(line)

            for job in datas['jobs']:
                obj_to_push = job
                obj_to_push['md5'] = md5
                obj_to_push['lang'] = lang
                jobs.append( { 'Data' : json.dumps(obj_to_push)+"\n" }   )


            for education in datas['educations'] : 
                educ_to_push = education 
                educ_to_push['md5'] = md5
                educ_to_push['lang'] = lang
                educations.append( { 'Data' : json.dumps(educ_to_push)+"\n" }   )

            if len(jobskill) <= 500: 
                res = firehose.put_record_batch(DeliveryStreamName="jobskill-to-s3", Records=jobskill)
            
            if len(jobskill) > 500 and len(jobskill) <= 500:
                res = firehose.put_record_batch(DeliveryStreamName="jobskill-to-s3", Records=jobskill[:500])
                res = firehose.put_record_batch(DeliveryStreamName="jobskill-to-s3", Records=jobskill[500:])
            
            res = firehose.put_record_batch(DeliveryStreamName="jobs-to-s3", Records=jobs)
            
            if educations:
                res = firehose.put_record_batch(DeliveryStreamName="educations-to-s3", Records=educations)
            res = firehose.put_record(DeliveryStreamName="profils-to-s3", Record=profile)

            es.index(index="datas", doc_type="cv", id=md5, body=datas_to_es)

