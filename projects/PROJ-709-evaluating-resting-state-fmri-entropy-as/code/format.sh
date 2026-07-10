#!/bin/bash
# Format code using Black and sort imports using Ruff
set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff linter (fix mode)..."
ruff check code/ --fix

echo "Formatting complete."
