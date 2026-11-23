#!/bin/bash
# Script to automatically fix linting and formatting issues
# Usage: ./scripts/fix_all.sh

set -e

echo "Fixing code quality issues..."

echo "--- Running Ruff (auto-fix) ---"
ruff check . --fix

echo "--- Running Black ---"
black .

echo "--- Fixes applied ---"