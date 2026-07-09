#!/usr/bin/env bash
# Script to run Flake8 linter on the codebase

set -e

echo "Running Flake8 linter..."
flake8 code/ tests/
echo "Linting complete."