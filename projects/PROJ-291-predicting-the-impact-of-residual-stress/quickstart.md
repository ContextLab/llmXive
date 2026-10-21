# Quickstart: Predicting Residual‑Stress Impact on Fatigue Life

> Assumes a recent Python 3.11 interpreter and internet access from the repository root.

## 1. Set up the environment
```bash
# Create a clean virtual environment
python -m venv.venv
source.venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2. Verify the runner environment (CI sanity check)
```bash
# This script ensures the GitHub Actions runner meets RAM, disk, and package requirements.
# It must exit with status 0 before any further step.
bash scripts/env_check.sh
```

## 3. Run the full analysis pipeline
```bash
# 1) Ingest & preprocess (uses the bundled synthetic validation set)
bash scripts/run_pipeline.sh
```

## 4. Inspect results
- Unified dataset: `data/processed/unified_fatigue.csv`
- Model metrics, statistical tests, and figures will appear under `results/` as later tasks complete.

## 5. Run automated tests
```bash
pytest -q
```

All steps are designed to complete within the GitHub Actions free‑tier limits (≤ 6 h runtime, < 7 GB RAM).