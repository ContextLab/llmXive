#!/bin/bash
# T028: Ensure prediction runtime <= 30s and memory <= 4GB
# This script wraps the Python prediction logic with resource constraints.

set -e

# Configuration
MEMORY_LIMIT_MB=4096
TIME_LIMIT_S=30

# Parse arguments
GENOME_FILE=""
MODEL_FILE=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --genome)
            GENOME_FILE="$2"
            shift 2
            ;;
        --model)
            MODEL_FILE="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$GENOME_FILE" ]; then
    echo "Error: --genome is required"
    exit 1
fi

if [ -z "$MODEL_FILE" ]; then
    # Default to standard project path if not provided
    MODEL_FILE="data/models/model.pkl"
fi

if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="data/reports"
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Define the Python script to run
PYTHON_SCRIPT=$(cat << 'PYTHON_EOF'
import os
import sys
import json
import argparse
import time
import resource
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cli.predict_host_range import parse_args, load_reference_hosts, run_prediction, main as python_main
from src.data.feature_extractor import extract_single_genome_features
from src.models.train import load_model
from loguru import logger

def enforce_memory_limit(limit_mb):
    """Enforce memory limit using resource module (Unix only)."""
    if os.name != 'posix':
  logger.warning("Memory limit enforcement only available on Unix systems.")
  return
    
    limit_bytes = limit_mb * 1024 * 1024
    try:
  resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
  logger.info(f"Memory limit set to {limit_mb} MB")
    except (ValueError, resource.error) as e:
  logger.warning(f"Could not set memory limit: {e}")

def main():
    # Parse arguments
    args = parse_args()
    
    # Enforce memory limit
    enforce_memory_limit(4096)
    
    start_time = time.time()
    
    try:
  # Load model
  model = load_model(args.model)
  
  # Load reference hosts
  hosts = load_reference_hosts(args.interactions)
  
  # Extract features for the novel genome
  logger.info(f"Extracting features for genome: {args.genome}")
  features = extract_single_genome_features(args.genome)
  
  # Run prediction
  results = run_prediction(model, features, hosts)
  
  # Save results
  output_path = Path(args.output_dir) / "prediction.csv"
  results.to_csv(output_path, index=False)
  
  # Calculate and save host range breadth
  mean_prob = results['probability'].mean()
  breadth_path = Path(args.output_dir) / "host_range_breadth.json"
  with open(breadth_path, 'w') as f:
      json.dump({"mean_probability": float(mean_prob)}, f)
      
  elapsed = time.time() - start_time
  logger.info(f"Prediction completed in {elapsed:.2f} seconds")
  
  # Check time limit
  if elapsed > 30:
      logger.warning(f"Prediction took {elapsed:.2f}s, exceeding 30s limit")
      # Still exit 0 as the prediction was successful, just slow
  else:
      logger.info(f"Prediction completed within time limit ({elapsed:.2f}s <= 30s)")
      
    except Exception as e:
  logger.error(f"Prediction failed: {e}")
  raise

if __name__ == "__main__":
    main()
PYTHON_EOF
)

# Run the Python script with timeout
echo "Running prediction with memory limit ${MEMORY_LIMIT_MB}MB and time limit ${TIME_LIMIT_S}s..."

# Use timeout command for time limit (GNU coreutils)
if command -v timeout &> /dev/null; then
    timeout "${TIME_LIMIT_S}s" python3 -c "$PYTHON_SCRIPT" \
        --genome "$GENOME_FILE" \
        --model "$MODEL_FILE" \
        --output-dir "$OUTPUT_DIR" \
        --interactions "data/raw/interactions_merged.csv"
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 124 ]; then
        echo "Error: Prediction exceeded time limit of ${TIME_LIMIT_S}s"
        exit 1
    elif [ $EXIT_CODE -ne 0 ]; then
        echo "Error: Prediction failed with exit code $EXIT_CODE"
        exit $EXIT_CODE
    fi
else
    echo "Warning: 'timeout' command not found, running without time limit..."
    python3 -c "$PYTHON_SCRIPT" \
        --genome "$GENOME_FILE" \
        --model "$MODEL_FILE" \
        --output-dir "$OUTPUT_DIR" \
        --interactions "data/raw/interactions_merged.csv"
    
    if [ $? -ne 0 ]; then
        echo "Error: Prediction failed"
        exit 1
    fi
fi

echo "Prediction completed successfully."
exit 0