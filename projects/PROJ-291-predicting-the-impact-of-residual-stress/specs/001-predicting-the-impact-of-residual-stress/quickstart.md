# Quickstart: Predicting Residual‑Stress Impact on Fatigue Life

> All commands assume you are in the repository root and have a recent Python 3.11 interpreter installed.

## 1. Set up the environment
```bash
# Create a clean virtualenv
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2. Verify data integrity
```bash
# Check that the synthetic dataset checksum matches the recorded hash (validation only)
python -c "import hashlib, pandas as pd; df = pd.read_csv('data/raw/synthetic_fatigue.csv'); \
print('Checksum OK' if hashlib.sha256(df.to_csv(index=False).encode()).hexdigest() == \
open('state/projects/PROJ-291-predicting-the-impact-of-residual-stress.yaml').read().split('synthetic_fatigue_checksum: ')[1].strip() else 'Checksum MISMATCH')"
```

## 3. Run the full pipeline
```bash
# 1) Ingest & preprocess (real open data; synthetic data only validates the code)
python -m src.ingest.ingest          # downloads (real) data, verifies checksum
python -m src.preprocess.preprocess   # unit conversion, imputation, proxy calc, checksum propagation, contract validation

# 2) Train models (5‑fold CV, hyper‑grid)
python -m src.models.train --feature-set A   # process‑only
python -m src.models.train --feature-set B   # process + measured stress (if any)
python -m src.models.train --feature-set C   # process + material props

# 3) Evaluate predictive gains
python -m src.models.evaluate --compare A B   # paired t‑test (full set) + sensitivity on measured subset
python -m src.models.evaluate --cross-material  # transfer learning evaluation

# 4) Mediation analysis (optional; runs only when enough measured‑stress rows exist)
python -m src.mediation.bootstrap_mediation --resamples 10000
```

## 4. Inspect results
- Model metrics: `results/reports/model_performance.csv`
- Paired‑t test: `results/reports/paired_t_test.csv`
- Mediation summary (if run): `results/reports/mediation_summary.csv`
- Figures: `results/reports/*.png`

## 5. Run tests
```bash
pytest -q
```

All steps complete within the GitHub Actions free‑tier limits (≈ 2.5 h, < 7 GB RAM). Synthetic data is **not** used for any scientific claim; it only confirms that the code executes correctly.
