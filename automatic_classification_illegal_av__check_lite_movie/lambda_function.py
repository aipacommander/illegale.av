import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import os
import cv2
import numpy as np
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)
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


def download_file(object_name):
    try:
        root_path = os.path.join(os.path.sep, 'tmp')
        _object_name = object_name.split('/')[-1]
        save_path = os.path.join(root_path, _object_name)
        print(object_name, save_path)
        BUCKET.download_file(object_name, save_path)
    except ClientError as e:
        # AllAccessDisabled error == bucket or object not found
        logging.error(e)
        return None

    # Return an open StreamingBody object
    return save_path


def preprocessing(file_path):
    cap = cv2.VideoCapture(file_path)
    frames = []
    before_gray= None
    while(1):
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if before_gray is None:
            before_gray = gray
            continue

        diff_img = cv2.absdiff(gray, before_gray)
        gray2 = gray.copy()
        gray2[diff_img.astype(bool)] = 0
        frames.append(gray2)
        before_gray = gray

    _frame = np.mean(frames, axis=0).astype(np.uint8)
    _, th_img = cv2.threshold(_frame.copy(), 125, 255, cv2.THRESH_BINARY)
    
    kernel = np.ones([5, 5], np.uint8)
    dilate_img = cv2.dilate(th_img, kernel, iterations=2)
    
    return _frame, dilate_img


def exists_title(img_obj):
    contours, _ = cv2.findContours(img_obj.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # titleっぽい特徴のサイズでいずれ取らないといけないかも.
    filtered_contours = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w < 20:
            continue

        filtered_contours.append(c)

    return int(len(filtered_contours) > 0)
    
    
def lambda_handler(event, context):
    # object_name = event['Records'][0]['s3']['object']['key']
    object_name = 'thumnail_movie_downloads/cd82c6c699a54265711f4d3991e76b61_1578671417.773293.mp4'
    download_file_path = download_file(object_name)

    # opencvで前処理
    _, img_obj = preprocessing(download_file_path)
    title_flag = exists_title(img_obj)

    # download json file for s3
    key_name = download_file_path.split('/')[2].split('_')[0]
    data_file_path = os.path.join('scrap_data', '{}.json'.format(key_name))
    print(data_file_path)
    _json_str = get_object(data_file_path)
    scrap_data = json.loads(_json_str)
    scrap_data['title_flag'] = title_flag

    # s3 upload
    file_name = datetime.now().timestamp()
    file_path = os.path.join('added_title_flag_json', '{}.json'.format(file_name))
    BUCKET.put_object(Key=file_path, Body=json.dumps(scrap_data))

    return {
        'statusCode': 200,
        'body': json.dumps({})
    }