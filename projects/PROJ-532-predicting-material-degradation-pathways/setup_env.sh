#!/bin/bash
# Setup script to configure environment variables for the project.
# Source this file: `source setup_env.sh`

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)"
export DEGRADATION_DATASET_URL="https://zenodo.org/api/records/12345/files/corrosion_data.csv"
export RANDOM_SEED=42
export LOG_LEVEL="INFO"

echo "Environment configured. PYTHONPATH set to include current directory."