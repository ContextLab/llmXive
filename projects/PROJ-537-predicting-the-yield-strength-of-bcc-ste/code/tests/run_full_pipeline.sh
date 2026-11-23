#!/bin/bash
# Script to run the full pipeline end-to-end integration test
# Usage: ./tests/run_full_pipeline.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "=========================================="
echo "Running Full Pipeline End-to-End Test"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo "Working Directory: $(pwd)"
echo ""

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if needed
if [ -f "code/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -q -r code/requirements.txt
fi

# Run the Python test script
echo "Running Python integration test..."
python code/tests/test_full_pipeline.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Full Pipeline Test PASSED"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "✗ Full Pipeline Test FAILED"
    echo "=========================================="
fi

exit $EXIT_CODE
