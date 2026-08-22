#!/bin/bash
# data-hygiene.sh
# Wrapper script to execute data hygiene checks and update state checksums.
# Implements Constitution Principle III by calling the Python implementation.

set -e  # Exit immediately if a command exits with a non-zero status

# Determine the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root to ensure relative paths in Python work correctly
cd "$PROJECT_ROOT"

# Execute the Python data hygiene module
# This will generate SHA256 checksums for all files in data/ 
# and write them to state/checksums.json
python code/src/data_hygiene.py

# Verify the output file was created
if [ ! -f "state/checksums.json" ]; then
    echo "ERROR: state/checksums.json was not created by data_hygiene.py" >&2
    exit 1
fi

echo "Data hygiene check completed successfully. Checksums written to state/checksums.json"
exit 0