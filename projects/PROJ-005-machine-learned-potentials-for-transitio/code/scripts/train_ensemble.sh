#!/bin/bash
# T023b: Orchestration script to launch parallel training jobs for the ensemble.
# This script spawns 5 independent training processes, each with a distinct random seed.
# It relies on the implementation in `code/src/models/ensemble.py` (T023a) and `code/src/models/schnet.py` (T022).

set -e

# Configuration
NUM_MODELS=5
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/venv"
SCRIPT_DIR="${PROJECT_ROOT}/scripts"
LOG_DIR="${PROJECT_ROOT}/logs"

# Ensure directories exist
mkdir -p "${LOG_DIR}"
mkdir -p "${PROJECT_ROOT}/data/processed/models"

echo "=========================================="
echo "Starting Ensemble Training Orchestration"
echo "=========================================="
echo "Project Root: ${PROJECT_ROOT}"
echo "Number of Models: ${NUM_MODELS}"
echo "Output Directory: ${PROJECT_ROOT}/data/processed/models"
echo "Log Directory: ${LOG_DIR}"
echo "=========================================="

# Activate virtual environment
if [ -d "${VENV_DIR}" ]; then
    source "${VENV_DIR}/bin/activate"
    echo "Virtual environment activated."
else
    echo "ERROR: Virtual environment not found at ${VENV_DIR}. Please run setup.sh first."
    exit 1
fi

# Launch training jobs in parallel
# Each job runs the main entry point of ensemble.py with a specific seed
# The python script handles the actual training loop, model saving, and logging.

echo "Launching ${NUM_MODELS} parallel training processes..."

# We use an array to hold PIDs for optional monitoring or waiting
pids=()

for i in $(seq 0 $((NUM_MODELS - 1))); do
    SEED=$((1000 + i)) # Distinct seeds: 1000, 1001, 1002, 1003, 1004
    LOG_FILE="${LOG_DIR}/train_seed_${SEED}.log"
    
    echo "  [Job ${i}] Starting model training with seed ${SEED}..."
    echo "  [Job ${i}] Log file: ${LOG_FILE}"
    
    # Launch the training script in the background
    # We pass the seed as an environment variable or argument. 
    # The ensemble.py main function is designed to read config or args.
    # Here we assume the script reads from a config or default args, 
    # but we can override the seed via environment variable if needed.
    # To be robust, we call the script which internally handles the seed logic 
    # or we pass it as an argument if the main function supports it.
    # Based on T023a/T024 requirements, the script should handle the seed.
    
    python "${SCRIPT_DIR}/run_ensemble_training.py" --seed ${SEED} > "${LOG_FILE}" 2>&1 &
    pids+=($!)
done

echo "All ${NUM_MODELS} jobs launched. Waiting for completion..."
echo "------------------------------------------"

# Wait for all background processes to complete
failed=0
for pid in "${pids[@]}"; do
    if ! wait ${pid}; then
        echo "ERROR: Job with PID ${pid} failed."
        failed=1
    fi
done

echo "------------------------------------------"
if [ ${failed} -eq 0 ]; then
    echo "SUCCESS: All ${NUM_MODELS} training jobs completed successfully."
    echo "Check logs in ${LOG_DIR} for details."
    echo "Models saved to ${PROJECT_ROOT}/data/processed/models/"
else
    echo "FAILURE: One or more training jobs failed. Check logs in ${LOG_DIR}."
    exit 1
fi

# Deactivate virtual environment (optional, good practice)
# deactivate

echo "=========================================="
echo "Orchestration Complete"
echo "=========================================="
