#!/bin/bash
# Script to format code and apply linting fixes
set -e

echo "Running Black formatter..."
black code/src code/tests

echo "Running Ruff to check for errors and autofix..."
ruff check --fix code/src code/tests

echo "Formatting and linting complete."
