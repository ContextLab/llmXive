#!/bin/bash
# Formatting script for llmXive project
# Uses black for formatting and ruff for linting

set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff linter (fix mode)..."
ruff check code/ --fix

echo "Running Ruff linter (report mode)..."
ruff check code/

echo "Formatting and linting complete."
