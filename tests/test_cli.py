import contextlib
import io
import unittest

from typing_coach import cli


class CliTest(unittest.TestCase):
    def test_help_renders_without_running_browser(self):
        output = io.StringIO()

        with self.assertRaises(SystemExit) as error:
            with contextlib.redirect_stdout(output):
                cli.main(["selenium", "--help"])

        self.assertEqual(error.exception.code, 0)
        self.assertIn("--strategy", output.getvalue())
        self.assertIn("--max-words", output.getvalue())


if __name__ == "__main__":
    unittest.main()
