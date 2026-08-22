#!/bin/bash
# hash_artifacts.sh
# Generates SHA256 checksums for all files in data/configs, data/results, data/logs, and state.
# Satisfies Constitution Principle III (Data Hygiene) and V (Versioning Discipline).

set -e

# Project root is the parent of the scripts directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MANIFEST_FILE="$PROJECT_ROOT/state/checksums.json"

echo "Running checksum generation for project: $PROJECT_ROOT"

# Ensure the state directory exists
mkdir -p "$PROJECT_ROOT/state"

# Run the Python script to generate the manifest
# We use python3 explicitly to ensure the correct environment
python3 -m src.utils.checksum generate --output "$MANIFEST_FILE"

if [ -f "$MANIFEST_FILE" ]; then
    echo "SUCCESS: Checksums generated and saved to $MANIFEST_FILE"
    exit 0
else
    echo "FAILURE: Checksum manifest was not created."
    exit 1
fi
