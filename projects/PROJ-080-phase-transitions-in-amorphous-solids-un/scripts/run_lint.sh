#!/bin/bash
# Run linting checks for the project
# Exits with non-zero status if issues are found

set -e

echo "Running ruff check..."
ruff check code/ tests/

echo "Running ruff format check..."
ruff format --check code/ tests/

echo "Linting and formatting checks passed."
