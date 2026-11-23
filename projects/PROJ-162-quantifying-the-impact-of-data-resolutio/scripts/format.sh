#!/bin/bash
# Script to format and lint the codebase

set -e

echo "Running Ruff (lint + fix)..."
ruff check --fix .

echo "Running Black (format)..."
black .

echo "Running Ruff format (alternative if enabled)..."
ruff format .

echo "Formatting complete."
