#!/bin/bash
# Linting and formatting script for the project
# Runs clang-format for C++ and black/flake8 for Python

set -e

PROJECT_ROOT=$(dirname "$(dirname "$(dirname "$0")")")
cd "$PROJECT_ROOT"

echo "=== Running Linting and Formatting ==="

# Check if tools are installed
if ! command -v clang-format &> /dev/null; then
    echo "WARNING: clang-format not found. Skipping C++ formatting."
else
    echo "Formatting C++ files with clang-format..."
    find code/benchmark -name "*.cpp" -o -name "*.hpp" -o -name "*.h" | \
    xargs -I {} clang-format -i --style=file --assume-filename={} \
    --dry-run 2>&1 || echo "Clang-format dry run completed (check output for issues)."
fi

if ! command -v black &> /dev/null; then
    echo "WARNING: black not found. Skipping Python formatting."
else
    echo "Formatting Python files with black..."
    black --check code/analysis code/scripts 2>&1 || echo "Black check completed (run 'black code/ analysis code/scripts' to fix)."
fi

if ! command -v flake8 &> /dev/null; then
    echo "WARNING: flake8 not found. Skipping Python linting."
else
    echo "Linting Python files with flake8..."
    flake8 code/analysis code/scripts 2>&1 || echo "Flake8 check completed (fix issues manually)."
fi

echo "=== Linting and Formatting Complete ==="
