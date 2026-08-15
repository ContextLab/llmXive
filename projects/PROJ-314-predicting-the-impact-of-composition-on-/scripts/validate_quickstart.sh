#!/bin/bash
# Validate the quickstart guide against the implemented pipeline

set -e

echo "Validating pipeline artifacts..."

# Check required directories
required_dirs=("data/raw" "data/processed" "data/artifacts" "data/results" "data/models" "data/reports" "logs")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "ERROR: Missing directory: $dir"
        exit 1
    fi
done

# Check required files
required_files=(
    "data/processed/step_final_cleaned.csv"
    "data/models/best_model.pkl"
    "data/results/model_metrics.json"
    "data/results/baseline_metrics.json"
    "data/results/feature_ranking_table.csv"
    "data/results/stability_metrics.json"
    "data/artifacts/shap_summary.png"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "WARNING: Missing file: $file"
    fi
done

echo "Validation complete."