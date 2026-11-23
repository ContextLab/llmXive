#!/bin/bash
# Run Full Integration Test Suite for llmXive
# This script orchestrates the complete execution flow.

set -e  # Exit on any error

echo "=== llmXive Full Integration Test Suite ==="
echo "Starting at: $(date)"

# Ensure we are in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

# Ensure logs directory exists
mkdir -p logs

# Run the main integration script
echo "Executing main integration suite..."
python3 src/main.py --run-full-sweep

EXIT_CODE=$?

echo "=== Suite Finished ==="
echo "Exit Code: $EXIT_CODE"
echo "Finished at: $(date)"

if [ $EXIT_CODE -eq 0 ]; then
    echo "All checks passed. Artifacts validated."
else
    echo "Suite failed. Check logs/integration_suite.log for details."
fi

exit $EXIT_CODE