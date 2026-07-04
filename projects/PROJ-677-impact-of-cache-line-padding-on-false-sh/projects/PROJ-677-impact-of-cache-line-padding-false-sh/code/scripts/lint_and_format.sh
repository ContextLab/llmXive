#!/bin/bash
# Linting and formatting script for the project
# Usage: ./code/scripts/lint_and_format.sh [--fix]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../" && pwd)"
CODE_DIR="$PROJECT_ROOT/code"
TESTS_DIR="$PROJECT_ROOT/tests"

echo "Running linters and formatters..."

# Check for Python tools
if ! command -v black &> /dev/null; then
    echo "Warning: black not found. Installing..."
    pip install black
fi

if ! command -v flake8 &> /dev/null; then
    echo "Warning: flake8 not found. Installing..."
    pip install flake8
fi

if ! command -v clang-format &> /dev/null; then
    echo "Warning: clang-format not found. Ensure it is installed on the system."
fi

# Run flake8
echo "--- Running flake8 ---"
flake8 "$CODE_DIR" "$TESTS_DIR" --config="$PROJECT_ROOT/.flake8" || true

# Run black (check mode by default, fix if --fix passed)
echo "--- Running black ---"
if [[ "$1" == "--fix" ]]; then
    black "$CODE_DIR" "$TESTS_DIR" --config="$PROJECT_ROOT/pyproject.toml"
else
    black --check "$CODE_DIR" "$TESTS_DIR" --config="$PROJECT_ROOT/pyproject.toml"
fi

# Run clang-format (check mode)
if command -v clang-format &> /dev/null; then
    echo "--- Running clang-format ---"
    find "$CODE_DIR" -name "*.cpp" -o -name "*.hpp" -o -name "*.h" -o -name "*.c" | while read -r file; do
        clang-format --dry-run --Werror "$file"
    done || echo "Warning: clang-format check failed. Run manually to fix."
fi

echo "--- Linting and formatting checks complete ---"
