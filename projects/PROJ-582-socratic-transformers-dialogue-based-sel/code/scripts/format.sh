#!/bin/bash
# Formatting script for Socratic Transformers project
# Runs ruff check --fix and black on all Python files in src/ and tests/

set -e

echo "Running Ruff fix..."
ruff check --fix src/ tests/

echo "Running Black formatter..."
black src/ tests/

echo "Formatting complete."
