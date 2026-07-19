#!/bin/bash
# data-hygiene.sh
# Wrapper script to execute data hygiene checks and update checksums.
# This script enforces Constitution Principle III by ensuring the
# state/checksums.json file is the single source of truth for file integrity.

set -e

# Determine the project root (assumes script is in code/scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root to ensure relative paths in Python work correctly
cd "$PROJECT_ROOT"

echo "Running data hygiene checks..."

# Execute the Python hygiene module
# The Python script handles directory creation and file scanning
python code/src/data_hygiene.py

if [ $? -eq 0 ]; then
    echo "Data hygiene check completed successfully."
    echo "Checksums written to: state/checksums.json"
else
    echo "ERROR: Data hygiene check failed."
    exit 1
fi