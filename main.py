
from typing import IO, Tuple
from re import sub
from time import sleep
from traceback import print_exc
from subprocess import run
from getpass import getpass
from requests import get

import cv2
import pytesseract

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def mousehunt_url(endpoint: str) -> str:
    return f"https://www.mousehuntgame.com/{endpoint}"


def get_driver(headless: bool = True) -> WebDriver:
    options = Options()
    options.headless = headless
    driver = webdriver.Firefox(options=options)
    return driver


def go_to_login(driver: WebDriver) -> None:
    driver.get(mousehunt_url('login.php'))


def login(driver: WebDriver, username: str, password: str) -> None:

    def find_field(field: str):
        selector = f"input.{field}[placeholder='Enter your {field}']"
        return driver.find_element(By.CSS_SELECTOR, selector)

    find_field('username').send_keys(username)
    find_field('password').send_keys(password)
    sleep(1)
    login_script = "app.pages.LoginPage.loginHitGrab();"
    driver.execute_script(login_script)
    driver.refresh()
    print(f'User {username} has logged in')


def try_get_captcha_source(driver: WebDriver) -> str | None:
    captcha_css = "div.mousehuntPage-puzzle-form-captcha-image img"
    try:
        captcha_element = driver.find_element(By.CSS_SELECTOR, captcha_css)
        return captcha_element.get_attribute("src")
    except Exception:
        return None


def enter_captcha(driver: WebDriver, solution: str) -> None:
    input_selector = "input.mousehuntPage-puzzle-form-code"
    input_element = driver.find_element(By.CSS_SELECTOR, input_selector)
    input_element.send_keys(solution)
    submit_script = "app.views.HeadsUpDisplayView.hud.submitPuzzleForm();"
    driver.execute_script(submit_script)


def download_to_temp_file(url: str) -> IO[bytes]:
    img = get(url).content
    with open('captcha.png', 'wb') as file:
        file.write(img)
    return file.name


# This code is best treated as a black box
# https://stackoverflow.com/questions/65930463/how-to-process-this-captcha-image-for-pytesseract

def extract_text(img_path: str) -> str:
    img = cv2.imread(img_path)
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    (height, width) = grey.shape[:2]
    grey = cv2.resize(grey, (width * 2, height * 2))
    close = cv2.morphologyEx(grey, cv2.MORPH_CLOSE, None)
    thresh_type = cv2.THRESH_BINARY | cv2.THRESH_OTSU
    threshold = cv2.threshold(close, 0, 255, thresh_type)[1]
    text = pytesseract.image_to_string(threshold)
    return text.split()[0]


def handle_potential_captcha(driver: WebDriver) -> None:
    captcha_found = False
    try:
        while True:
            sleep(5)
            captcha_source = try_get_captcha_source(driver)
            if captcha_source is not None:
                captcha_found = True
            else:
                break
            print("Captcha found")
            image_file = download_to_temp_file(captcha_source)
            attempt = extract_text(image_file)
            cleaned_attempt = sub('/[^0-9a-z]/gi', '', attempt)
            print(f"Captcha attempt: {cleaned_attempt}")
            enter_captcha(driver, cleaned_attempt)
            resume_script = "app.views.HeadsUpDisplayView.hud.resumeHunting()"
            driver.execute_script(resume_script)
    except Exception:
        print_exc()
    finally:
        return captcha_found


def wait_until_horn_ready(driver: WebDriver) -> None:
    minutes_to_wait = 60 * 16
    poll_frequency = 30
    ready_element_class = "huntersHornView__timerState--type-ready"
    visibility_args = (By.CLASS_NAME, ready_element_class)
    horn_ready = EC.visibility_of_element_located(visibility_args)
    WebDriverWait(driver, minutes_to_wait, poll_frequency).until(horn_ready)


def sound_horn(driver: WebDriver) -> None:
    sound_script = f"fetch('{mousehunt_url('turn.php')}')"
    driver.execute_script(sound_script)


def handle_horn(driver: WebDriver) -> None:
    while True:
        try:
            sleep(5)
            print()
            print("Checking for captcha")
            was_captcha = handle_potential_captcha(driver)
            if not was_captcha:
                print("No captcha found")
            print("Waiting for horn")
            wait_until_horn_ready(driver)
            print("Sounding Horn")
            sound_horn(driver)
            driver.refresh()
        except Exception:
            print_exc()


def get_credentials() -> Tuple[str, str]:
    from os import environ
    from sys import argv

    username = environ.get('MOUSEHUNT_USERNAME')
    if not username:
        username = input('Enter your mousehunt username: ')

    password = environ.get('MOUSEHUNT_PASSWORD')
    if not password:
        password = getpass('Enter your mousehunt password: ')

    return username, password


def main() -> None:
    username, password = get_credentials()
    while True:
        sleep(5)
        try:
            print("trying")
            driver = get_driver()
            go_to_login(driver)
            login(driver, username, password)
            handle_horn(driver)
        except Exception:
            print_exc()
            driver.close()


main()
