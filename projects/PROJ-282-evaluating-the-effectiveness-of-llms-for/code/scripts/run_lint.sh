#!/bin/bash
set -e

echo "Running Ruff (Linting)..."
cd code
python -m ruff check .

echo "Running Black (Formatting Check)..."
python -m black --check .

echo "Lint and Format checks passed."
