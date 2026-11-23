#!/bin/bash
# Script to run linting and formatting checks
# Task: T003 - Configure linting (ruff) and formatting (black)

set -e

echo "Running Ruff Linting..."
ruff check code/ tests/

echo "Running Black Formatting Check..."
black --check code/ tests/

echo "All checks passed!"
