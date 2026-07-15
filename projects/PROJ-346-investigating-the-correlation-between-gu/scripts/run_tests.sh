#!/bin/bash
# Basic test runner script for PROJ-346
# Runs pytest with the project's configuration

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_DIR="$PROJECT_ROOT/code"
TESTS_DIR="$PROJECT_ROOT/tests"

echo "Running tests for PROJ-346..."
echo "Project root: $PROJECT_ROOT"
echo "Code directory: $CODE_DIR"
echo "Tests directory: $TESTS_DIR"

# Ensure we are in the project root
cd "$PROJECT_ROOT"

# Run pytest using the configuration in code/pytest.ini
# We pass the tests directory explicitly to ensure discovery works
python -m pytest "$TESTS_DIR" -c "$CODE_DIR/pytest.ini" "$@"

echo "Test run completed."
