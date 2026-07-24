#!/bin/bash
set -e

echo "Starting llmXive Code Complexity Pipeline"

# 1. Setup (if needed)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# 2. Ingest Data
echo "Step 1: Ingesting Defects4J data..."
python code/src/ingest.py

# 3. Extract Metrics
echo "Step 2: Extracting Metrics (LOC, CC, Halstead)..."
python code/src/metrics.py
python code/src/metrics_pmd.py
python code/src/metrics_halstead.py

# 4. Label Data
echo "Step 3: Labeling bug files..."
python code/src/labeling.py

# 5. Generate Features
echo "Step 4: Generating features.csv..."
python code/src/generate_features.py

echo "Pipeline complete. Check code/data/processed/features.csv"
