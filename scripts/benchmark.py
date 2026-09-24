"""Reproducible local comparison; never submits a public typing score."""
from dataclasses import asdict
import argparse
import json
from pathlib import Path
import platform
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from typing_coach.automation import run_playwright, run_selenium


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser-path", type=Path, required=True,
                        help="Use exactly the same Chrome binary for both engines")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "benchmark.json")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    runs = []
    for repeat in range(args.repeats):
        # Reverse order every repeat to reduce warmup/order bias.
        profiles = [(engine, strategy) for engine in ["selenium", "playwright"]
                    for strategy in ["active", "turbo"]]
        if repeat % 2:
            profiles.reverse()
        for engine, strategy in profiles:
            runner = run_selenium if engine == "selenium" else run_playwright
            result = runner(target=str(ROOT / "tests" / "fixtures" / "modern.html"),
                            browser_path=args.browser_path, strategy=strategy,
                            headless=True, delay=0, duration=30, max_words=120,
                            settle_seconds=0,
                            screenshot_path=ROOT / "outputs" / f"bench-{engine}-{strategy}.png")
            if result.typed_words != 120 or result.attempted_words != 120:
                raise RuntimeError(f"Incomplete benchmark: {result}")
            run = asdict(result)
            runs.append(run)
            print(f"{engine:10} {strategy:6} {result.elapsed_seconds:.6f}s", flush=True)
    summary = []
    for engine in ["selenium", "playwright"]:
        for strategy in ["active", "turbo"]:
            times = [r["elapsed_seconds"] for r in runs if r["engine"] == engine and r["strategy"] == strategy]
            summary.append(dict(engine=engine, strategy=strategy,
                                median_seconds=statistics.median(times)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(python=platform.python_version(),
        platform=platform.platform(), runs=runs, summary=summary), indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
