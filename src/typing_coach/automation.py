"""Browser automation runners used by the example scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Literal


DEFAULT_SCREENSHOT = Path("final_result.png")
DEFAULT_MAX_WORDS = 400
TEN_FAST_FINGERS_TR = "https://10fastfingers.com/typing-test/turkish"
TypingStrategy = Literal["turbo", "active"]


@dataclass(frozen=True)
class AutomationResult:
    engine: str
    url: str
    strategy: str
    typed_words: int
    elapsed_seconds: float
    screenshot_path: Path


def resolve_target_url(target: str) -> str:
    """Resolve a friendly target name into a URL."""

    if target in {"demo", "local"}:
        return (Path(__file__).resolve().parents[2] / "demo" / "typing_test.html").as_uri()
    if target in {"10fastfingers", "10fastfingers-tr", "turkish"}:
        return TEN_FAST_FINGERS_TR
    if target.startswith(("http://", "https://", "file://")):
        return target
    return Path(target).expanduser().resolve().as_uri()


def run_selenium(
    target: str = "10fastfingers-tr",
    duration: int = 60,
    headless: bool = False,
    delay: float = 0.02,
    max_words: int = DEFAULT_MAX_WORDS,
    strategy: TypingStrategy = "turbo",
    screenshot_path: Path = DEFAULT_SCREENSHOT,
    settle_seconds: float = 5.0,
) -> AutomationResult:
    """Run the typing automation with Selenium."""

    try:
        from selenium import webdriver
        from selenium.common.exceptions import TimeoutException
        from selenium.common.exceptions import WebDriverException
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as exc:
        raise RuntimeError(
            "Selenium is not installed. Run: python -m pip install '.[selenium]'"
        ) from exc

    url = resolve_target_url(target)
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--remote-debugging-pipe")
    chrome_options.add_argument("--window-size=1280,900")

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except WebDriverException as exc:
        raise RuntimeError(
            "Chrome could not be started by Selenium. Make sure Google Chrome is "
            "installed, then try again. In sandboxed environments, run the same "
            "command in your normal terminal."
        ) from exc
    started = time.monotonic()
    typed_words = 0

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        if strategy not in {"turbo", "active"}:
            raise RuntimeError("Strategy must be 'turbo' or 'active'.")

        if _selenium_has_legacy_input(driver, wait):
            typing_input = driver.find_element(By.ID, "inputfield")
            typing_input.click()
            mode = "legacy"
        else:
            word_box = _selenium_wait_for_modern_word_box(driver, wait)
            word_box.click()
            mode = "modern"

        started = time.monotonic()
        if strategy == "turbo":
            if mode == "legacy":
                words = _selenium_get_legacy_words(driver, max_words)
                if words:
                    typing_input = driver.find_element(By.ID, "inputfield")
                    typing_input.click()
                    typing_input.send_keys(_join_words(words))
                    typed_words = len(words)
            else:
                while time.monotonic() - started < duration and typed_words < max_words:
                    word = _selenium_get_modern_active_word(driver)
                    if not word:
                        break
                    ActionChains(driver).send_keys(word).send_keys(Keys.SPACE).perform()
                    typed_words += 1
        else:
            while time.monotonic() - started < duration and typed_words < max_words:
                if mode == "legacy":
                    try:
                        word = wait.until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, f"span[wordnr='{typed_words}']")
                            )
                        ).text.strip()
                    except TimeoutException:
                        break
                else:
                    word = _selenium_get_modern_active_word(driver)

                if not word:
                    break

                if mode == "legacy":
                    typing_input = driver.find_element(By.ID, "inputfield")
                    typing_input.click()
                    typing_input.send_keys(word)
                    typing_input.send_keys(Keys.SPACE)
                else:
                    ActionChains(driver).send_keys(word).send_keys(Keys.SPACE).perform()

                typed_words += 1
                time.sleep(delay)

        elapsed_seconds = round(time.monotonic() - started, 2)
        time.sleep(settle_seconds)
        screenshot_path = Path(screenshot_path)
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        if not driver.save_screenshot(str(screenshot_path)) or not screenshot_path.exists():
            raise RuntimeError(f"Screenshot could not be saved to: {screenshot_path}")
        return AutomationResult(
            engine="selenium",
            url=url,
            strategy=strategy,
            typed_words=typed_words,
            elapsed_seconds=elapsed_seconds,
            screenshot_path=screenshot_path,
        )
    finally:
        driver.quit()


def run_playwright(
    target: str = "10fastfingers-tr",
    duration: int = 60,
    headless: bool = False,
    delay: float = 0.02,
    max_words: int = DEFAULT_MAX_WORDS,
    strategy: TypingStrategy = "turbo",
    screenshot_path: Path = DEFAULT_SCREENSHOT,
    settle_seconds: float = 5.0,
) -> AutomationResult:
    """Run the typing automation with Playwright."""

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run: python -m pip install '.[playwright]' && playwright install chromium"
        ) from exc

    url = resolve_target_url(target)
    started = time.monotonic()
    typed_words = 0

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=headless)
        except Exception as exc:
            raise RuntimeError(
                "Playwright could not start Chromium. Run "
                "'playwright install chromium' and try from your normal terminal."
            ) from exc
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            page.goto(url, wait_until="domcontentloaded")

            if strategy not in {"turbo", "active"}:
                raise RuntimeError("Strategy must be 'turbo' or 'active'.")

            if page.locator("#inputfield").count() > 0:
                page.click("#inputfield")
                mode = "legacy"
            else:
                _playwright_wait_for_modern_word_box(page)
                page.click("div[class*='word-box']")
                mode = "modern"

            started = time.monotonic()
            if strategy == "turbo":
                if mode == "legacy":
                    words = _playwright_get_legacy_words(page, max_words)
                    if words:
                        page.click("#inputfield")
                        page.keyboard.type(_join_words(words), delay=0)
                        typed_words = len(words)
                else:
                    while time.monotonic() - started < duration and typed_words < max_words:
                        word = _playwright_get_modern_active_word(page)
                        if not word:
                            break
                        page.keyboard.type(word, delay=0)
                        page.keyboard.press(" ")
                        typed_words += 1
            else:
                while time.monotonic() - started < duration and typed_words < max_words:
                    if mode == "legacy":
                        selector = f"span[wordnr='{typed_words}']"
                        try:
                            word = page.locator(selector).inner_text(timeout=15000).strip()
                        except PlaywrightTimeoutError:
                            break
                    else:
                        word = _playwright_get_modern_active_word(page)

                    if not word:
                        break

                    if mode == "legacy":
                        page.click("#inputfield")
                    else:
                        page.click("div[class*='word-box']")
                    page.keyboard.type(word, delay=0)
                    page.keyboard.press(" ")
                    typed_words += 1
                    time.sleep(delay)

            elapsed_seconds = round(time.monotonic() - started, 2)
            time.sleep(settle_seconds)
            screenshot_path = Path(screenshot_path)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_path), full_page=True)
            if not screenshot_path.exists():
                raise RuntimeError(f"Screenshot could not be saved to: {screenshot_path}")
            return AutomationResult(
                engine="playwright",
                url=url,
                strategy=strategy,
                typed_words=typed_words,
                elapsed_seconds=elapsed_seconds,
                screenshot_path=screenshot_path,
            )
        finally:
            browser.close()


def _selenium_has_legacy_input(driver, wait) -> bool:
    del wait
    return bool(driver.find_elements("id", "inputfield"))


def _selenium_wait_for_modern_word_box(driver, wait):
    return wait.until(
        lambda current: next(
            (
                element
                for element in current.find_elements("css selector", "div[class*='word-box']")
                if element.text.strip()
            ),
            False,
        )
    )


def _selenium_get_modern_active_word(driver) -> str:
    word = driver.execute_script(
        """
        const active = [...document.querySelectorAll('.word-box-active-word')];
        if (active.length) {
          return active.map((node) => node.innerText || node.textContent || '').join('').trim();
        }

        const box = [...document.querySelectorAll('div[class*="word-box"]')]
          .find((node) => (node.innerText || '').trim().length);
        return box ? (box.innerText || '').trim().split(/\\s+/)[0] : '';
        """
    )
    return str(word or "").strip()


def _selenium_get_legacy_words(driver, max_words: int) -> list[str]:
    words = driver.execute_script(
        """
        const nodes = [...document.querySelectorAll('span[wordnr]')];
        return nodes
          .sort((left, right) => Number(left.getAttribute('wordnr')) - Number(right.getAttribute('wordnr')))
          .map((node) => (node.innerText || node.textContent || '').trim())
          .filter(Boolean)
          .slice(0, arguments[0]);
        """,
        max_words,
    )
    return _clean_words(words, max_words)


def _selenium_get_modern_words(driver, max_words: int) -> list[str]:
    words = driver.execute_script(
        """
        const box = [...document.querySelectorAll('div[class*="word-box"]')]
          .find((node) => (node.innerText || '').trim().length);
        if (!box) return [];
        return (box.innerText || box.textContent || '').trim().split(/\\s+/).slice(0, arguments[0]);
        """,
        max_words,
    )
    return _clean_words(words, max_words)


def _playwright_wait_for_modern_word_box(page) -> None:
    page.wait_for_function(
        """
        () => [...document.querySelectorAll('div[class*="word-box"]')]
          .some((node) => (node.innerText || '').trim().length)
        """,
        timeout=15000,
    )


def _playwright_get_modern_active_word(page) -> str:
    word = page.evaluate(
        """
        () => {
          const active = [...document.querySelectorAll('.word-box-active-word')];
          if (active.length) {
            return active.map((node) => node.innerText || node.textContent || '').join('').trim();
          }

          const box = [...document.querySelectorAll('div[class*="word-box"]')]
            .find((node) => (node.innerText || '').trim().length);
          return box ? (box.innerText || '').trim().split(/\\s+/)[0] : '';
        }
        """
    )
    return str(word or "").strip()


def _playwright_get_legacy_words(page, max_words: int) -> list[str]:
    words = page.evaluate(
        """
        (maxWords) => {
          const nodes = [...document.querySelectorAll('span[wordnr]')];
          return nodes
            .sort((left, right) => Number(left.getAttribute('wordnr')) - Number(right.getAttribute('wordnr')))
            .map((node) => (node.innerText || node.textContent || '').trim())
            .filter(Boolean)
            .slice(0, maxWords);
        }
        """,
        max_words,
    )
    return _clean_words(words, max_words)


def _playwright_get_modern_words(page, max_words: int) -> list[str]:
    words = page.evaluate(
        """
        (maxWords) => {
          const box = [...document.querySelectorAll('div[class*="word-box"]')]
            .find((node) => (node.innerText || '').trim().length);
          if (!box) return [];
          return (box.innerText || box.textContent || '').trim().split(/\\s+/).slice(0, maxWords);
        }
        """,
        max_words,
    )
    return _clean_words(words, max_words)


def _clean_words(words, max_words: int) -> list[str]:
    if not isinstance(words, list):
        return []
    return [str(word).strip() for word in words if str(word).strip()][:max_words]


def _join_words(words: list[str]) -> str:
    return " ".join(words).strip() + " "
