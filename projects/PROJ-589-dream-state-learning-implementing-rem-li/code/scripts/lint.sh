#!/usr/bin/env bash
set -euo pipefail

# Script to run linter (ruff) only

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CODE_DIR="$(dirname "$SCRIPT_DIR")"

echo "Running linter (ruff)..."
ruff check "$CODE_DIR"

echo "Linting complete."
