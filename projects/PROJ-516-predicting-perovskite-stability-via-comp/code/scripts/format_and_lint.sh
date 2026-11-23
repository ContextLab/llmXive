#!/bin/bash
# Script to format and lint the codebase
# Usage: ./scripts/format_and_lint.sh

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running isort..."
isort code/ tests/

echo "Running Flake8..."
flake8 code/ tests/

echo "Running Pylint..."
pylint code/ tests/

echo "All checks passed."
