#!/bin/bash
# Script to run linting checks without fixing

set -e

echo "Running Ruff (lint only)..."
ruff check .

echo "Running Black (check only)..."
black --check .

echo "Linting complete."
