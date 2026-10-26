#!/usr/bin/env bash
set -e

echo "=== Step 1: Download raw data ==="
python code/data/download.py

echo "=== Step 2: Preprocess data ==="
python code/data/preprocess.py

echo "=== Step 3: Create train/test split ==="
python code/data/split.py

echo "=== Step 4: Train models (GNN + RF) ==="
python code/analysis/train.py --config config.yaml

echo "=== Step 5: Evaluate models ==="
python code/analysis/evaluate.py

echo "=== Step 6: Statistical tests ==="
python code/analysis/statistical_tests.py

echo "=== Step 7: Explainability ==="
python code/analysis/explain.py

echo "=== Step 8: Generate report ==="
python code/analysis/comparative_report.py

echo "=== Step 9: Verify metrics ==="
python code/utils/verify_metrics.py

echo "=== Pipeline completed successfully ==="