#!/bin/bash
# Script to check code formatting without modifying files (CI friendly)
set -e

echo "Checking Black formatting..."
black --check code/ tests/ scripts/

echo "Checking Ruff linting..."
ruff check code/ tests/ scripts/

echo "All checks passed."