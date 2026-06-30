#!/bin/bash
# Script to run linting and formatting checks for the llmXive project
# Usage: ./scripts/lint_and_format.sh [--fix]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Running linting and formatting checks for llmXive project..."
echo "Project root: $PROJECT_ROOT"

# Change to project root
cd "$PROJECT_ROOT"

if [ "$1" == "--fix" ]; then
    echo "Fixing issues with ruff and black..."
    ruff check --fix .
    black .
else
    echo "Checking for issues (use --fix to auto-correct)..."
    ruff check .
    black --check .
fi

echo "Done."
