#!/bin/bash
# Script to run linting checks for the Socratic Transformers project
# Exits with non-zero status if any issues are found.

set -e

echo "Running Ruff checks..."
ruff check src/ tests/

echo "Running Black format checks..."
black --check src/ tests/

echo "All linting and formatting checks passed."
