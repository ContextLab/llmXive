#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------------------------------------
# Deterministic seeds
# ----------------------------------------------------------------------
export PYTHONHASHSEED=0
python - <<PY
import random, numpy as np, torch
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
PY

# ----------------------------------------------------------------------
# Pipeline steps (order respects data flow)
# ----------------------------------------------------------------------
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

echo "=== Step 6: Explainability analysis ==="
python code/analysis/explain.py

# ----------------------------------------------------------------------
# Hand‑off document
# ----------------------------------------------------------------------
RESULTS_MD=$(paths.results "results.md")
cat > "$RESULTS_MD" <<EOF
# Pipeline Run Summary

- **Dataset source**: \`data/raw/permeability_data.csv\`
- **Processed data**: \`data/processed/processed_data.parquet\`
- **Train / Test splits**: \`data/processed/train.parquet\`, \`data/processed/test.parquet\`
- **GNN checkpoint**: \`code/models/gnn.pt\`
- **Random Forest model**: \`code/models/rf.pkl\`
- **Metrics**: \`results/metrics.json\`
- **Interpretability artifacts**: \`results/interpretability/*\`
EOF

echo "Pipeline completed successfully. Summary written to $RESULTS_MD"
