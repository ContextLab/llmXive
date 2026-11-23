#!/bin/bash
# hash_artifacts.sh
# Generates SHA256 checksums for all files in data/configs, data/results, data/logs, and state.
# This script is a wrapper around the Python implementation in src/utils/checksum.py
# to ensure deterministic execution and compliance with Constitution Principle III & V.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

OUTPUT_FILE="$PROJECT_ROOT/state/checksums.json"

echo "Generating SHA256 checksums for project artifacts..."
echo "Project Root: $PROJECT_ROOT"
echo "Output File: $OUTPUT_FILE"

# Run the Python script to generate checksums
python "$PROJECT_ROOT/code/src/utils/checksum.py" --output "$OUTPUT_FILE"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Checksum generation successful."
    echo "Output saved to: $OUTPUT_FILE"
    
    # Verify the file exists and is non-empty
    if [ -s "$OUTPUT_FILE" ]; then
        echo "Verification: Output file exists and is non-empty."
        exit 0
    else
        echo "Error: Output file is empty."
        exit 1
    fi
else
    echo "Error: Checksum generation failed."
    exit 1
fi
