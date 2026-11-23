#!/bin/bash
# Script to run the full pytest suite for the project
# This script ensures all tests pass as required by T038

set -e  # Exit on error

echo "=========================================="
echo "Running Pytest Suite for T038"
echo "=========================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment not found. Running with system Python."
fi

# Run pytest with verbose output
echo "Running tests..."
pytest tests/ -v --tb=short

echo "=========================================="
echo "All tests completed successfully!"
echo "=========================================="

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate
fi
