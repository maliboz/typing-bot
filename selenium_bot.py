#!/usr/bin/env python3
"""
10fastfingers Typing Bot using Selenium

This script automates the 10fastfingers Turkish typing test using Selenium.
It runs for 60 seconds, types the words displayed on the page as fast as possible,
and then captures a screenshot of the final results after a 10-second wait.

Usage:
    python selenium_bot.py
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_typing_bot():
    # Configure Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")  # Recommended for Windows

    # Initialize the WebDriver for Chrome with headless mode enabled
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://10fastfingers.com/typing-test/turkish")

    # Wait for the input field to be present and click it to set focus
    wait = WebDriverWait(driver, 10)
    typing_input = wait.until(EC.presence_of_element_located((By.ID, "inputfield")))
    typing_input.click()

    current_index = 0  # Starting word index (wordnr begins at 0)
    start_time = time.time()  # Record the start time

    # Minimal delay for high-speed typing (in seconds)
    delay = 0.001

    # Run the typing loop for 60 seconds
    while time.time() - start_time < 60:
        try:
            # Dynamically retrieve the word element based on its 'wordnr' attribute
            xpath = f"//span[@wordnr='{current_index}']"
            word_element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            word = word_element.text.strip()
            
            # Re-locate the input field and click it to ensure focus
            typing_input = driver.find_element(By.ID, "inputfield")
            typing_input.click()
            
            # Send the word and a space to simulate typing
            typing_input.send_keys(word)
            typing_input.send_keys(Keys.SPACE)
            
            # Move to the next word
            current_index += 1
            
            # Minimal delay between words
            time.sleep(delay)
        except Exception as e:
            print(f"Error (wordnr {current_index}): {e}")
            time.sleep(1)  # Brief pause in case of error

    print("1 minute has elapsed. Waiting 10 seconds before capturing screenshot...")
    
    # Wait 10 seconds before capturing the final screen
    time.sleep(10)
    
    # Capture and save a screenshot of the final result
    screenshot_path = "final_result.png"
    driver.save_screenshot(screenshot_path)
    print(f"Screenshot saved as: {screenshot_path}")
    
    driver.quit()

if __name__ == "__main__":
    run_typing_bot()
