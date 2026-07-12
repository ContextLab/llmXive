#!/bin/bash
# Script to run formatting and linting checks on the project
# Usage: ./scripts/format_and_lint.sh

set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff linter..."
ruff check code/ --fix

echo "Running Ruff format check..."
ruff format --check code/

echo "Linting and formatting complete."