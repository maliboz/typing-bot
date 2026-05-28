#!/usr/bin/env python3
"""Selenium entry point for the typing automation example."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from typing_coach.cli import main  # noqa: E402


def run_typing_bot() -> int:
    return main(["selenium", *(sys.argv[1:] or ["--target", "10fastfingers-tr"])])


if __name__ == "__main__":
    raise SystemExit(run_typing_bot())
