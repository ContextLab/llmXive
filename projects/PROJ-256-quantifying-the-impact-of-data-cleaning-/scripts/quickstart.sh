#!/bin/bash
# Quickstart script for PROJ-256: Quantifying the Impact of Data Cleaning on Statistical Inference
# This script runs the full pipeline and validates results.

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

LOG_FILE="quickstart_run.log"
echo "Starting quickstart pipeline at $(date)" | tee "$LOG_FILE"

# 1. Ensure dependencies are installed
echo "Checking dependencies..." | tee -a "$LOG_FILE"
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found!" | tee -a "$LOG_FILE"
    exit 1
fi
pip install -q -r requirements.txt

# 2. Download and verify raw data (if not present)
echo "Ensuring raw data exists..." | tee -a "$LOG_FILE"
python -m code.data_loader

# 3. Run baseline analysis
echo "Running baseline analysis..." | tee -a "$LOG_FILE"
python -m code.main --stage baseline

# 4. Run cleaning pipeline
echo "Running cleaning pipeline..." | tee -a "$LOG_FILE"
python -m code.main --stage cleaning

# 5. Run permutation-based FPR estimation
echo "Running permutation-based FPR estimation..." | tee -a "$LOG_FILE"
python -m code.main --stage fpr

# 6. Run comparison and reporting
echo "Running comparison and reporting..." | tee -a "$LOG_FILE"
python -m code.main --stage report

# 7. Validate dataset bins (T1229)
echo "Validating dataset bins (T1229)..." | tee -a "$LOG_FILE"
python code/validate_dataset_bins.py

# 8. Final validation
echo "Running final validation..." | tee -a "$LOG_FILE"
python -m code.main --stage validate

echo "Quickstart pipeline completed successfully at $(date)" | tee -a "$LOG_FILE"
