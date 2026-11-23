#!/bin/bash
# Script to run Black formatting and Flake8 linting on the code directory
# Usage: ./code/format_check.sh

set -e

echo "Running Black check..."
black --check --line-length 100 code/

echo "Running Flake8 linting..."
flake8 --max-line-length=100 --ignore=E203,E266,W503 code/

echo "Running Pylint..."
pylint --max-line-length=100 --disable=C0114,C0115,C0116,R0903,W0511 code/

echo "All checks passed."
