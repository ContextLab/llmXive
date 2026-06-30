#!/bin/bash
# Convenience script to format code and run linters
# Usage: bash code/format_and_lint.sh

set -e

echo "Formatting code with Black..."
python -m black code/

echo "Fixing linting issues with Ruff..."
python -m ruff check --fix code/

echo "Running final check..."
python -m black --check code/
python -m ruff check code/

echo "All checks passed."