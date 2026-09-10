#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "Running Ruff linter..."
python -m ruff check code/
echo "Linting complete."
