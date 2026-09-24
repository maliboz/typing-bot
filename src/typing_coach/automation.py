"""Selenium / Playwright launchers with a shared, acknowledged typing loop."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import socket
import time
from typing import Literal

from .cdp import CdpConnection, key_events
from .page_state import FOCUS, WAIT_STATE

DEFAULT_SCREENSHOT = Path("final_result.png")
DEFAULT_MAX_WORDS = 10000
TEN_FAST_FINGERS_TR = "https://10fastfingers.com/typing-test/turkish"
TypingStrategy = Literal["turbo", "active"]


@dataclass(frozen=True)
class AutomationResult:
    engine: str
    url: str
    strategy: str
    typed_words: int  # Confirmed UI advances, not attempts or official WPM.
    elapsed_seconds: float
    screenshot_path: Path
    attempted_words: int = 0
    stop_reason: str = "max_words"
    browser_version: str = ""
    target_wpm: float = 0


def resolve_target_url(target: str) -> str:
    if target in {"demo", "local"}:
        return (Path(__file__).resolve().parents[2] / "demo" / "typing_test.html").as_uri()
    if target in {"10fastfingers", "10fastfingers-tr", "turkish"}:
        return TEN_FAST_FINGERS_TR
    if target.startswith(("http://", "https://", "file://")):
        return target
    return Path(target).expanduser().resolve().as_uri()


def _validate(duration, delay, max_words, strategy, settle_seconds, wpm=0):
    for name, value in (("duration", duration), ("delay", delay), ("settle", settle_seconds), ("wpm", wpm)):
        if not math.isfinite(value) or value < 0:
            raise RuntimeError(f"{name} must be finite and non-negative.")
    if duration == 0 or max_words < 1 or not isinstance(max_words, int):
        raise RuntimeError("duration and max-words must be positive.")
    if strategy not in {"turbo", "active"}:
        raise RuntimeError("Strategy must be 'turbo' or 'active'.")


def _wait_args(token=None, timeout=15000, initial=False):
    return {"token": token, "timeout": max(1, timeout), "initial": initial}


def _drive_loop(state, send_word, wait_state, *, duration, max_words, delay, wpm=0):
    """Never send another word until the previous submission advances the UI."""
    started = time.perf_counter()
    deadline = started + duration
    confirmed = attempted = 0
    characters = 0
    reason = "max_words"
    while confirmed < max_words:
        if wpm and characters:
            due = min(deadline, started + characters * 60 / (wpm * 5))
            time.sleep(max(0, due - time.perf_counter()))
        if time.perf_counter() >= deadline:
            reason = "duration"
            break
        if state.get("done"):
            reason = "completed"
            break
        word = state.get("word", "")
        if not state.get("ready") or not word or any(c.isspace() for c in word):
            reason = "unsupported_page"
            break
        previous = state
        send_word(word)
        attempted += 1
        characters += len(word) + 1
        remaining = deadline - time.perf_counter()
        # Check the deadline between words; at most one word is in flight.
        state = wait_state(_wait_args(previous["token"], min(2000, max(1, remaining * 1000))))
        if state.get("timedOut"):
            reason = "duration" if time.perf_counter() >= deadline else "stalled"
            break
        if state.get("errors", 0) > previous.get("errors", 0):
            confirmed += 1
            reason = "input_error"
            break
        if state.get("exhausted"):
            confirmed += 1
            reason = "words_exhausted"
            break
        if state.get("done") and not state.get("ready"):
            confirmed += 1
            reason = "completed"
            break
        if state.get("token") == previous["token"]:
            reason = "stalled"
            break
        confirmed += 1
        if delay and confirmed < max_words:
            time.sleep(min(delay, max(0, deadline - time.perf_counter())))
    return confirmed, attempted, round(time.perf_counter() - started, 6), reason


def _cdp_wait(connection, args):
    return connection.evaluate(f"({WAIT_STATE})({json.dumps(args)})")


def _screenshot_path(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_selenium(
    target="10fastfingers-tr", duration=60, headless=False, delay=0.02,
    max_words=DEFAULT_MAX_WORDS, strategy: TypingStrategy = "turbo",
    screenshot_path=DEFAULT_SCREENSHOT, settle_seconds=5.0, browser_path=None, wpm=0,
) -> AutomationResult:
    _validate(duration, delay, max_words, strategy, settle_seconds, wpm)
    try:
        from selenium import webdriver
        from selenium.common.exceptions import WebDriverException
        from selenium.webdriver.common.action_chains import ActionChains
    except ImportError as exc:
        raise RuntimeError("Install Selenium: python -m pip install '.[selenium]'") from exc
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.page_load_strategy = "eager"
    options.add_argument("--remote-debugging-address=127.0.0.1")
    if browser_path:
        options.binary_location = str(Path(browser_path).resolve())
    driver = connection = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False,
        })
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(20)
        url = resolve_target_url(target)
        driver.get(url)
        wait_state = lambda args: driver.execute_async_script(
            f"const done = arguments[1]; ({WAIT_STATE})(arguments[0]).then(done);", args
        )
        state = wait_state(_wait_args(initial=True))
        if not state.get("ready"):
            raise RuntimeError("No supported active word appeared within 15s; the site layout may have changed.")
        driver.execute_script(f"({FOCUS})()")
        if strategy == "turbo":
            info = driver.execute_cdp_cmd("Target.getTargetInfo", {})["targetInfo"]
            connection = CdpConnection(driver.capabilities["goog:chromeOptions"]["debuggerAddress"], info["targetId"])
            send_word = connection.type_word
            wait_state = lambda args: _cdp_wait(connection, args)
        else:
            send_word = lambda word: ActionChains(driver).send_keys(word + " ").perform()
        confirmed, attempted, elapsed, reason = _drive_loop(
            state, send_word, wait_state, duration=duration, max_words=max_words,
            delay=delay if strategy == "active" else 0,
            wpm=wpm,
        )
        time.sleep(settle_seconds)
        path = _screenshot_path(screenshot_path)
        if not driver.save_screenshot(str(path)):
            raise RuntimeError(f"Screenshot could not be saved: {path}")
        return AutomationResult("selenium", url, strategy, confirmed, elapsed, path,
                                attempted, reason, driver.capabilities["browserVersion"], wpm)
    except WebDriverException as exc:
        raise RuntimeError(f"Selenium could not complete the run: {exc}") from exc
    finally:
        try:
            if connection:
                connection.close()
        finally:
            if driver:
                driver.quit()


def _playwright_type(page, session, word, mode):
    # Unicode needs explicit native key events on keydown-driven pages.
    chunk = ""
    for char in word + " ":
        if mode == "legacy" or char.isascii():
            chunk += char
        else:
            if chunk:
                page.keyboard.type(chunk)
                chunk = ""
            for event in key_events(char):
                session.send("Input.dispatchKeyEvent", event)
    if chunk:
        page.keyboard.type(chunk)


def run_playwright(
    target="10fastfingers-tr", duration=60, headless=False, delay=0.02,
    max_words=DEFAULT_MAX_WORDS, strategy: TypingStrategy = "turbo",
    screenshot_path=DEFAULT_SCREENSHOT, settle_seconds=5.0, browser_path=None, wpm=0,
) -> AutomationResult:
    _validate(duration, delay, max_words, strategy, settle_seconds, wpm)
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError as exc:
        raise RuntimeError("Install Playwright: python -m pip install '.[playwright]' then python -m playwright install chromium") from exc
    # Select a loopback port. A collision fails target-id verification rather
    # than attaching to a different browser or an unrelated user tab.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    browser = connection = None
    with sync_playwright() as playwright:
        try:
            launch = {"headless": headless}
            if strategy == "turbo":
                launch["args"] = [f"--remote-debugging-port={port}", "--remote-debugging-address=127.0.0.1"]
            if browser_path:
                launch["executable_path"] = str(Path(browser_path).resolve())
            browser = playwright.chromium.launch(**launch)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            url = resolve_target_url(target)
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            state = page.evaluate(WAIT_STATE, _wait_args(initial=True))
            if not state.get("ready"):
                raise RuntimeError("No supported active word appeared within 15s; the site layout may have changed.")
            page.evaluate(FOCUS)
            session = page.context.new_cdp_session(page)
            if strategy == "turbo":
                info = session.send("Target.getTargetInfo")["targetInfo"]
                connection = CdpConnection(f"127.0.0.1:{port}", info["targetId"])
                send_word = connection.type_word
                wait_state = lambda args: _cdp_wait(connection, args)
            else:
                send_word = lambda word: _playwright_type(page, session, word, state["mode"])
                wait_state = lambda args: page.evaluate(WAIT_STATE, args)
            confirmed, attempted, elapsed, reason = _drive_loop(
                state, send_word, wait_state, duration=duration, max_words=max_words,
                delay=delay if strategy == "active" else 0,
                wpm=wpm,
            )
            page.wait_for_timeout(settle_seconds * 1000)
            path = _screenshot_path(screenshot_path)
            page.screenshot(path=str(path))
            return AutomationResult("playwright", url, strategy, confirmed, elapsed, path,
                                    attempted, reason, browser.version, wpm)
        except Error as exc:
            raise RuntimeError(f"Playwright could not complete the run: {exc}") from exc
        finally:
            try:
                if connection:
                    connection.close()
            finally:
                if browser:
                    browser.close()
