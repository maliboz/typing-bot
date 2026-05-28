# Contributing

Thanks for helping improve Typing Bot.

## Local setup

```bash
python -m venv .venv
python -m pip install -e ".[all]"
```

Browser automation dependencies are optional extras. Keep new dependencies rare
and justify them in the pull request.

## Tests

```bash
python -m unittest discover -s tests
```

## Pull request checklist

- Keep changes focused and user-facing behavior documented.
- Add or update tests for CLI or automation behavior changes.
- Run the test suite before opening a pull request.
- Keep browser automation examples readable enough for beginners to study.
- Keep the real 10FastFingers target as the main example.
