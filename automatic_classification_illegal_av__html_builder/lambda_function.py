from jinja2 import Template
import boto3
from botocore.exceptions import ClientError

import os
import logging

logger = logging.getLogger()
S3 = boto3.resource('s3')
TEMPLATE_AWS_S3_BUCKET_NAME = 'automatic.classification.illegal.av'
WEB_AWS_S3_BUCKET_NAME = 'automatic.classification.illegal.av.static'
TEMPLATE_BUCKET = S3.Bucket(TEMPLATE_AWS_S3_BUCKET_NAME)
WEB_BUCKET = S3.Bucket(WEB_AWS_S3_BUCKET_NAME)
DB = boto3.resource('dynamodb')


def get_object(bucket, object_name):
    """Retrieve an object from an Amazon S3 bucket

    :param bucket_name: string
    :param object_name: string
    :return: botocore.response.StreamingBody object. If error, return None.
    """
    try:
        response = bucket.Object(object_name).get()
    except ClientError as e:
        # AllAccessDisabled error == bucket or object not found
        logging.error(e)
        return None
    # Return an open StreamingBody object
    return response['Body'].read()



def main():
    index_html = get_object(TEMPLATE_BUCKET,
                            os.path.join('static_templates', 'index.html')) \
                            .decode('utf8')
    box_html = get_object(TEMPLATE_BUCKET,
                          os.path.join('static_templates', 'box.html')) \
                          .decode('utf8')

    table_name = 'IllegalAv'
    table = DB.Table(table_name)
    res = table.scan(Limit=10)

    index_t = Template(index_html)
    insert_boxes = []
    for r in res['Items']:
        box_t = Template(box_html)
        insert_boxes.append(box_t.render(
            title=r['AvTitle'],
            duration=r['duration'],
            url=r['Url']
        ))

    output_html = index_t.render(boxes=''.join(insert_boxes))
    return output_html


def lambda_handler(event, context):
    output_html = main()

    # write
    file_path = 'index.html'
    WEB_BUCKET.put_object(Key=file_path, Body=output_html)
    
    return None