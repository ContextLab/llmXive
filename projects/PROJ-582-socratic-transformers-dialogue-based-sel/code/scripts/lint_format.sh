#!/bin/bash
# Lint and format script for Socratic Transformers project
# Usage: ./scripts/lint_format.sh [--fix]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Running lint checks..."
ruff check src/ tests/

echo "Running format checks..."
black --check src/ tests/

if [ "$1" == "--fix" ]; then
    echo "Fixing lint issues..."
    ruff check --fix src/ tests/

    echo "Applying formatting..."
    black src/ tests/

    echo "Lint and format fixes applied successfully."
else
    echo "Run with --fix to automatically apply fixes."
fi
