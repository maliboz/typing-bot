#!/usr/bin/env python3
"""
10fastfingers Typing Bot using Playwright

This script automates the 10fastfingers Turkish typing test using Playwright.
It runs for 60 seconds, types the words displayed on the page as fast as possible,
and then captures a screenshot of the final results after a 10-second wait.

Usage:
    python playwright_bot.py
"""

import time
from playwright.sync_api import sync_playwright

def run_typing_bot():
    with sync_playwright() as p:
        # Launch Chromium in headless mode for maximum performance
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the 10fastfingers Turkish typing test page
        page.goto("https://10fastfingers.com/typing-test/turkish")
        
        # Wait for the input field to be present and click it to set focus
        page.wait_for_selector("#inputfield")
        page.click("#inputfield")
        
        current_index = 0  # Starting index for the 'wordnr' attribute
        start_time = time.time()  # Record the start time
        
        # Minimal delay between words (in seconds)
        delay = 0.01

        # Run the typing loop for 60 seconds
        while time.time() - start_time < 60:
            try:
                # Dynamically select the word element by its wordnr attribute
                xpath = f"//span[@wordnr='{current_index}']"
                element = page.wait_for_selector(xpath, timeout=10000)
                word = element.inner_text().strip()
                
                # Click the input field to maintain focus
                page.click("#inputfield")
                
                # Type the word and then press space
                page.keyboard.type(word, delay=0)  # No per-character delay
                page.keyboard.press(" ")
                
                current_index += 1  # Move to the next word
                
                time.sleep(delay)  # Minimal delay between words
            except Exception as e:
                print(f"Error (wordnr {current_index}): {e}")
                time.sleep(0.5)  # Brief pause in case of error

        print("1 minute has elapsed. Waiting 10 seconds before capturing screenshot...")
        
        # Wait 10 seconds to let the final results settle
        time.sleep(10)
        
        # Capture a screenshot of the final result
        screenshot_path = "final_result.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved as: {screenshot_path}")
        
        browser.close()

if __name__ == "__main__":
    run_typing_bot()
