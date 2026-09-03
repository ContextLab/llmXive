#!/bin/bash
# Script to delete consolidated files after verifying imports are updated
# This script is run as part of the T1214 verification step

set -e

echo "Checking for consolidated files..."

FILES_TO_DELETE=(
    "code/cleanup_utils.py"
    "code/profiler.py"
)

for file in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        echo "Deleting $file..."
        rm "$file"
        echo "Deleted $file"
    else
        echo "$file does not exist (already deleted or never existed)"
    fi
done

echo "Consolidation cleanup complete."
echo "Note: The stub files were kept in this task to allow import testing."
echo "Run this script after updating all imports to remove the stub files."