#!/usr/bin/env bash
# Run linting checks on the project
# Usage: ./scripts/lint.sh [files...]

set -e

if [ $# -eq 0 ]; then
    TARGET="code tests"
else
    TARGET="$*"
fi

echo "Running flake8 on: $TARGET"
flake8 --config .flake8 $TARGET

echo "Linting complete. No issues found."
