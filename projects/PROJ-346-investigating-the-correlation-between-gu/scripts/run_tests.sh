#!/bin/bash
# Basic test runner script for the Gut Microbiome and Cognitive Flexibility project.
# This script runs pytest with standard configurations for the project.

set -e

# Project root is the directory containing this script's parent (scripts/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Running tests for PROJ-346..."
echo "Project root: $PROJECT_ROOT"

# Ensure we are using the virtual environment if one exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest with specific flags:
# -v: Verbose output
# -m "not slow": Exclude slow tests by default
# --tb=short: Short traceback format
# --cov=code: Generate coverage report for the code directory (optional, requires pytest-cov)
# --cov-report=term-missing: Show coverage in terminal with missing lines
# tests/: Run tests in the tests directory

# Check if pytest-cov is installed, if not, run without coverage
if python -c "import pytest_cov" 2>/dev/null; then
    pytest -v -m "not slow" --tb=short --cov=code --cov-report=term-missing tests/
else
    pytest -v -m "not slow" --tb=short tests/
fi

echo "Test run completed."
