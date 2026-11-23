#!/bin/bash
# Script to format code with Black and lint with Ruff
# Run from the project root (code/)

set -e

echo "Formatting code with Black..."
black .

echo "Checking formatting with Ruff..."
ruff check .

echo "Formatting and linting complete."
