#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "Running Black formatter..."
python -m black code/
echo "Running Ruff linter (fix mode)..."
python -m ruff check --fix code/
echo "Formatting and linting complete."
