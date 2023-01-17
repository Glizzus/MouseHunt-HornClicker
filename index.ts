import { Builder, By, until, WebDriver,  } from 'selenium-webdriver'
import firefox from 'selenium-webdriver/firefox'
import { spawn } from 'child_process'
import { writeFile, unlink } from 'fs/promises'

async function sleep(ms: number) {
    await new Promise((res) => setTimeout(res, ms));
}

/**
 * Intializes a headless firefox browser and goes to the MouseHunt login page
 * @returns the created driver
 */
async function init(headless = true) {
    let options = new firefox.Options().headless();
    if (headless) {
        options = options.headless();
    }
    const driver = await new Builder().forBrowser('firefox').setFirefoxOptions(options).build();
    await driver.get('https://www.mousehuntgame.com/login.php');
    return driver;
}

/**
 * Attempts to log in using credentials set in process.env.
 * @param driver The WebDriver to use
 * @returns The provided driver
 */
async function login(driver: WebDriver, username: string, password: string) {
    const findInput = (type: string) => {
        return driver.findElement(By.css(`input.${type}[placeholder='Enter your ${type}']`));
    };
    await Promise.all([
        findInput('username').sendKeys(username),
        findInput('password').sendKeys(password)
    ]);
    await driver.executeScript("app.pages.LoginPage.loginHitGrab();");
    await driver.navigate().refresh();
    await driver.wait(until.urlIs("https://www.mousehuntgame.com/camp.php"), 1000 * 15);
    console.log('User has logged in');
    return driver;
}

/**
 * Finds the src attribute of the captcha image on the DOM.
 * @param driver The WebDriver to use
 * @returns The url of the captcha image
 */
async function findCaptchaImageSource(driver: WebDriver) {
    return driver.findElement(
        By.css("div.mousehuntPage-puzzle-form-captcha-image img")
    ).getAttribute("src");
}

/**
 * Sends the provided keys to the captcha form and submits the solution.
 * @param driver The WebDriver to use
 * @param solution The keys to send
 */
async function enterCaptcha(driver: WebDriver, solution: string) {
    await driver.findElement(
        By.css("input.mousehuntPage-puzzle-form-code")
    ).sendKeys(solution);
    await driver.executeScript(
        "app.views.HeadsUpDisplayView.hud.submitPuzzleForm();"
    )
}

/**
 * Downloads an image. This loads the entire resource into memory.
 * @param imageUrl The url of the image
 * @param path The filepath to download to
 */
async function downloadImage(imageUrl: string, path: string) {
    const response = await fetch(imageUrl);
    const blob = await response.blob();
    const arrayBuffer = await blob.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    await writeFile(path, buffer);
}

/**
 * Employs captcha.py to extract the text from the captcha.
 * @param imagePath The path of the captcha image.
 * @returns A Promise containing either the extracted text, or an error from captcha.py
 */
async function extractTextFromCaptcha(imagePath: string) {
    const python = spawn('python', ['./captcha.py', imagePath]);
    return new Promise<string>((res, rej) => {
        python.stdout.on('data', (data) => res(data.toString()))
        python.stderr.on('data', (data) => rej(data.toString()))
    });
}

/**
 * Brute Forces a captcha if it exists, returns if it doesn't otherwise.
 * This function creates a temporary file in the current directory, but always removes it.
 * @param driver The WebDriver to use
 */
async function handlePotentialCaptcha(driver: WebDriver) {
    const path = "captcha.jpg";
    try {
        while (true) {
            // Mitigate any infinite failures
            await sleep(3000);

            let imageSource: string;
            try {
                imageSource = await findCaptchaImageSource(driver);
            } catch (err) {
                // No captcha; handle the horn
                return; 
            }

            console.log("Captcha found: source", imageSource);
            await downloadImage(imageSource, path);
            const text = await extractTextFromCaptcha(path);
            // Remove any extraneous non alphanumeric characters
            const filteredText = text.replace(/[^0-9a-z]/gi, '');
            console.log("Captcha text:", filteredText);
            await enterCaptcha(driver, filteredText);
            await driver.executeScript("app.views.HeadsUpDisplayView.hud.resumeHunting()");
        }
    } catch (err) {
        console.log("Error solving captcha:", (err as any).toString());
    }
    finally {
        unlink(path)
            .catch(() => {});
    }
}

/**
 * Handles the Horn. This forever runs until the horn exists, and then the horn is clicked.
 * This is handles any potential captchas.
 * @param driver The WebDriver to use
 */
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
            // Mitigate infinite failing loops
            await sleep(1000);
            await handlePotentialCaptcha(driver);            
            console.log("Waiting to sound horn");
            await hornIsReady();
            console.log("Ready to sound horn");
            await driver.executeScript("fetch('https://www.mousehuntgame.com/turn.php')");
            console.log("Horn has been sounded");
            await driver.navigate().refresh()
        } catch (err) {
            console.error(err);
            if (err instanceof Error) {
                // The browser is gone, and we need to initialize again
                if (err.name === "NoSuchSessionError") {
                    return;
                }
            }
        }
    }
}

function getCredentials() {
    let { username, password } = process.env;
    if (!username || !password) {
        [username, password] = process.argv.slice(2);
        if (!username || !password) {
            throw new Error("Username or password not set");
        }
    }
    return [username, password];
}

async function main() {
    const [username, password] = getCredentials();
    while (true) {
        try {
            // Mitigate any infinite failing loops
            await sleep(1000 * 15); 
            const driver = await init();
            await login(driver, username, password);
            await handleHorn(driver);
        } catch (err) {
            console.error(err);
        }
    }
}

main();