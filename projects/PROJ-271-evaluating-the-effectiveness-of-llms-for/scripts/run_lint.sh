#!/bin/bash
# Run linting and formatting checks
# Usage: ./scripts/run_lint.sh [--fix]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Running linting checks from: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Run flake8
echo "Running flake8..."
python -m flake8 code/ || true

# Run black check
echo "Running black check..."
if [ "$1" == "--fix" ]; then
    echo "Running black with fix mode..."
    python -m black code/
else
    python -m black --check code/ || true
fi

echo "Linting checks completed."
