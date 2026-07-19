#!/bin/bash
# data-hygiene.sh
# Wrapper script to execute data hygiene checks and update checksums.
# This script enforces Constitution Principle III by ensuring the
# state/checksums.json file is the single source of truth for file integrity.

set -e  # Exit immediately if a command exits with a non-zero status

# Determine the project root directory
# This script assumes it is run from the project root or a subdirectory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root to ensure relative paths in Python work correctly
cd "$PROJECT_ROOT"

echo "Starting data hygiene check at $(date)..."
echo "Project root: $PROJECT_ROOT"

# Ensure the state directory exists
mkdir -p state

# Run the Python data hygiene module
# The main() function in src/data_hygiene.py handles:
# 1. Calculating SHA256 checksums for all files in data/
# 2. Updating state/checksums.json
python code/src/data_hygiene.py

if [ $? -eq 0 ]; then
    echo "Data hygiene check completed successfully."
    echo "Checksums written to state/checksums.json"
else
    echo "ERROR: Data hygiene check failed."
    exit 1
fi
