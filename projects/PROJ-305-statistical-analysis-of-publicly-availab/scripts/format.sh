#!/bin/bash
# Script to format and lint the codebase

set -e

echo "Running Black formatter..."
black .

echo "Running Ruff linter (auto-fix)..."
ruff check . --fix

echo "Running Ruff formatter (if available)..."
ruff format .

echo "Formatting complete."
