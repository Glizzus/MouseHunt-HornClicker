from typing import Tuple
from time import sleep
from traceback import print_exc
from getpass import getpass
from os import environ
import logging
from sys import stdout

import captchabeater
import evader

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
    logging.info("Login script attempted")
    driver.refresh()
    logging.info(f'User {username} has logged in')


def try_get_captcha_source(driver: WebDriver) -> str | None:
    captcha_css = "div.mousehuntPage-puzzle-form-captcha-image img"
    try:
        captcha_element = driver.find_element(By.CSS_SELECTOR, captcha_css)
        return captcha_element.get_attribute("src")
    except Exception:
        return None


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
            logging.info("Captcha found")
            captchabeater.beat(driver, captcha_source)
    except Exception:
        print_exc()
    finally:
        return captcha_found


def wait_until_horn_ready(driver: WebDriver) -> None:
    ready_element_class = "huntersHornView__timerState--type-ready"
    visibility_args = (By.CLASS_NAME, ready_element_class)
    horn_ready = EC.visibility_of_element_located(visibility_args)
    args = {
        'driver': driver,
        'timeout': 60 * 16,
        'poll_frequency': 30
    }
    WebDriverWait(**args).until(horn_ready)


def sound_horn(driver: WebDriver) -> None:
    sound_script = f"fetch('{mousehunt_url('turn.php')}')"
    driver.execute_script(sound_script)


def handle_horn(driver: WebDriver) -> None:
    while True:
        try:
            sleep(5)
            print()
            logging.info("Checking for captcha")
            was_captcha = handle_potential_captcha(driver)
            if not was_captcha:
                logging.info("No captcha found")
            logging.info("Waiting for horn")
            wait_until_horn_ready(driver)
            logging.info("Sounding Horn")
            sound_horn(driver)
            logging.info("Waiting...")
            evader.safety_wait()
        except Exception as exc:
            print_exc()
            raise exc


def get_credentials() -> Tuple[str, str]:

    username = environ.get('MOUSEHUNT_USERNAME')
    if not username:
        username = input('Enter your mousehunt username: ')

    password = environ.get('MOUSEHUNT_PASSWORD')
    if not password:
        password = getpass('Enter your mousehunt password: ')

    return username, password


def run(username, password):
    sleep(5)
    try:
        driver = get_driver()
        logging.info("Driver created")
        go_to_login(driver)
        logging.info("Attempting to log in")
        login(driver, username, password)
        handle_horn(driver)
    except Exception as exp:
        print_exc()
        driver.close()
        raise exp


def main() -> None:
    log_options = {
        'stream': stdout,
        'encoding': 'utf-8',
        'level': logging.INFO
    }
    logging.basicConfig(**log_options)
    logging.info("Starting...")
    username, password = get_credentials()
    logging.info(f"Credentials received for user {username}")

    def run_with_args():
        run(username, password)

    evader.until_successive_failures(run_with_args, 5)


if __name__ == '__main__':
    main()
