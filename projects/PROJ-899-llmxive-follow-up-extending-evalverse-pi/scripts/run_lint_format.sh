#!/usr/bin/env bash
set -euo pipefail

echo "Running linting (ruff)..."
ruff check code/

echo "Running formatter (black)..."
black --check code/

echo "All checks passed."
