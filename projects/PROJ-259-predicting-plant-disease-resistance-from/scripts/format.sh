#!/usr/bin/env bash
# Format code according to project standards
# Usage: ./scripts/format.sh [files...]

set -e

if [ $# -eq 0 ]; then
    TARGET="code tests"
else
    TARGET="$*"
fi

echo "Running Black formatter on: $TARGET"
black --config pyproject.toml $TARGET

echo "Running isort on: $TARGET"
isort --settings-file pyproject.toml $TARGET

echo "Formatting complete. Running flake8 to verify..."
flake8 --config .flake8 $TARGET

echo "All checks passed."
