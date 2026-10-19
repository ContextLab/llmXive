# Quickstart: Predicting Residual‑Stress Impact on Fatigue Life

> Assumes a recent Python 3.11 interpreter and internet access from the repository root.

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
# This script ensures the GitHub Actions runner meets RAM, disk, and package requirements.
# It must exit with status 0 before any further step.
bash scripts/env_check.sh
```

## 3. Run the full analysis pipeline
```bash
# 1) Ingest & preprocess (downloads open data and loads the synthetic validation set)
python -m src.ingest.ingest          # downloads, checksums, merges, proxy calc; exits 0 on success
python -m src.preprocess.preprocess   # unit conversion, imputation, contract validation

# 2) Train models (5‑fold CV, hyper‑grid)
python -m src.models.train --feature-set A   # process‑only
python -m src.models.train --feature-set B   # process + measured stress (if any)
python -m src.models.train --feature-set C   # process + material props (+ proxy stress)

# 3) Evaluate predictive gains
python -m src.models.evaluate --compare A B   # paired t‑test (measured‑stress subset)
python -m src.models.evaluate --cross-material  # transfer learning ΔMAPE + permutation test

# 4) Mediation analysis (runs only when enough measured‑stress rows exist)
python -m src.mediation.bootstrap_mediation --resamples 10000
```

## 4. Inspect results
- Model metrics: `results/reports/model_performance.csv`  
- Paired t‑test: `results/reports/paired_t_test.csv`  
- Cross‑material ΔMAPE: `results/reports/cross_material.csv`  
- Mediation (if executed): `results/reports/mediation_summary.csv`  
- Figures (PNG): `results/reports/*.png`

## 5. Run automated tests
```bash
pytest -q
```

All steps complete within the GitHub Actions free‑tier limits (≈ 2.5 h, < 7 GB RAM). Synthetic data is **not** used for external scientific conclusions; it only confirms that the pipeline runs without error.
