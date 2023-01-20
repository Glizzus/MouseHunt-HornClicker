from re import sub
import cv2
import pytesseract
from requests import get
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By


def beat(driver: WebDriver, src: str) -> None:
    """
    Beats the captcha.

    driver -- the WebDriver to use
    src -- the url of the captcha image
    """

    file_name = 'captcha.png'

    def download_to_temp_file():
        img = get(src).content
        with open(file_name, 'wb') as file:
            file.write(img)

    def extract_text() -> str:
        img = cv2.imread(file_name)
        grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        (height, width) = grey.shape[:2]
        grey = cv2.resize(grey, (width * 2, height * 2))
        close = cv2.morphologyEx(grey, cv2.MORPH_CLOSE, None)
        thresh_type = cv2.THRESH_BINARY | cv2.THRESH_OTSU
        threshold = cv2.threshold(close, 0, 255, thresh_type)[1]
        text = pytesseract.image_to_string(threshold)
        return text.split()[0]

    def enter_captcha(solution: str):
        input_selector = "input.mousehuntPage-puzzle-form-code"
        input_element = driver.find_element(By.CSS_SELECTOR, input_selector)
        input_element.send_keys(solution)
        submit_script = "app.views.HeadsUpDisplayView.hud.submitPuzzleForm();"
        driver.execute_script(submit_script)

    download_to_temp_file()
    text = extract_text()
    cleaned_text = sub('/[^0-9a-z]/gi', '', text)
    print(f'Captcha attempt: {cleaned_text}')
    enter_captcha(text)
    resume_script = "app.views.HeadsUpDisplayView.hud.resumeHunting()"
    driver.execute_script(resume_script)
