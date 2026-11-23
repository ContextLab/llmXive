#!/bin/bash
# Run the full pytest suite including contract tests
# This script is used for T039: Run pytest full suite including contract tests

set -e

echo "Running pytest full suite..."

# Change to project root
cd "$(dirname "$0")/.."

# Run all tests with verbose output
python -m pytest tests/ -v --tb=short

echo "All tests completed successfully!"
