#!/bin/bash
# Script to format code using Black and Ruff
# Usage: ./scripts/format.sh

set -e

echo "Running Ruff fix..."
ruff check --fix code/ tests/

echo "Running Black..."
black code/ tests/

echo "Formatting complete."
