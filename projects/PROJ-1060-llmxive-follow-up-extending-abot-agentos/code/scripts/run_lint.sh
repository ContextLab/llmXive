#!/bin/bash
# Script to run Ruff linting on the codebase
# Usage: ./scripts/run_lint.sh

set -e

echo "Running Ruff linting..."
ruff check .

echo "Linting complete."
