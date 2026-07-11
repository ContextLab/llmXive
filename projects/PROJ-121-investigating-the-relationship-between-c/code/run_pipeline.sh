#!/bin/bash
# run_pipeline.sh - Wrapper script for the cosmic ray anisotropy pipeline
#
# This script orchestrates the execution of src/pipeline.py with configurable
# bin size parameters. It handles argument parsing, environment setup, and
# provides a clean interface for running the full data analysis pipeline.
#
# Usage:
#   ./run_pipeline.sh [OPTIONS]
#
# Options:
#   --bin-size N    Set the temporal bin size in days (default: 27)
#   --help          Display this help message
#
# Environment Variables:
#   DATA_DIR        Base directory for data storage (default: data/)
#   LOG_LEVEL       Logging level (default: INFO)
#   PYTHONPATH      Must include the code/ directory

set -e  # Exit on error

# Default values
BIN_SIZE=27
DATA_DIR="${DATA_DIR:-data}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_DIR="${SCRIPT_DIR}/code"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --bin-size)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "Error: --bin-size requires a numeric argument" >&2
                exit 1
            fi
            BIN_SIZE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--bin-size N] [--help]"
            echo ""
            echo "Options:"
            echo "  --bin-size N    Set the temporal bin size in days (default: 27)"
            echo "  --help          Display this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DATA_DIR        Base directory for data storage (default: data/)"
            echo "  LOG_LEVEL       Logging level (default: INFO)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Validate bin size is numeric
if ! [[ "$BIN_SIZE" =~ ^[0-9]+$ ]]; then
    echo "Error: bin-size must be a positive integer" >&2
    exit 1
fi

# Set PYTHONPATH to include the code directory
export PYTHONPATH="${CODE_DIR}:${PYTHONPATH}"

# Change to the code directory to ensure relative paths work correctly
cd "${CODE_DIR}"

# Log the execution start
echo "=============================================="
echo "Cosmic Ray Anisotropy Pipeline"
echo "=============================================="
echo "Bin Size: ${BIN_SIZE} days"
echo "Data Directory: ${DATA_DIR}"
echo "Log Level: ${LOG_LEVEL}"
echo "Execution Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=============================================="

# Execute the pipeline with the specified parameters
python src/pipeline.py \
    --bin-size "${BIN_SIZE}" \
    --data-dir "${DATA_DIR}" \
    --log-level "${LOG_LEVEL}"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "=============================================="
    echo "Pipeline execution completed successfully"
    echo "=============================================="
else
    echo "=============================================="
    echo "Pipeline execution failed with exit code: ${EXIT_CODE}"
    echo "=============================================="
fi

exit $EXIT_CODE