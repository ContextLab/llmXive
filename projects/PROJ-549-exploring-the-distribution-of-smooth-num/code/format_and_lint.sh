#!/bin/bash
# Script to run Black formatting and Flake8/Pylint linting on the codebase.
# This script is intended to be run from the project root directory.

set -e

CODE_DIR="code"

echo "=========================================="
echo "Running Black formatter..."
echo "=========================================="
black --config "${CODE_DIR}/pyproject.toml" "${CODE_DIR}"

echo ""
echo "=========================================="
echo "Running Flake8 linter..."
echo "=========================================="
flake8 --config="${CODE_DIR}/.flake8" "${CODE_DIR}"

echo ""
echo "=========================================="
echo "Running Pylint linter..."
echo "=========================================="
pylint --rcfile="${CODE_DIR}/pylintrc" "${CODE_DIR}"

echo ""
echo "=========================================="
echo "All checks passed successfully!"
echo "=========================================="
