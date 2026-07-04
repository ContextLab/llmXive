#!/bin/bash
set -e

echo "Running flake8..."
python -m flake8 code/ tests/ --count --show-source --statistics

echo "Running black check..."
python -m black --check code/ tests/

echo "Running isort check..."
python -m isort --check-only code/ tests/

echo "All linting checks passed."
