#!/usr/bin/env bash
# Format codebase using black and ruff
set -e

echo "Running ruff check (fix)..."
python -m ruff check code/ tests/ --fix

echo "Running black..."
python -m black --line-length 100 code/ tests/

echo "Formatting complete."
