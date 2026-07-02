#!/bin/bash
# Entry point for the Plant Pathogen Host Range Prediction Pipeline.
# Usage: ./run_pipeline.sh --data-dir ./data --mode primary --seed 42

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/code"

# Default values
DATA_DIR=""
MODE="primary"
SEED=42

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$DATA_DIR" ]; then
    echo "Error: --data-dir is required."
    exit 1
fi

echo "Starting Pipeline..."
echo "Data Dir: $DATA_DIR"
echo "Mode: $MODE"
echo "Seed: $SEED"

# Run the Python script
python "$PROJECT_ROOT/src/cli/run_pipeline.py" \
    --data-dir "$DATA_DIR" \
    --mode "$MODE" \
    --seed "$SEED"

echo "Pipeline execution finished."
