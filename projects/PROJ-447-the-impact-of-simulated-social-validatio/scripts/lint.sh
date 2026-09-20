#!/bin/bash
# Lint code with Ruff and check Black formatting

echo "Checking Black formatting..."
black --check code/ tests/

echo "Running Ruff linter..."
ruff check code/ tests/

if [ $? -eq 0 ]; then
    echo "Linting passed!"
else
    echo "Linting failed. Please fix the issues above."
    exit 1
fi