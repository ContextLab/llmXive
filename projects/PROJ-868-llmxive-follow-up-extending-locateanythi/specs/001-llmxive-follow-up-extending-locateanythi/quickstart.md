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
    --model-variant mini \
    --max-dense-samples 2000 \
    --batch-size 4 \
    --output-dir ../../data/
```
- `--datasets` selects the verified datasets (VRSBench & COCO validation).  
- `--sparsity-grid` defines the windows to evaluate; add `1` to include the optional run.  
- `--run-one-patch` toggles FR‑009 (optional 1‑patch run).  
- `--model-variant mini` selects the lightweight **LocateAnything‑mini** checkpoint that fits the CPU budget.  
- `--max-dense-samples 2000` caps the number of dense images processed (see Phase 1 sampling for compute feasibility).  
- The script **randomizes** the order of sparsity configurations using a fixed seed, eliminating warm‑up bias.  
- After inference, the script automatically **consolidates** all `inference_*.parquet` files into `data/results/master_inference.parquet` before generating figures and tables.

## 5. (Optional) Perform the ±8‑patch sensitivity sweep
If a tipping point is detected, the script automatically runs the sweep. To force it manually:
```bash
python -m src.cli.run_experiment \
    --datasets vrsbench coco_val \
    --sparsity-grid global 64 32 16 \
    --sweep-around-tipping true \
    --model-variant mini \
    --max-dense-samples 2000 \
    --batch-size 4
```

## 6. Validate contracts
```bash
pytest -q tests/contract/
```
All result files must satisfy `contracts/inference_results.schema.yaml`. Failure aborts the CI job.

## 7. Inspect results
- `docs/results.md` – markdown summary ready for the paper pipeline.  
- `figures/` – PNG files for degradation curve, latency, attribution examples.  
- `tables/` – CSV files for ANOVA, trend test, tipping‑point.

All tables/figures reference the consolidated `master_inference.parquet`, satisfying the Single Source of Truth principle.

## 8. Clean up (optional)
```bash
rm -rf data/raw/* data/processed/* data/results/* data/analysis/*
```

**Note**: The entire run completes in ≤ 6 hours on the free‑tier GitHub Actions CPU runner (empirically on the order of 3–4 h for the sampled subset). If you encounter memory pressure, lower the batch size via `--batch-size 2` or reduce `--max-dense-samples`.  

---  