#!/bin/bash
# Script to run linting and formatting checks
# Usage: ./scripts/run_linting.sh [--fix]

set -e

FIX_MODE=false
if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
    echo "🔧 Running in fix mode..."
else
    echo "🔍 Running in check mode..."
fi

# Change to code directory
cd "$(dirname "$0")/.."

# Run Ruff (linting)
echo "🚨 Running Ruff linting..."
if [ "$FIX_MODE" = true ]; then
    ruff check --fix .
else
    ruff check .
fi

# Run Black (formatting)
echo "🎨 Running Black formatting check..."
if [ "$FIX_MODE" = true ]; then
    black .
else
    black --check .
fi

echo "✅ All checks passed!"
