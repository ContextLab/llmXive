#!/bin/bash
# run_pipeline.sh - CLI entry point for the Plant Pathogen Host Range Prediction Pipeline
# Usage: ./run_pipeline.sh --data-dir ./data --mode primary --seed 42

set -e

# Default values
DATA_DIR="./data"
MODE="primary"
SEED=42
FULL_DATASET=false
CONFIG=""

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
        --full-dataset)
            FULL_DATASET=true
            shift
            ;;
        --config)
            CONFIG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "Error: Data directory $DATA_DIR does not exist."
    exit 1
fi

# Check for required files
if [ ! -f "$DATA_DIR/raw/interactions_merged.csv" ]; then
    echo "Error: Interactions file not found. Run T009A first."
    exit 1
fi

if [ ! -f "$DATA_DIR/processed/valid_pathogens.json" ]; then
    echo "Error: Valid pathogens file not found. Run T010C first."
    exit 1
fi

echo "Starting Pipeline..."
echo "Data Dir: $DATA_DIR"
echo "Mode: $MODE"
echo "Seed: $SEED"

# Execute Python script
python -m src.cli.run_pipeline \
    --data-dir "$DATA_DIR" \
    --mode "$MODE" \
    --seed "$SEED" \
    ${CONFIG:+--config "$CONFIG"} \
    ${FULL_DATASET:+--full-dataset}

echo "Pipeline execution finished."
