#!/bin/bash
#
# run_pipeline.sh
# Wrapper script to execute the cosmic ray anisotropy pipeline.
#
# Usage:
#   ./run_pipeline.sh [--bin-size <days>]
#
# Default bin size is 27 days (as per spec).
#

set -e

# Default configuration
DEFAULT_BIN_SIZE=27
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$PROJECT_ROOT/code/src/pipeline.py"

# Parse arguments
BIN_SIZE=$DEFAULT_BIN_SIZE
if [ "$#" -gt 0 ]; then
    if [ "$1" == "--bin-size" ]; then
        if [ -z "$2" ]; then
            echo "Error: --bin-size requires an integer argument."
            exit 1
        fi
        BIN_SIZE=$2
        # Validate argument is an integer
        if ! [[ "$BIN_SIZE" =~ ^[0-9]+$ ]]; then
            echo "Error: --bin-size argument must be a positive integer."
            exit 1
        fi
        shift 2
    else
        echo "Error: Unknown argument '$1'"
        echo "Usage: $0 [--bin-size <days>]"
        exit 1
    fi
fi

echo "Starting Cosmic Ray Anisotropy Pipeline..."
echo "Bin size: $BIN_SIZE days"
echo "Working directory: $PROJECT_ROOT"

# Change to project root to ensure relative paths in pipeline.py work correctly
cd "$PROJECT_ROOT"

# Execute the pipeline
python3 "$PYTHON_SCRIPT" --bin-size "$BIN_SIZE"

if [ $? -eq 0 ]; then
    echo "Pipeline completed successfully."
    echo "Results are available in data/results/"
else
    echo "Pipeline execution failed."
    exit 1
fi