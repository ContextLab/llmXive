#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

echo "Running Ruff linting (no fix)..."
ruff check "$PROJECT_ROOT/code"

echo "Linting complete."
