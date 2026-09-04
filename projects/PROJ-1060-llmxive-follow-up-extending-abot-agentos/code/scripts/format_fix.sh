#!/bin/bash
# Script to automatically fix formatting and linting issues where possible
# Usage: ./scripts/format_fix.sh

set -e

echo "Running Black formatting..."
black code/

echo "Running Ruff fix (auto-fix)..."
ruff check code/ --fix --exit-zero

echo "Auto-fix complete."
