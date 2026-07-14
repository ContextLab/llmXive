#!/bin/bash
# Script to run linting and formatting checks for the project.
# This script assumes dependencies (black, flake8, isort) are installed.

set -e

echo "Running isort..."
python -m isort code/ --profile black --check-only

echo "Running black..."
python -m black --check --line-length 88 code/

echo "Running flake8..."
python -m flake8 --config=code/.flake8 code/

echo "All linting checks passed."
