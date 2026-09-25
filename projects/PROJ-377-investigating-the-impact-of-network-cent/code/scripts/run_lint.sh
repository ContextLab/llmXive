#!/bin/bash
# Run linting and formatting checks for the project
# Usage: bash code/scripts/run_lint.sh

set -e

echo "Running flake8 linting..."
flake8 code/

echo "Running isort check..."
isort --check-only code/

echo "Running black check..."
black --check code/

echo "All linting checks passed!"
