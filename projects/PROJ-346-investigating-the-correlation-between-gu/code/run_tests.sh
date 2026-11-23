#!/bin/bash
# Basic test runner script for the gut microbiome and cognitive flexibility project
# This script sets up the environment and runs pytest with the project configuration.

set -e

# Determine the project root directory (assuming this script is in code/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project Root: $PROJECT_ROOT"
echo "Running tests from: $PROJECT_ROOT/tests"

# Change to project root to ensure relative imports in tests work correctly
cd "$PROJECT_ROOT"

# Check if virtual environment is activated or if we need to activate one
# Assuming standard venv usage in the project root
if [ -d "venv" ]; then
    echo "Virtual environment found. Activating..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Virtual environment found (.venv). Activating..."
    source .venv/bin/activate
fi

# Ensure pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed or not in PATH."
    echo "Please install it via: pip install pytest"
    exit 1
fi

# Run pytest with the configuration file
echo "Starting test execution..."
pytest -c code/pytest.ini "$@"

echo "Test execution finished."
