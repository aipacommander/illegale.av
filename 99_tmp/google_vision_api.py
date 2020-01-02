import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import base64
from config import config
import json
import copy
import io
import time
import cv2
import argparse


FONT_PATH = '/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc'

def request_api(img):
    content = base64.b64encode(img).decode('utf8')
    url = '%s?key=%s' % (config['api']['url'], config['api']['key'])
    res = json.dumps({
        'requests': [{
            'image': {
                'content': content
            },
            'features': [{
                'type': 'TEXT_DETECTION',
                'maxResults': 200
            }]
        }]
    })
    res = requests.post(url, res)
    return res.json()


def response_parser(res):
    if 'error' in res['responses'][0]:
        print(res)
        assert False

    text_annotations = res['responses'][0]['textAnnotations']

    detect_list = []
    for text in text_annotations:
        if 'locale' in text: continue
        detect_list.append([text['description'], text['boundingPoly']['vertices']])

        print(text['description'], text['boundingPoly']['vertices'])

    return detect_list


def draw(img, detect_list):
    c_img = copy.deepcopy(img)
    draw_img = ImageDraw.Draw(c_img)
    r = 0.5
    for detect in detect_list:
        lt = detect[1][0]
        rb = detect[1][2]
        x_conditions = 'x' in lt and 'x' in rb
        y_conditions = 'y' in rb and 'y' in rb
        if not(x_conditions and y_conditions): continue

        start_point = lt['x'], lt['y']
        end_point = rb['x'], rb['y']
        draw_img.rectangle((start_point, end_point), outline=(150, 0, 0), fill=(150, 0, 0))

        # テキスト描画
        text_size = abs(end_point[1] - start_point[1]) * r
        font = ImageFont.truetype(FONT_PATH, int(text_size))
        draw_img.text((start_point[0] + 5, start_point[1] + 5), detect[0], font=font, fill=(0, 0, 0))

    c_img.save('./assets/%s.jpg' % (time.time()))
    c_img.show()


def preprocessing(img):
    img_np = np.asarray(img)
    gray_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    
    kernel = np.ones([5, 5], np.uint8)
    dilate = cv2.dilate(gray_img, kernel, iterations=1)

    sub = 255 - (dilate - gray_img)

    return {'gray': gray_img, 'dilate': dilate, 'sub': sub}


def image_preprocessing(img):
    """ RGBでなければ変換する. """
    pil_img = Image.open(io.BytesIO(img))
    size = pil_img.size
    r = 0.4
    resize = (int(size[0] * r), int(size[1] * r))
    pil_img = pil_img.resize(resize)
    if pil_img.mode == 'RGB':
        return pil_img
    else:
        return pil_img.convert('RGB')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--img_path', type=str, required=True)
    args = parser.parse_args()
    img_path = args.img_path

    img = None
    with open(img_path, 'rb') as f:
        img = image_preprocessing(f.read())

    img_dict = preprocessing(img)
    buffer = io.BytesIO()
    Image.fromarray(img_dict['gray']).save(buffer, 'jpeg')
    request_img = buffer.getvalue()

    res = request_api(request_img)
    detect_list = response_parser(res)
    print(detect_list)


if __name__ == '__main__':
    main()