## 10fastfingers Typing Bot (Turkish)

This repository contains two automated typing bot implementations for the Turkish typing test on https://10fastfingers.com/typing-test/turkish.

The bots are designed to type continuously for 60 seconds at maximum speed and capture a screenshot of the final test results. Two different browser automation frameworks are used: Playwright and Selenium.

---

## Repository Structure

playwright_bot.py   High-speed typing bot implemented with Playwright  
selenium_bot.py     High-speed typing bot implemented with Selenium (headless Chrome)  
README.md           Project documentation

---

## Requirements

### Common Requirements
- Python 3.x

### Playwright Bot
- playwright
- Playwright-supported browsers

### Selenium Bot
- selenium
- Google Chrome
- ChromeDriver available in system PATH

---

## Installation

### Playwright Installation
pip install playwright  
playwright install

### Selenium Installation
pip install selenium

Download the ChromeDriver version compatible with your Chrome browser and ensure it is added to your system PATH.

---

## Usage

### Running the Playwright Bot
python playwright_bot.py

### Running the Selenium Bot
python selenium_bot.py

Both scripts perform the following steps:
- Navigate to the Turkish typing test page
- Type words automatically for 60 seconds
- Wait 10 seconds after the test finishes
- Save a screenshot of the final results as final_result.png

---

## Configuration

### Typing Speed Adjustment

Typing speed can be customized to balance speed and accuracy.

Playwright:
page.keyboard.type(word, delay=0)

Selenium:
Adjust the delay variable in the script.

---

### Test Duration

To change the typing duration, modify the following condition in either script:
while time.time() - start_time < 60

Replace 60 with the desired duration in seconds.

---

### Headless Mode

Both bots run in headless mode by default for maximum performance.

Playwright:
Set headless=False when launching the browser.

Selenium:
Remove the --headless option from Chrome settings.

---

## Contributing

Contributions are welcome.  
Bug reports, feature suggestions, and pull requests are encouraged.

---

## License

This project is licensed under the MIT License.  
See the LICENSE file for more information.

---

## Disclaimer

This project is intended for educational and experimental purposes only.  
Ensure that your usage complies with the target website’s terms of service.
