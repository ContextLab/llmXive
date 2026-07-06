#!/usr/bin/env bash
set -euo pipefail

# Script to format code using black and lint using ruff
# Must be run from the project root or code directory

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CODE_DIR="$(dirname "$SCRIPT_DIR")"

echo "Running linter (ruff)..."
ruff check "$CODE_DIR"

echo "Running formatter (black)..."
black "$CODE_DIR"

echo "Formatting and linting complete."
