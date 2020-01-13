from bs4 import BeautifulSoup
import boto3
from botocore.exceptions import ClientError

import os
from datetime import datetime
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


AWS_S3_BUCKET_NAME = 'automatic.classification.illegal.av'
S3 = boto3.resource('s3')
BUCKET = S3.Bucket(AWS_S3_BUCKET_NAME)


def scrap_xvideos(html_obj):
    data = []
    div = html_obj.find('div', {'id': 'content'})
    div = div.find('div', {'class': 'mozaique'})
    for _div in div.contents:
        if isinstance(_div, str):
            continue

        a = _div.find('a')

        # title
        title = _div.find('p', {'class': 'title'}).find('a').get_text()
        title = title.strip()

        # thumnail image
        thumnail = a.find('img')['data-src']

        # duration
        duration = _div.find('span', {'class': 'duration'}).get_text()

        # url
        page_url = a['href']

        # thumnail movie url
        thumnail_splited = thumnail.split('/')
        thumnail_splited[4] = 'videopreview'
        del thumnail_splited[-1]
        # file名に利用
        key_name = thumnail_splited[-1]
        thumnail_splited[-1] = '{}_169.mp4'.format(key_name)
        thumnail_movie_url = '/'.join(thumnail_splited)

        data.append({
            'AvTitle': title,
            'ThumnailUrl': thumnail,
            'duration': duration,
            'Url': page_url,
            'ThumnailMovieUrl': thumnail_movie_url,
            'KeyName': key_name
        })

    return data


def scrap_pornhub(html_obj):
    data = []
    ul = html_obj.find('ul', {'id': 'videoCategory'})
    li_list = ul.find_all('li', {'class': 'videoblock'})
    for li in li_list:
        a = li.find('div', {'class': 'videoPreviewBg'}).find('a')

        # title
        title = li.find('span', {'class': 'title'}).get_text()
        title = title.strip()

        # thumnail image
        thumnail = a.find('img')['data-thumb_url']

        # duration
        duration = li.find('var', {'class': 'duration'}).get_text()

        # url
        page_url  = a['href']

        # thumnail movie url
        thumnail_movie_url = ''

        # file名に利用.
        key_name = ''

        data.append({
            'AvTitle': title,
            'ThumnailUrl': thumnail,
            'duration': duration,
            'Url': page_url,
            'ThumnailMovieUrl': thumnail_movie_url,
            'KeyName': key_name
        })
    
    return data


def scrap(html_resource):
    html_obj = BeautifulSoup(html_resource, 'html.parser')
    _text = html_obj.find('title').get_text().lower()
    print(_text)
    data = []
    if _text.find('pornhub') > -1:
        data = scrap_pornhub(html_obj)
    elif _text.find('xvideos') > -1:
        data = scrap_xvideos(html_obj)
    else:
        raise Exception('Not found site type.')
    
    return data
        

def main(html_resource):
    return scrap(html_resource)


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
    logger.info("scraping sample lambda started.")
    object_name = event['Records'][0]['s3']['object']['key']
    html_resource = get_object(object_name).decode('utf8')
    
    data = main(html_resource)
    for d in data:
        file_name = '{}'.format(d['KeyName'])
        del d['KeyName']
        file_path = os.path.join('scrap_data', '{}.json'.format(file_name))
        BUCKET.put_object(Key=file_path, Body=json.dumps(d))

    return {
        'statusCode': 200,
        'body': json.dumps({})
    }