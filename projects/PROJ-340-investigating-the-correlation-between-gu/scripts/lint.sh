#!/usr/bin/env bash
set -euo pipefail

echo "Running linter (flake8)..."
flake8 code/ tests/ scripts/

echo "Linting complete."
