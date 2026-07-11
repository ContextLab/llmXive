#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

echo "Running Ruff linting..."
ruff check "$PROJECT_ROOT/code"

echo "Running Black formatting..."
black "$PROJECT_ROOT/code"

echo "Running Ruff auto-fix..."
ruff check --fix "$PROJECT_ROOT/code" || true

echo "Formatting complete."
