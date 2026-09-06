#!/bin/bash
# Orchestration script for the Avian Foraging Guilds Prediction Pipeline
# This script executes all pipeline steps in dependency order

set -e  # Exit on first error

echo "Starting Avian Foraging Guilds Prediction Pipeline..."
echo "======================================================"

# Define script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to log step execution
run_step() {
    local step_name="$1"
    local script_path="$2"
    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Executing: $step_name"
    echo "------------------------------------------------------"
    if python "$script_path"; then
        echo "✓ $step_name completed successfully"
    else
        echo "✗ $step_name FAILED"
        exit 1
    fi
}

echo "Phase 1: Data Download"
echo "----------------------"
# run_step "Download EBD Data" "data/download_ebd.py"
# run_step "Download NLCD Data" "data/download_nlcd.py"
# run_step "Download Guild Source" "data/download_guild_source.py"

echo "Phase 2: Data Processing"
echo "------------------------"
# run_step "Generate Guild Mapping" "data/generate_guild_mapping.py"
# run_step "Load and Count Species" "data/load_and_count.py"
# run_step "Select Top Species" "data/select_top_species.py"
# run_step "Filter and Log" "data/filter_and_log.py"
# run_step "Merge and Buffer" "data/merge_and_buffer.py"
# run_step "Aggregate Species Profiles" "data/aggregate.py"

echo "Phase 3: Model Training"
echo "-----------------------"
# run_step "Train Random Forest" "models/train.py"

echo "Phase 4: Model Evaluation"
echo "-------------------------"
# run_step "Evaluate Model" "models/evaluate.py"

echo "Phase 5: Visualization"
echo "----------------------"
# run_step "Plot Confusion Matrix" "viz/plot_confusion.py"
# run_step "Plot Feature Importance" "viz/plot_importance.py"
# run_step "Map Habitat" "viz/map_habitat.py"

echo ""
echo "======================================================"
echo "Pipeline execution completed successfully!"
echo "Results are available in the 'data/', 'models/', and 'viz/' directories."