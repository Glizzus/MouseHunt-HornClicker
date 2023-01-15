import { Builder, By, until, WebDriver,  } from 'selenium-webdriver'
import firefox from 'selenium-webdriver/firefox'


async function init() {
    const options = new firefox.Options().headless();
    const driver = await new Builder().forBrowser('firefox').setFirefoxOptions(options).build();
    await driver.get('https://www.mousehuntgame.com/login.php');
    return driver;
}

async function login(driver: WebDriver) {
    const { username, password } = process.env;
    if (!username || !password) {
        throw new Error("Username or password not set");
    }

    const findInput = (type: string) => {
        return driver.findElement(By.css(`input.${type}[placeholder='Enter your ${type}']`));
    };
    await Promise.all([
        findInput('username').sendKeys(username),
        findInput('password').sendKeys(password)
    ]);
    await driver.executeScript("app.pages.LoginPage.loginHitGrab();");
    
    await driver.wait(until.urlIs("https://www.mousehuntgame.com/camp.php"));
    console.log('User has logged in');
    return driver;
}

async function handleHorn(driver: WebDriver) {

    const minutes = (num: number) => num * 1000 * 60;
    const hornIsReady = () => {
        const minutesToWait = 16;
        const readyElement = driver.findElement(
            By.className("huntersHornView__timerState--type-ready")
        );
        const condition = until.elementIsVisible(readyElement);
        const timeoutMessage = `Horn has not been sounded after ${minutesToWait} minutes`;
        return driver.wait(condition, minutes(minutesToWait), timeoutMessage, minutes(1));
    }

    while (true) {

        try {
            console.log("Waiting to sound horn");
            await hornIsReady();
            console.log("Ready to sound horn");
            await driver.executeScript("fetch('https://www.mousehuntgame.com/turn.php')");
            console.log("Horn has been sounded");
            await driver.navigate().refresh()
            await new Promise((res) => setTimeout(res, 1000));
        } catch (err) {
            console.error(err);
            if (err instanceof Error) {
                if (err.name === "NoSuchSessionError") {
                    return;
                }
            }
        }
    }
}

init()
    .then(login)
    .then(handleHorn);