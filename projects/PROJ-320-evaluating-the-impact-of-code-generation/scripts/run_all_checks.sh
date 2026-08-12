#!/bin/bash
# Script to run all linting and formatting checks

set -e

echo "Running all code quality checks..."

echo "1. Running ruff linting..."
ruff check code/ tests/

echo "2. Running black formatting check..."
black --check code/ tests/

echo "All checks passed successfully!"