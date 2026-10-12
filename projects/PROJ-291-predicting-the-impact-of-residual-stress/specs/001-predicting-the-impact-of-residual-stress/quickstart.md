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

## 2. Verify data integrity (optional sanity check)
```bash
# Example: Verify synthetic validation dataset checksum
python - <<'PY'
import hashlib, yaml, pandas as pd
with open('data/raw/synthetic_fatigue.csv', 'rb') as f:
    chk = hashlib.sha256(f.read()).hexdigest()
state = yaml.safe_load(open('state/projects/PROJ-291-predicting-the-impact-of-residual-stress.yaml'))
print('Checksum match' if chk == state.get('synthetic_fatigue_checksum') else 'Checksum mismatch')
PY
```

## 3. Run the full analysis pipeline
```bash
# 1) Ingest & preprocess (real open data; synthetic data only validates the code)
python -m src.ingest.ingest          # downloads, checksums, merges
python -m src.preprocess.preprocess   # unit conversion, imputation, proxy calc, contract validation

# 2) Train models (5‑fold CV, hyper‑grid)
python -m src.models.train --feature-set A   # process‑only
python -m src.models.train --feature-set B   # process + measured stress (if any)
python -m src.models.train --feature-set C   # process + material properties

# 3) Evaluate predictive gains
python -m src.models.evaluate --compare A B   # paired t‑test + Bonferroni
python -m src.models.evaluate --cross-material  # transfer learning ΔMAPE

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

All steps complete within the GitHub Actions free‑tier limits (≈ 2.5 h, < 7 GB RAM). Synthetic data is **not** used for scientific conclusions; it only confirms that the pipeline runs without error.

---
