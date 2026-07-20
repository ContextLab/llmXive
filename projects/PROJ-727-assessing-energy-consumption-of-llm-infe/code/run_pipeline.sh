#!/bin/bash
# run_pipeline.sh - Orchestrates the LLM Energy Assessment Pipeline
# This script verifies the environment, runs the dummy test, and exits with code 1 on failure.

set -e

echo "=========================================="
echo "LLM Energy Assessment Pipeline - Runner"
echo "=========================================="

# 1. Verify environment and run the dummy test (T008a)
echo "[Step 1/3] Verifying environment with dummy inference test..."
if ! python -m pytest tests/test_dummy.py::test_dummy_inference -v; then
    echo "ERROR: Environment verification failed. The dummy inference test did not pass."
    exit 1
fi
echo "Environment Verified: Dummy inference test passed."

# 2. Run the full pipeline (Inference -> Evaluation -> Aggregation -> Analysis -> Visualization)
# Note: The main entry point for the full pipeline is code/main.py which orchestrates the steps.
# However, based on the task dependencies, we explicitly run the modules if main.py is not the single entry point.
# Given the structure, we assume code/main.py handles the orchestration of the full flow.

echo "[Step 2/3] Running full pipeline (Inference, Evaluation, Analysis, Visualization)..."

# Check if data/raw directory exists (T009 prerequisite)
if [ ! -d "data/raw" ]; then
    echo "ERROR: data/raw directory does not exist. Run T005/T009 first."
    exit 1
fi

# Run the main pipeline script
# We assume the user has installed requirements. 
# If T013, T014, T016, T021, T027 etc. are implemented, main.py should call them.
# If main.py is not fully implemented yet, we run the specific modules sequentially to ensure progress.

# 2a. Inference (T013)
echo "  -> Running Inference..."
python code/inference.py || { echo "ERROR: Inference failed."; exit 1; }

# 2b. Evaluation (T014)
echo "  -> Running Evaluation..."
python code/evaluation.py || { echo "ERROR: Evaluation failed."; exit 1; }

# 2c. Aggregation (T016)
echo "  -> Running Aggregation..."
python code/main.py || { echo "ERROR: Aggregation failed."; exit 1; }

# 2d. Analysis (T021, T022, T023, T024)
echo "  -> Running Statistical Analysis..."
python code/analysis.py || { echo "ERROR: Analysis failed."; exit 1; }

# 2e. Visualization (T027, T028, T029)
echo "  -> Running Visualization..."
python code/visualization.py || { echo "ERROR: Visualization failed."; exit 1; }

echo "[Step 3/3] Pipeline completed successfully."
echo "=========================================="
echo "All artifacts generated in data/processed/"
echo "=========================================="

exit 0
