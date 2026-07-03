#!/bin/bash
# Orchestration script for the Avian Foraging Behavior Prediction Pipeline
# Executes the full data processing, modeling, and visualization workflow.
#
# Usage: bash run_pipeline.sh
#
# Prerequisites:
#   - Python 3.11+ installed
#   - Virtual environment activated with dependencies from requirements.txt
#   - Real data sources (eBird, NLCD) accessible via network

set -e  # Exit immediately if a command exits with a non-zero status

# Determine script directory to ensure relative paths work correctly
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Starting Avian Foraging Behavior Pipeline"
echo "=========================================="
echo "Working directory: $(pwd)"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "------------------------------------------"

# Step 1: Download eBird Data
echo "[1/7] Downloading eBird data..."
python data/download_ebd.py
echo "Step 1 complete."

# Step 2: Download NLCD Data
echo "[2/7] Downloading NLCD land cover data..."
python data/download_nlcd.py
echo "Step 2 complete."

# Step 3: Merge and Buffer
echo "[3/7] Merging data and calculating buffers..."
python data/merge_and_buffer.py
echo "Step 3 complete."

# Step 4: Train Model
echo "[4/7] Training Random Forest model..."
python models/train.py
echo "Step 4 complete."

# Step 5: Evaluate Model
echo "[5/7] Evaluating model performance..."
python models/evaluate.py
echo "Step 5 complete."

# Step 6: Plot Confusion Matrix
echo "[6/7] Generating confusion matrix visualization..."
python viz/plot_confusion.py
echo "Step 6 complete."

# Step 7: Plot Feature Importance
echo "[7/7] Generating feature importance chart..."
python viz/plot_importance.py
echo "Step 7 complete."

# Note: map_habitat.py is not included in the primary chain in tasks.md description
# but if needed, it would be run here. The tasks.md specific command list ends at plot_importance.
# If map_habitat is required by the user, uncomment the line below:
# echo "Generating habitat map..."
# python viz/map_habitat.py

echo "------------------------------------------"
echo "Pipeline completed successfully!"
echo "Check 'data/processed/' for datasets and 'figures/' for visualizations."
echo "=========================================="