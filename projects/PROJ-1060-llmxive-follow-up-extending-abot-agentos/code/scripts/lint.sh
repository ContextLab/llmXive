#!/bin/bash
# Script to run Ruff linter in strict mode
# Usage: ./scripts/lint.sh

set -e

echo "Running Ruff linter..."
ruff check code/ --output-format=full

echo "Linting complete."
