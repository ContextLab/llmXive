#!/bin/bash
# Run Ruff linter without auto-fixing
# Usage: ./scripts/lint.sh

set -e

echo "Running Ruff linter (strict mode)..."
ruff check code/ tests/

echo "Linting complete."
