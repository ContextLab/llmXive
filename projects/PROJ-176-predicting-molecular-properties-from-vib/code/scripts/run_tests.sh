#!/bin/bash
# Shell script to run the test suite
# Usage: ./run_tests.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Running test suite for llmXive project..."
echo "Project root: $PROJECT_ROOT"

# Ensure results directory exists for coverage reports
mkdir -p "$PROJECT_ROOT/results"

# Run pytest with coverage
cd "$PROJECT_ROOT"
python -m pytest tests/ -v --cov=code --cov-report=term-missing --cov-report=xml:results/coverage.xml --cov-report=html:results/htmlcov

echo "Tests completed successfully."
echo "Coverage reports generated in results/"