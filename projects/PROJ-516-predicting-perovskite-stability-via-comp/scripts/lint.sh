#!/usr/bin/env bash
set -euo pipefail

echo "Running Flake8..."
python -m flake8 code/ tests/ || true

echo "Running Pylint..."
# We use a custom rcfile to suppress specific warnings common in data science code
python -m pylint code/ --rcfile=.pylintrc --output-format=colorized || true

echo "Linting complete."
