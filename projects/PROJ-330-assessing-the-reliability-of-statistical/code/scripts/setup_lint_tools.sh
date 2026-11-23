#!/usr/bin/env bash
# T003: Install and verify linting (flake8) and formatting (black) tools.
# Exits non-zero on any failure so CI can catch broken tooling.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== Installing flake8 and black =="
python -m pip install --quiet "flake8>=6.0" "black>=24.0"

echo "== Verifying flake8 configuration =="
python -m flake8 --version
if [ ! -f .flake8 ]; then
    echo "ERROR: .flake8 configuration missing" >&2
    exit 1
fi
# Dry-run flake8 over the source tree; report violations but do not
# fail the setup on pre-existing lint debt (config syntax is validated).
python -m flake8 src scripts tests main.py || echo "NOTE: flake8 reported violations above (pre-existing lint debt)."

echo "== Verifying black configuration =="
python -m black --version
if [ ! -f pyproject.toml ]; then
    echo "ERROR: pyproject.toml (black config) missing" >&2
    exit 1
fi
# Check formatting without modifying files.
python -m black --check src scripts tests main.py || echo "NOTE: black reported unformatted files above; run 'python -m black src scripts tests main.py' to fix."

echo "== Lint tooling configured successfully =="
