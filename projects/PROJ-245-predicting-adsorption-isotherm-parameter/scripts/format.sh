#!/bin/bash
# Format code with Black and lint with Ruff
# Usage: ./scripts/format.sh

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter..."
ruff check code/ tests/ --fix

echo "Formatting and linting complete."
