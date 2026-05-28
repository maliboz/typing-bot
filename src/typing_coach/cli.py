"""Command line interface for the 10FastFingers bot."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from . import __version__
from .automation import DEFAULT_MAX_WORDS, DEFAULT_SCREENSHOT, run_playwright, run_selenium


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="typing-bot",
        description="Fast Selenium and Playwright automation for 10FastFingers.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    selenium = subparsers.add_parser("selenium", help="run the Selenium bot")
    add_automation_arguments(selenium)

    playwright = subparsers.add_parser(
        "playwright",
        help="run the Playwright bot",
    )
    add_automation_arguments(playwright)

    return parser


def add_automation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--target",
        default="10fastfingers-tr",
        help=(
            "10fastfingers-tr, demo, a URL, or a local HTML file path "
            "(default: 10fastfingers-tr)"
        ),
    )
    parser.add_argument(
        "-t",
        "--duration",
        type=int,
        default=60,
        help="maximum automation duration in seconds",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="run without opening a visible browser window",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="open a visible browser window; this is the default for demos",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.02,
        help="delay between words in active strategy",
    )
    parser.add_argument(
        "--strategy",
        choices=["turbo", "active"],
        default="turbo",
        help="turbo uses the fastest safe path; active types word by word with delay",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=DEFAULT_MAX_WORDS,
        help="maximum words to type in turbo or active mode",
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        default=DEFAULT_SCREENSHOT,
        help="where to save the final screenshot",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=5.0,
        help="seconds to wait before taking the final screenshot",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        argv = ["selenium"]
    args = parser.parse_args(argv)
    command = args.command

    if command == "selenium":
        return run_selenium_command(args)
    if command == "playwright":
        return run_playwright_command(args)

    parser.print_help()
    return 1


def run_selenium_command(args: argparse.Namespace) -> int:
    try:
        result = run_selenium(
            target=args.target,
            duration=args.duration,
            headless=args.headless and not args.headful,
            delay=args.delay,
            max_words=args.max_words,
            strategy=args.strategy,
            screenshot_path=args.screenshot,
            settle_seconds=args.settle,
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(format_automation_result(result))
    return 0


def run_playwright_command(args: argparse.Namespace) -> int:
    try:
        result = run_playwright(
            target=args.target,
            duration=args.duration,
            headless=args.headless and not args.headful,
            delay=args.delay,
            max_words=args.max_words,
            strategy=args.strategy,
            screenshot_path=args.screenshot,
            settle_seconds=args.settle,
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(format_automation_result(result))
    return 0


def format_automation_result(result) -> str:
    return (
        f"Engine: {result.engine}\n"
        f"Target: {result.url}\n"
        f"Strategy: {result.strategy}\n"
        f"Typed words: {result.typed_words}\n"
        f"Elapsed: {result.elapsed_seconds}s\n"
        f"Screenshot: {result.screenshot_path}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
