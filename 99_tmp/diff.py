import cv2
import time
import numpy as np


if __name__ == '__main__':
    file_name = 'e77ed39ba5b52081585fbc4c06b7b99b_169.mp4'
    cap = cv2.VideoCapture(file_name)
    frames = []
    c = 0 
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
        bg_diff_path = './diff__{:0>5}.jpg'.format(c)
        cv2.imwrite(bg_diff_path, gray2)
        c += 1
        before_gray = gray

    _frame = np.mean(frames, axis=0).astype(np.uint8)
    _, th_img = cv2.threshold(_frame.copy(), 125, 255, cv2.THRESH_BINARY)
    print(_frame.shape)
    bg_diff_path = './diff.jpg'
    
    #「差分」画像の保存
    cv2.imwrite(bg_diff_path, th_img)