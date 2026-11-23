#!/usr/bin/env bash
# Script to format code using Black and sort imports using Ruff
set -e

echo "Formatting code with Black..."
black src/ tests/

echo "Sorting imports and fixing linting issues with Ruff..."
ruff check --fix src/ tests/

echo "Formatting complete."
