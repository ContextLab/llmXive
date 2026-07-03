#!/bin/bash
# Run linting and formatting checks
# Exits with non-zero status if checks fail

set -e

echo "Running flake8..."
flake8 src/ tests/

echo "Running black check..."
black --check src/ tests/

echo "Running isort check..."
isort --check-only src/ tests/

echo "All linting checks passed."
