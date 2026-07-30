#!/bin/bash
# Run linting and formatting checks for the project
# Exit on first error
set -e

echo "Running flake8 linting..."
flake8 code/ --config=code/.flake8

echo "Running isort check..."
isort --check-only --diff code/

echo "Running black check..."
black --check --diff code/

echo "All linting checks passed."
