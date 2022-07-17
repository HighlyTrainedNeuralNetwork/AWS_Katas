import boto3
import csv
import os
from dotenv import load_dotenv

load_dotenv()

with open('S3-connector-credentials.csv', 'r') as f:
    csv_credentials = next(csv.DictReader(f))
s3 = boto3.resource(service_name='s3',
                    aws_access_key_id=csv_credentials['Access key ID'],
                    aws_secret_access_key=csv_credentials['Secret access key'])
bucket = s3.Bucket(os.getenv("S3_BUCKET_NAME"))

test_string = 'Hello World'
bucket.put_object(Key='test.txt', Body=test_string)
for obj in bucket.objects.all():
    print(obj.get()['Body'].read().decode('utf-8'))