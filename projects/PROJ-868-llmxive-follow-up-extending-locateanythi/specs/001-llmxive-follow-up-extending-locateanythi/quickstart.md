# Quickstart: Running the Attention‑Sparsity Study

This guide assumes a fresh GitHub Actions runner or a local environment with the same resource limits (2 CPU cores, ≤ 7 GB RAM).

## 1. Clone the repository and navigate to the feature directory
```bash
git clone <REPO_URL>
cd specs/001-llmxive-follow-up
```

## 2. Install the exact dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ../../requirements.txt   # repository‑wide pinned requirements
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

## 4. Run the full pipeline (default configuration)
```bash
python -m src.cli.run_experiment \
    --datasets vrsbench coco_val \
    --sparsity-grid global 64 32 16 \
    --run-one-patch false \
    --attribution-method gradcam \
    --output-dir ../../data/
```
- `--datasets` selects the verified datasets (VRSBench & COCO validation).  
- `--sparsity-grid` defines the windows to evaluate; add `1` to include the optional run.  
- `--run-one-patch` toggles FR‑009 (optional 1‑patch run).  
- All intermediate artifacts are written under `data/` with content‑hash filenames.

## 5. (Optional) Perform the ±8‑patch sensitivity sweep
If a tipping point is detected, the script automatically runs the sweep. To force it manually:
```bash
python -m src.cli.run_experiment \
    --sparsity-grid global 64 32 16 \
    --sweep-around-tipping true
```

## 6. Validate contracts
```bash
pytest -q tests/contract/
```
All result files must satisfy `contracts/inference_results.schema.yaml`. Failure aborts the CI job.

## 7. Inspect results
- `docs/results.md` – markdown summary ready for the paper pipeline.  
- `figures/` – PNG files for degradation curve, latency, attribution examples.  
- `tables/` – CSV files for ANOVA, correlation, tipping‑point.

## 8. Clean up (optional)
```bash
rm -rf data/raw/* data/processed/* data/results/* data/analysis/*
```

**Note**: The entire run completes in ≤ 6 hours on the free‑tier GitHub Actions CPU runner (empirically on the order of several hours for the full grid). Adjust `--batch-size` if you encounter memory pressure.

---
