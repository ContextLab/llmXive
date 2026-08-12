#!/bin/bash
#
# run_pipeline.sh
# Orchestration script for the Avian Foraging Behavior Prediction Pipeline.
#
# This script executes the full research pipeline in the correct order:
# 1. Data Download (EBD, NLCD)
# 2. Data Processing (Merge, Buffer, Aggregate)
# 3. Model Training & Evaluation
# 4. Visualization & Reporting
#
# Usage: bash run_pipeline.sh
#
# Exit codes:
#   0 - All steps completed successfully
#   1 - One or more steps failed
#

set -e  # Exit immediately if a command exits with a non-zero status

# Determine the directory where this script resides
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================"
echo "Starting Avian Foraging Pipeline"
echo "Working directory: $(pwd)"
echo "========================================"
echo ""

# Helper function to run a step
run_step() {
    local step_name="$1"
    local command="$2"
    echo "----------------------------------------"
    echo "STEP: $step_name"
    echo "COMMAND: $command"
    echo "----------------------------------------"
    eval "$command"
    echo "[$step_name] Completed successfully."
    echo ""
}

# 1. Data Download
run_step "Download EBD Data" "python data/download_ebd.py"
run_step "Download NLCD Data" "python data/download_nlcd.py"

# 2. Data Processing
# Part A: Merge and calculate land cover proportions
run_step "Merge and Buffer (Part A)" "python data/merge_and_buffer.py --part A"
# Part B: Assign foraging guilds
run_step "Merge and Buffer (Part B)" "python data/merge_and_buffer.py --part B"
# Aggregate observations to species level
run_step "Aggregate Data" "python data/aggregate.py"

# 3. Model Training & Evaluation
run_step "Train Model" "python models/train.py"
run_step "Evaluate Model" "python models/evaluate.py"

# 4. Visualization & Reporting
run_step "Plot Confusion Matrix" "python viz/plot_confusion.py"
run_step "Plot Feature Importance" "python viz/plot_importance.py"
run_step "Map Habitat" "python viz/map_habitat.py"

echo "========================================"
echo "Pipeline Execution Complete"
echo "========================================"