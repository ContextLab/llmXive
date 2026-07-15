#!/usr/bin/env bash
set -euo pipefail

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Linting complete."
