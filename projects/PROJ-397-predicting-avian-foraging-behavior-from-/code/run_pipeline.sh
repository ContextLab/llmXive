#!/bin/bash
set -e

echo "Starting Avian Foraging Behavior Pipeline..."

# Ensure we are in the code directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Step 1: Download EBD Data"
python data/download_ebd.py

echo "Step 2: Download NLCD Data"
python data/download_nlcd.py

echo "Step 3: Fetch Guild Mapping"
python data/fetch_guild_mapping.py

echo "Step 4: Filter Top 25 Species"
python data/filter_top_25.py

echo "Step 5: Merge and Buffer"
python data/merge_and_buffer.py

echo "Step 6: Aggregate Profiles"
python data/aggregate.py

echo "Step 7: Extract Top Species"
python data/extract_top_species.py

echo "Step 8: Train Model"
python models/train.py

echo "Step 9: Evaluate Model"
python models/evaluate.py

echo "Step 10: Plot Confusion Matrix"
python viz/plot_confusion.py

echo "Step 11: Plot Feature Importance"
python viz/plot_importance.py

echo "Step 12: Map Habitat"
python viz/map_habitat.py

echo "Pipeline completed successfully."
