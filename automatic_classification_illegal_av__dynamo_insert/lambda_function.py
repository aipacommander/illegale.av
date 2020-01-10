import json
import boto3
from datetime import datetime
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
    table_name = 'IllegalAv'
    table = DB.Table(table_name)

    object_name = event['Records'][0]['s3']['object']['key']
    _json_str = get_object(object_name)
    insert_data = json.loads(_json_str)
    
    _date = int(datetime.now().strftime('%Y%m%d'))
    
    for d in insert_data:
        d['Date'] = _date
        table.put_item(Item=d)

    return {
        'statusCode': 200,
        'body': json.dumps({})
    }
