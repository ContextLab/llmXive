# Quickstart: Running the Attention‑Sparsity Study

This guide assumes a fresh GitHub Actions runner or a local environment with the same resource limits (2 CPU cores, ≤ 7 GB RAM).

## 1. Clone the repository and navigate to the feature directory
```bash
git clone <REPO_URL>
cd specs/001-llmxive-follow-up
```

## 2. Install the exact dependencies
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r../../requirements.txt # repository‑wide pinned requirements
```

## 3. Set deterministic seeds (optional – defaults are already fixed)
```bash
export PYTHONHASHSEED=0
python - <<'PY'
import numpy as np, torch, random
np.random.seed(0)
torch.manual_seed(0)
random.seed(0)
PY
```

## 4. Run the sanity experiment (global attention, 5‑image sample)
```bash
python -m src.cli.run_experiment --config global --sample 5
```

This command will:
- Download the required raw datasets if they are missing.
- Run the preprocessing pipeline to create the dense / non‑dense splits.
- Sample five images from the dense subset.
- Produce `data/results/sanity_global.parquet` and `data/predictions/sample_global.json`. [UNRESOLVED-CLAIM: c_0a99d549 — status=not_enough_info]

## 5. Validate contracts
```bash
pytest -q tests/contract/
```

All result files must satisfy `contracts/inference_results.schema.yaml`. The sanity run should pass this validation. [UNRESOLVED-CLAIM: c_02e5750a — status=not_enough_info]

## 6. Inspect results
- `data/results/sanity_global.parquet` – contains one row per sampled image with columns
 `image_id`, `prediction`, `mean_iou`, `latency_ms`.
- `data/predictions/sample_global.json` – maps each `image_id` to the list of predicted boxes.

## 7. Clean up (optional)
```bash
rm -rf data/raw/* data/processed/* data/results/* data/analysis/*
```