# Quickstart: Predicting Residual‑Stress Impact on Fatigue Life

> Assumes a fresh Python 3.11 interpreter and internet access from the repository root.

## 1. Set up the environment
```bash
# Create a clean virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2. Verify the runner environment (CI sanity check)
```bash
# Checks Python version, required packages, RAM, and disk space.
# Must exit with status 0 before proceeding.
bash scripts/env_check.sh
```

## 3. Run the full analysis pipeline (end‑to‑end)
```bash
# 0) Generate deterministic synthetic data (pipeline validation only)
python -m src.data.gen_synthetic

# 1) Ingest & preprocess (unit conversion, imputation, proxy calc)
python -m src.ingest.ingest          # creates unified_fatigue.csv & missing_flags.json
python -m src.preprocess.validate    # validates against contracts/dataset_schema.yaml

# 2) Build feature sets (balanced A & B, full C)
python -m src.features.build_sets

# 3) Train models (5‑fold CV, hyper‑grid
``` 

# Note
The pipeline runs **only** on synthetic data for illustration; no empirical conclusions about real fatigue behavior are drawn.
