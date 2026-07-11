#!/bin/bash
# T019 Verification Runner Script
# Executes the verification routine to ensure T014-T018 outputs are valid

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Running T019 Verification..."
echo "Project Root: $PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Run the verification script
python code/data/verify_output.py

echo "Verification complete."
