#!/bin/bash
# Script to format code with Black and lint with Ruff
# Usage: ./scripts/format.sh

set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff formatter (optional, replaces black if preferred)..."
# ruff format code/ tests/

echo "Formatting and linting complete."
