#!/usr/bin/env bash
# T003: Verify linting configuration by running `ruff check .` successfully.
set -e

# Run from the project root (one level above this script).
cd "$(dirname "$0")/.."

# Ensure ruff is available (pinned in pyproject.toml dev extras).
if ! command -v ruff >/dev/null 2>&1; then
    echo "ruff not found on PATH; installing..."
    python -m pip install --quiet "ruff>=0.1.0"
fi

echo "ruff version: $(ruff --version)"

# First attempt: plain check.
if ruff check .; then
    echo "LINT OK: ruff check . passed with no violations."
    exit 0
fi

# Second attempt: apply autofixes (import sorting, unused imports, etc.),
# then re-check. If violations remain, fail loudly.
echo "Initial check failed; applying ruff autofixes and re-checking..."
ruff check . --fix || true
if ruff check .; then
    echo "LINT OK: ruff check . passed after autofix."
    exit 0
fi

echo "LINT FAILED: ruff check . still reports violations after autofix." >&2
exit 1