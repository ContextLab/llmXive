#!/bin/bash
# Script to run flake8 linting and black formatting checks
# Usage: ./code/run_lint_format.sh

set -e

echo "Running flake8 linter..."
flake8 code/

echo "Running black format check..."
black --check code/

echo "Linting and formatting checks passed."