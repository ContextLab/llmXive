#!/bin/bash
set -e

echo "Starting Avian Foraging Behavior Pipeline..."

# Ensure we are in the code directory
cd "$(dirname "$0")"

# 1. Data Download
echo "Step 1: Downloading eBird EBD data..."
python data/download_ebd.py

echo "Step 2: Downloading NLCD 2019 data..."
python data/download_nlcd.py

# 2. Data Processing
echo "Step 3: Fetching guild mapping..."
python data/fetch_guild_mapping.py

echo "Step 4: Filtering top 25 species..."
python data/filter_top_25.py

echo "Step 5: Merging data and calculating buffers..."
python data/merge_and_buffer.py

echo "Step 6: Aggregating species profiles..."
python data/aggregate.py

echo "Step 7: Extracting top species JSON..."
python data/extract_top_species.py

# 3. Modeling
echo "Step 8: Training Random Forest model..."
python models/train.py

echo "Step 9: Evaluating model and running permutation test..."
python models/evaluate.py

# 4. Visualization
echo "Step 10: Plotting confusion matrix..."
python viz/plot_confusion.py

echo "Step 11: Plotting feature importance..."
python viz/plot_importance.py

echo "Step 12: Mapping habitat..."
python viz/map_habitat.py

echo "Pipeline completed successfully."
