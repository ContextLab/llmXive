#!/bin/bash
# Script to automatically fix linting and formatting issues
# Uses Ruff for fixes and Black for formatting.

set -e

echo "Running Black to format code..."
black src/ tests/

echo "Running Ruff to fix linting issues..."
ruff check --fix src/ tests/

echo "Formatting and linting fixes applied."