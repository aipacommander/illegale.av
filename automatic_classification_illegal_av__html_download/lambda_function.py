import boto3
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import os
from datetime import datetime
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


AWS_S3_BUCKET_NAME = 'automatic.classification.illegal.av'
S3 = boto3.resource('s3')
BUCKET = S3.Bucket(AWS_S3_BUCKET_NAME)


def get_web_resource(url):
    try:
        return urlopen(url)
    except HTTPError as e:
        print(e)
    except URLError as e:
        print('The server could not be found!')

    return None


def main(url):
    resource = get_web_resource(url)
    if resource is None:
        raise Exception('Failed html download.')

    html_resource = resource.read()

    return html_resource


def lambda_handler(event, context):
    urls = json.loads(event['responsePayload']['body'])
    for url_obj in urls:
        html_resource = main(url_obj['SiteUrl'])
        file_name = datetime.now().timestamp()
        file_path = os.path.join('html_downloads', '{}.html'.format(file_name))
        BUCKET.put_object(Key=file_path, Body=html_resource)
        print(url_obj, file_path)

    return {
        'statusCode': 200,
        'body': json.dumps({})
    }