#!/bin/bash
# Orchestrator for the full data pipeline
# Downloads data, bins events, generates HEALPix maps, and outputs dipole CSVs

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CODE_DIR="${SCRIPT_DIR}/code"

echo "Starting Cosmic Ray Anisotropy Pipeline..."
echo "Working directory: ${CODE_DIR}"

# Run the main pipeline script
python "${CODE_DIR}/src/pipeline.py" --bin-size 27

echo "Data acquisition completed."
echo "Results written to data/results/dipole_timeseries.csv"
