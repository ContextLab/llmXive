#!/bin/bash
# Run all checks (lint + format check)
set -e
echo "Running format check..."
python -m black --check .
echo "Running isort check..."
python -m isort --check-only .
echo "Running flake8..."
python -m flake8 .
echo "Running mypy..."
python -m mypy code/ --ignore-missing-imports
echo "All checks passed."