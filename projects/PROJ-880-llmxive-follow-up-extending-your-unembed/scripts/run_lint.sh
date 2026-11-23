#!/bin/bash
set -e

echo "Running code quality checks..."

# Check Python syntax and style
echo "Running flake8..."
flake8 code/ tests/ --count --show-source --statistics

# Check formatting
echo "Running black check..."
black --check code/ tests/

# Check import sorting
echo "Running isort check..."
isort --check-only code/ tests/

echo "All linting checks passed."
