#!/bin/bash
#
# run_pipeline.sh - Orchestration script for the Avian Foraging Behavior Prediction Pipeline
#
# This script executes all pipeline steps in dependency order:
# 1. Data Download (EBD, NLCD, Guild Source)
# 2. Data Processing (Selection, Merging, Aggregation)
# 3. Model Training and Evaluation
# 4. Visualization and Reporting
#
# Usage: bash run_pipeline.sh
#

set -e  # Exit on any error

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Avian Foraging Behavior Prediction Pipeline"
echo "=========================================="
echo "Starting pipeline execution at $(date)"
echo ""

# --- PHASE 1: Data Download ---
echo "[PHASE 1] Data Download"
echo "------------------------"

echo "Step 1.1: Download eBird EBD data..."
python data/download_ebd.py
echo "eBird data downloaded."

echo "Step 1.2: Download NLCD 2019 land cover data..."
python data/download_nlcd.py
echo "NLCD data downloaded."

echo "Step 1.3: Download Birds of the World guild source data..."
python data/download_guild_source.py
echo "Guild source data downloaded."

echo "Step 1.4: Generate guild mapping from source..."
python data/generate_guild_mapping.py
echo "Guild mapping generated."

echo "Step 1.5: Record NLCD provenance..."
python data/record_nlcd_provenance.py
echo "NLCD provenance recorded."

echo ""

# --- PHASE 2: Data Processing ---
echo "[PHASE 2] Data Processing"
echo "-------------------------"

echo "Step 2.1: Select top species (>=50 obs)..."
python data/select_top_species.py
echo "Top species selected."

echo "Step 2.2: Merge observations with land cover and assign guilds..."
python data/merge_and_buffer.py
echo "Data merged and buffered."

echo "Step 2.3: Aggregate observations to species profiles..."
python data/aggregate.py
echo "Data aggregated."

echo "Step 2.4: Extract top 25 species for visualization..."
python data/extract_top_species.py
echo "Top species extracted for visualization."

echo ""

# --- PHASE 3: Model Training and Evaluation ---
echo "[PHASE 3] Model Training and Evaluation"
echo "---------------------------------------"

echo "Step 3.1: Train Random Forest classifier..."
python models/train.py
echo "Model trained."

echo "Step 3.2: Evaluate model and run permutation test..."
python models/evaluate.py
echo "Model evaluated."

echo ""

# --- PHASE 4: Visualization and Reporting ---
echo "[PHASE 4] Visualization and Reporting"
echo "-------------------------------------"

echo "Step 4.1: Generate confusion matrix..."
python viz/plot_confusion.py
echo "Confusion matrix generated."

echo "Step 4.2: Generate feature importance chart and report..."
python viz/plot_importance.py
echo "Feature importance chart and report generated."

echo "Step 4.3: Validate feature importance against literature..."
python viz/validate_importance.py
echo "Feature importance validated."

echo "Step 4.4: Generate spatial habitat map..."
python viz/map_habitat.py
echo "Spatial habitat map generated."

echo ""
echo "=========================================="
echo "Pipeline execution completed successfully!"
echo "Finished at $(date)"
echo "=========================================="