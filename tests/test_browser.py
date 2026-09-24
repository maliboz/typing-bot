"""Opt-in integration tests: TYPING_BOT_BROWSER_TESTS=1, optional BROWSER path."""
import os
from pathlib import Path
import socket
import unittest

from typing_coach.automation import _cdp_wait, _drive_loop, _playwright_type, _wait_args
from typing_coach.cdp import CdpConnection
from typing_coach.page_state import FOCUS, READ_STATE, WAIT_STATE


@unittest.skipUnless(os.environ.get("TYPING_BOT_BROWSER_TESTS") == "1", "opt-in browser tests")
class BrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.playwright = sync_playwright().start()
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            cls.port = probe.getsockname()[1]
        options = dict(headless=True, args=[f'--remote-debugging-port={cls.port}'])
        if os.environ.get('TYPING_BOT_BROWSER'):
            options['executable_path'] = os.environ['TYPING_BOT_BROWSER']
        cls.browser = cls.playwright.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_native_input_handles_unicode_duplicates_recycling_and_delayed_render(self):
        fixture = (Path(__file__).parent / 'fixtures' / 'modern.html').resolve().as_uri()
        for query in ['', '?old=1', '?delay=25&hydrate=1']:
            for strategy in ['turbo', 'active']:
                with self.subTest(query=query, strategy=strategy):
                    page = self.browser.new_page()
                    connection = None
                    try:
                        page.goto(fixture + query)
                        state = page.evaluate(WAIT_STATE, _wait_args(initial=True))
                        page.evaluate(FOCUS)
                        session = page.context.new_cdp_session(page)
                        if strategy == 'turbo':
                            target = session.send('Target.getTargetInfo')['targetInfo']['targetId']
                            connection = CdpConnection(f'127.0.0.1:{self.port}', target)
                            send = connection.type_word
                            wait = lambda args: _cdp_wait(connection, args)
                        else:
                            send = lambda word: _playwright_type(page, session, word, 'modern')
                            wait = lambda args: page.evaluate(WAIT_STATE, args)
                        result = _drive_loop(state, send, wait, duration=30, max_words=200, delay=0)
                        stats = page.evaluate('window.stats')
                        self.assertEqual(result[:2], (120, 120))
                        self.assertEqual(result[3], 'completed')
                        self.assertEqual(stats['correct'], 120)
                        self.assertEqual(stats['untrusted'], 0)
                        self.assertEqual(stats['values'][:2], ['aynı', 'aynı'])
                    finally:
                        if connection:
                            connection.close()
                        page.close()

    def test_unknown_layout_does_not_fall_back_to_first_word(self):
        page = self.browser.new_page()
        try:
            page.set_content('<div class="word-box">first second</div>')
            self.assertFalse(page.evaluate(READ_STATE)['ready'])
        finally:
            page.close()

    def test_cursor_movement_does_not_count_as_progress(self):
        page = self.browser.new_page()
        try:
            page.set_content('<div data-testid="word-box-words"><span class="wb-test-aw">aynı</span><span> </span><span>aynı</span></div>')
            before = page.evaluate(READ_STATE)
            page.evaluate('''() => document.querySelector('div').innerHTML =
              '<span class="wb-test-aw wb-test-t">ay</span><span class="wb-test-aw wb-test-ac">nı</span><span> </span><span>aynı</span>' ''')
            after = page.evaluate(READ_STATE)
            self.assertEqual(before['token'], after['token'])
            self.assertEqual(after['word'], 'aynı')
        finally:
            page.close()

    def test_all_typed_spans_signal_exhaustion(self):
        page = self.browser.new_page()
        try:
            page.set_content('<div data-testid="word-box-words"><span class="wb-test-t">çığ</span><span class="wb-test-t"> </span></div>')
            state = page.evaluate(WAIT_STATE, _wait_args('previous', 100))
            self.assertTrue(state['exhausted'])
            self.assertNotIn('timedOut', state)
        finally:
            page.close()


if __name__ == '__main__':
    unittest.main()
