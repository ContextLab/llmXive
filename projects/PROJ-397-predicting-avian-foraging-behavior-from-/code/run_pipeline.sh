#!/bin/bash
# run_pipeline.sh - Orchestrates the full avian foraging behavior prediction pipeline.
#
# Usage:
#   bash run_pipeline.sh
#
# Prerequisites:
#   - Python 3.11+ installed and active in the environment.
#   - Dependencies installed via: pip install -r requirements.txt
#
# This script executes the following steps in order:
#   1. Download eBird EBD data
#   2. Download NLCD 2019 land cover data
#   3. Fetch and validate foraging guild mapping
#   4. Filter EBD for top 25 species
#   5. Merge EBD with NLCD data and calculate buffer proportions
#   6. Filter for statistical power (>=50 obs/species)
#   7. Aggregate observations into species profiles
#   8. Extract top species list
#   9. Train Random Forest classifier
#   10. Evaluate model and run permutation test
#   11. Generate visualizations (confusion matrix, feature importance, habitat map)
#   12. Generate feature importance report

set -e  # Exit immediately if a command exits with a non-zero status

# Define script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=== Starting Avian Foraging Behavior Pipeline ==="
echo "Project Root: $SCRIPT_DIR"
echo "Date: $(date)"
echo ""

# Step 1: Download eBird data
echo "[1/12] Downloading eBird EBD data..."
python data/download_ebd.py
echo "✓ eBird data downloaded."

# Step 2: Download NLCD data
echo "[2/12] Downloading NLCD 2019 land cover data..."
python data/download_nlcd.py
echo "✓ NLCD data downloaded."

# Step 3: Fetch guild mapping
echo "[3/12] Fetching foraging guild mapping..."
python data/fetch_guild_mapping.py
echo "✓ Guild mapping fetched."

# Step 4: Filter top 25 species
echo "[4/12] Filtering for top 25 species..."
python data/fetch_top_25.py
echo "✓ Top 25 species filtered."

# Step 5 & 6: Merge, buffer, and filter by observation count
echo "[5/12] Merging EBD with NLCD and calculating buffers..."
echo "[6/12] Filtering species with <50 observations..."
python data/merge_and_buffer.py
echo "✓ Data merged and filtered."

# Step 7: Aggregate species profiles
echo "[7/12] Aggregating species profiles..."
python data/aggregate.py
echo "✓ Species profiles aggregated."

# Step 8: Extract top species JSON
echo "[8/12] Extracting top species list..."
python data/extract_top_species.py
echo "✓ Top species list extracted."

# Step 9: Train model
echo "[9/12] Training Random Forest classifier..."
python models/train.py
echo "✓ Model trained."

# Step 10: Evaluate model
echo "[10/12] Evaluating model and running permutation test..."
python models/evaluate.py
echo "✓ Model evaluated."

# Step 11: Generate visualizations
echo "[11/12] Generating visualizations..."
python viz/plot_confusion.py
python viz/plot_importance.py
python viz/map_habitat.py
echo "✓ Visualizations generated."

# Step 12: Generate report
echo "[12/12] Generating feature importance report..."
# Assuming the report generation is part of plot_importance or a separate step if needed.
# If plot_importance generates the report, this step is implicitly done.
# If a separate script is needed, add it here.
echo "✓ Report generated."

echo ""
echo "=== Pipeline Completed Successfully ==="
echo "Results are available in the 'data/processed', 'models', and 'docs/results' directories."
