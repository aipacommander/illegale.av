import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import ssl
import urllib.request
import os
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)
DB = boto3.resource('dynamodb')
S3 = boto3.resource('s3')
AWS_S3_BUCKET_NAME = 'automatic.classification.illegal.av'
BUCKET = S3.Bucket(AWS_S3_BUCKET_NAME)


def get_object(object_name):
    """Retrieve an object from an Amazon S3 bucket

    :param bucket_name: string
    :param object_name: string
    :return: botocore.response.StreamingBody object. If error, return None.
    """
    try:
        response = BUCKET.Object(object_name).get()
    except ClientError as e:
        # AllAccessDisabled error == bucket or object not found
        logging.error(e)
        return None
    # Return an open StreamingBody object
    return response['Body'].read()
    
    
def lambda_handler(event, context):
    object_name = event['Records'][0]['s3']['object']['key']
    _json_str = get_object(object_name)
    insert_data = json.loads(_json_str)

    ssl._create_default_https_context = ssl._create_unverified_context
    url = 'https://img-l3.xvideos-cdn.com/videos/videopreview/cd/82/c6/cd82c6c699a54265711f4d3991e76b61_169.mp4'
    key_name = url.split('/')[-1].replace('_169.mp4', '')
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as res:
            body = res.read()

        t = datetime.now().timestamp()
        file_name = '{}_{}.mp4'.format(key_name, t)
        file_path = os.path.join('thumnail_movie_downloads', file_name)
        BUCKET.put_object(Key=file_path, Body=body)
    except Exception as e:
        print(e)

    return {
        'statusCode': 200,
        'body': json.dumps({})
    }
