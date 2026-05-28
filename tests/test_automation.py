from pathlib import Path
import unittest

from typing_coach.automation import resolve_target_url


class AutomationTest(unittest.TestCase):
    def test_resolves_10fastfingers_alias(self):
        self.assertEqual(
            resolve_target_url("10fastfingers-tr"),
            "https://10fastfingers.com/typing-test/turkish",
        )

    def test_resolves_demo_page(self):
        url = resolve_target_url("demo")

        self.assertTrue(url.startswith("file:///"))
        self.assertTrue(url.endswith("/demo/typing_test.html"))

    def test_resolves_local_file(self):
        url = resolve_target_url(str(Path("demo") / "typing_test.html"))

        self.assertTrue(url.startswith("file:///"))
        self.assertTrue(url.endswith("/demo/typing_test.html"))


if __name__ == "__main__":
    unittest.main()
