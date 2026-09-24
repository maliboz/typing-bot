# Changelog

## 0.2.0 — 2026-09-24

- Read current `word-box-words` / split `wb-…-aw` markers and older active-word layouts.
- Remove the first-word fallback and count acknowledged UI advances separately from attempts.
- Pipeline native Unicode keyboard events over a bounded CDP WebSocket connection in both turbo runners.
- Focus once; wait for hydration and word transitions instead of clicking or sleeping per word.
- Detect the current site's finite text exhaustion; add optional `--wpm` pacing for timed tests.
- Add browser selection, JSON results, native-event regression tests, and a repeatable local benchmark.
- Update benchmark claims to distinguish throughput, UI progress, and site scores.

## 0.1.0

- Updated Selenium and Playwright runners for the current 10FastFingers UI.
- Kept support for the old `#inputfield` and `span[wordnr]` structure.
- Made `10fastfingers-tr` the default target again.
- Added verified 60-second benchmark screenshots and commands.
- Fixed Playwright loading by waiting for the word box instead of network idle.
- Added a local demo page only as an offline fallback.
- Added package metadata, tests, GitHub issue templates, and CI.
