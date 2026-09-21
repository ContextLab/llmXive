#!/bin/bash
# CI Script for PROJ-342: Predicting the Influence of Alloying on Tg
# Executes the full pipeline and verifies all artifacts

set -e

echo "========================================"
echo "PROJ-342 CI Pipeline"
echo "========================================"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
export RANDOM_SEED=42
export RUNTIME_LIMIT_H=6
export MEMORY_LIMIT_GB=7

# Create necessary directories
mkdir -p data/raw data/processed artifacts/models artifacts/metrics artifacts/reports logs state/projects

echo "Running full pipeline..."
python code/run_full_pipeline.py

echo "Verifying artifacts..."
if [ ! -f "data/processed/cleaned_mg.csv" ]; then
    echo "ERROR: data/processed/cleaned_mg.csv not found"
    exit 1
fi

if [ ! -f "artifacts/models/best_model.pkl" ]; then
    echo "ERROR: artifacts/models/best_model.pkl not found"
    exit 1
fi

if [ ! -f "artifacts/reports/final_report.md" ]; then
    echo "ERROR: artifacts/reports/final_report.md not found"
    exit 1
fi

# Check for mandatory phrase in report
if ! grep -q "These findings are associational only" artifacts/reports/final_report.md; then
    echo "ERROR: Mandatory phrase not found in final report"
    exit 1
fi

# Check for causal language
if grep -qiE "(causes|determines|leads to|results in|proves|confirms|guarantees)" artifacts/reports/final_report.md; then
    echo "ERROR: Causal language detected in final report"
    exit 1
fi

echo "========================================"
echo "✅ CI Pipeline Passed Successfully!"
echo "========================================"
echo "Artifacts generated:"
echo "  - data/processed/cleaned_mg.csv"
echo "  - artifacts/models/best_model.pkl"
echo "  - artifacts/reports/final_report.md"
echo "========================================"

exit 0
