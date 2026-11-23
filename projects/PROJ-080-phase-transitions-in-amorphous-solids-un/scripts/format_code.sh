#!/bin/bash
# Automatically format code and sort imports
# Exits with non-zero status if changes are required

set -e

echo "Running ruff check --fix..."
ruff check --fix code/ tests/

echo "Running ruff format..."
ruff format code/ tests/

echo "Code formatting complete."