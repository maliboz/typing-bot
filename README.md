# 10fastfingers Typing Bot (Turkish)

This repository contains two implementations of an automated typing bot for the [10fastfingers Turkish typing test](https://10fastfingers.com/typing-test/turkish). The bots are designed to type as fast as possible for 60 seconds and then capture a screenshot of the final results. One implementation utilizes [Playwright](https://playwright.dev/python/), while the other is built with [Selenium](https://www.selenium.dev/).

---

## 📂 Repository Structure

- **`playwright_bot.py`** - High-speed typing bot implemented with Playwright.
- **`selenium_bot.py`** - High-speed typing bot implemented with Selenium (headless Chrome).
- **`README.md`** - This documentation file.

---

## 📌 Prerequisites

### ✅ Common Requirements
- **Python 3.x**

### 🚀 Installation
#### 🔹 Playwright Bot
1. Install the Playwright package:
   ```bash
   pip install playwright
   ```
2. Install the supported browsers:
   ```bash
   playwright install
   ```

#### 🔹 Selenium Bot
1. Install Selenium:
   ```bash
   pip install selenium
   ```
2. Download and install the appropriate WebDriver (e.g., **ChromeDriver**) and ensure it is available in your system's PATH.

---

## 🎯 Usage

### ▶️ Running the Playwright Bot
To execute the Playwright bot, run:
```bash
python playwright_bot.py
```

### ▶️ Running the Selenium Bot
To execute the Selenium bot, run:
```bash
python selenium_bot.py
```

Both bots will:
- Navigate to the [10fastfingers Turkish typing test](https://10fastfingers.com/typing-test/turkish).
- Type as fast as possible for **60 seconds**.
- Wait **10 seconds** after the test completion.
- Capture a screenshot named **`final_result.png`**.

---

## ⚙️ Customization

### ⏳ Typing Speed
- Adjust the per-character delay:
  - **Playwright Bot:** Modify the delay in `page.keyboard.type(word, delay=0)`.
  - **Selenium Bot:** Change the `delay` variable in the script to balance speed and accuracy.

### ⏲️ Test Duration
- Modify the loop condition in the scripts:
  ```python
  while time.time() - start_time < 60:
  ```
  Change `60` to your preferred test duration in seconds.

### 🖥️ Headless Mode
- Both implementations run in **headless mode** for maximum performance.
- For debugging purposes, you can disable headless mode:
  - **Playwright:** Set `headless=False`.
  - **Selenium:** Remove the `headless` argument.

---

## 🤝 Contributing
Contributions are welcome! If you have any **improvements** or **bug fixes**, feel free to **open an issue** or **submit a pull request**.

---

## 📜 License
This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## ⚠️ Disclaimer
This project is intended for **educational purposes only**. Please use it **responsibly** and ensure that your usage complies with the **target website's terms of service**.

