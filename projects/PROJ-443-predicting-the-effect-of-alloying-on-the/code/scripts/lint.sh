#!/bin/bash
set -e

echo "Running linters..."

# Run flake8
echo "Checking with flake8..."
python -m flake8 code/

# Run black check (dry run)
echo "Checking formatting with black..."
python -m black --check code/

# Run isort check
echo "Checking imports with isort..."
python -m isort --check-only code/

echo "All linters passed."
