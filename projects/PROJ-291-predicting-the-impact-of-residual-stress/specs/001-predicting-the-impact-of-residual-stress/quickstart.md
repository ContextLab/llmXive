# Quickstart: Predicting Residual‑Stress Impact on Fatigue Life

> Assumes a recent Python 3.11 interpreter and internet access from the repository root.

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
# 0) Run the deterministic synthetic data generator
python -m src.data.gen_synthetic

# 1) Ingest & preprocess (unit conversion, imputation, proxy calc)
python -m src.ingest.ingest          # creates unified_fatigue.csv & missing_flags.json
python -m src.preprocess.validate    # validates against contracts/dataset_schema.yaml

# 2) Build feature sets (balanced A & B, full C)
python -m src.features.build_sets

# 3) Train models (5‑fold CV, hyper‑grid)
python -m src.models.train --feature-set A
python -m src.models.train --feature-set B
python -m src.models.train --feature-set C

# 4) Evaluate predictive gains
python -m src.models.evaluate --compare A B   # Wilcoxon test + Bonferroni‑corrected significance

# 5) Cross‑material transfer evaluation
python -m src.models.evaluate --cross-material   # transfer ΔMAPE + permutation test

# 6) Mediation analysis — runs ONLY if a real open dataset (source != synthetic
#    and != verification) contributes >= 50 rows with measured residual stress.
#    The synthetic dataset is never eligible; if no real dataset is present,
#    this step is skipped and a limitation is reported.
python -m src.mediation.bootstrap_mediation --resamples 10000
```

## 4. Inspect results
- Model metrics: `results/reports/model_performance.csv`  
- Wilcoxon test: `results/reports/wilcoxon_test.csv`  
- Cross‑material ΔMAPE: `results/reports/cross_material.csv`  
- Proxy–measured agreement: `results/reports/proxy_agreement.csv`  
- Mediation (if executed on real data): `results/reports/mediation_summary.csv`  
- Figures (PNG): `results/reports/*.png`  

## 5. Run automated tests
```bash
pytest -q
```

All steps complete within the GitHub Actions free‑tier limits (≈ 2.5 h, < 7 GB RAM). Synthetic data is **not** used for external scientific conclusions and is **never used for mediation**; it only validates that the pipeline runs correctly.