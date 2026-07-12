#!/bin/bash
# Format code with Black and lint with Ruff
# Usage: ./scripts/format.sh

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter (fix mode)..."
ruff check --fix code/ tests/

echo "Running Ruff linter (strict mode)..."
ruff check code/ tests/

echo "Formatting and linting complete."
