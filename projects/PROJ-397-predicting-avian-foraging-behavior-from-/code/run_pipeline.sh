#!/bin/bash
# Orchestrates the full avian foraging prediction pipeline

set -e  # Stop on first error

echo "Starting Avian Foraging Pipeline..."

# Phase 1: Data Download
echo "Phase 1: Downloading data..."
python code/data/download_ebd.py
python code/data/download_nlcd.py
python code/data/download_guild_source.py

# Phase 2: Data Processing
echo "Phase 2: Processing data..."
python code/data/generate_guild_mapping.py
python code/data/select_top_species.py
python code/data/merge_and_buffer.py
python code/data/aggregate.py

# Phase 3: Model Training & Evaluation
echo "Phase 3: Training and evaluating models..."
python code/models/train.py
python code/models/evaluate.py

# Phase 4: Visualization
echo "Phase 4: Generating visualizations..."
python code/viz/plot_confusion.py
python code/viz/plot_importance.py
python code/viz/map_habitat.py

echo "Pipeline completed successfully!"