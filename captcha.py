import cv2
import pytesseract
from sys import stdout, argv

# This code is best treated as a black box
# https://stackoverflow.com/questions/65930463/how-to-process-this-captcha-image-for-pytesseract


def extract_text(img_path):
    img = cv2.imread(img_path)
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    (height, width) = grey.shape[:2]
    grey = cv2.resize(grey, (width * 2, height * 2))
    close = cv2.morphologyEx(grey, cv2.MORPH_CLOSE, None)
    thresh_type = cv2.THRESH_BINARY | cv2.THRESH_OTSU
    threshold = cv2.threshold(close, 0, 255, thresh_type)[1]
    text = pytesseract.image_to_string(threshold)
    return text.split()[0]


img_path = argv[1]
text = extract_text(img_path)
stdout.write(text)
stdout.flush()
