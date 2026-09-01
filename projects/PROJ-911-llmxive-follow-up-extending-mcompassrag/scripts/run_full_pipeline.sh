#!/bin/bash
set -e

echo "=== Starting Full Pipeline Reproducibility Validation ==="
echo "Project: PROJ-911-llmxive-follow-up-extending-mcompassrag"
echo "Task: T037"
echo ""

# 1. Setup
echo "[1/6] Setting up directories..."
python code/setup_data_dirs.py

echo "[2/6] Loading and sampling real data..."
python code/data_loader.py

# 2. US1: Graph Construction
echo "[3/6] Building fixed vocabulary..."
python code/vocabulary_builder.py

echo "[4/6] Constructing graphs and extracting features..."
python code/graph_builder.py
python code/topology_extractor.py

# 3. US2: Retrieval Simulation
echo "[5/6] Running Neural Baseline and Retrieval Simulation..."
python code/neural_baseline.py
python code/retrieval_sim.py

# 4. US3: Analysis
echo "[6/6] Calculating correlations and validating success criteria..."
python code/evaluator.py
python code/final_metrics_writer.py
python code/validate_success_criteria.py

echo ""
echo "=== Pipeline Execution Complete ==="
echo "Verifying artifacts..."

# Simple verification
if [ -f "data/results/metrics.json" ] && [ -f "data/results/correlation.csv" ] && [ -f "data/processed/features.csv" ]; then
    echo "SUCCESS: All critical artifacts generated."
    exit 0
else
    echo "FAILURE: Missing critical artifacts."
    exit 1
fi
