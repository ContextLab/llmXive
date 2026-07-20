#!/bin/bash
# Basic test runner script for PROJ-346
# Runs pytest with the project's configuration

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the code directory (where pytest.ini is located)
cd "$SCRIPT_DIR"

echo "Running tests for PROJ-346..."
echo "Working directory: $(pwd)"
echo "----------------------------------------"

# Run pytest with verbose output
python -m pytest -v --tb=short

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "----------------------------------------"
    echo "All tests passed successfully!"
else
    echo "----------------------------------------"
    echo "Some tests failed. Exit code: $exit_code"
fi

exit $exit_code
