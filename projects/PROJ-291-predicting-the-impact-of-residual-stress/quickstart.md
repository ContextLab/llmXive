# Quickstart: Predicting Residual‑Stress Impact on Fatigue Life

> All commands assume you are in the repository root and have a recent Python 3.11 interpreter installed.

## 1. Set up the environment
```bash
# Create a clean virtualenv
python -m venv.venv
source.venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2. Verify the environment
The repository provides a convenient `make` target that checks the installation of all required packages.
```bash
make env-check
```
The command should exit with status 0, confirming that the environment is ready.

## 3. Verify data integrity
```bash
# Check that the synthetic dataset checksum matches the recorded hash (validation only)
python -c "import hashlib, pandas as pd; df = pd.read_csv('data/raw/synthetic_fatigue.csv'); \
print('Checksum OK' if hashlib.sha256(df.to_csv(index=False).encode()).hexdigest() == \
open('state/projects/PROJ-291-predicting-the-impact-of-residual-stress.yaml').read().split('synthetic_fatigue_checksum: ')[1].strip() else 'Checksum MISMATCH')"
```

## 4. Run the full pipeline
A single command runs the entire analysis from data ingestion to final reporting:
```bash
bash run_pipeline.sh
```
The script orchestrates all stages (ingestion, preprocessing, model training, evaluation, mediation analysis, and report generation). It is provided later in the repository and can be invoked at any time after the environment is set up.

## 5. Inspect results
- Model metrics: `results/reports/model_performance.csv`
- Paired‑t test: `results/reports/paired_t_test.csv`
- Mediation summary (if run): `results/reports/mediation_summary.csv`
- Figures: `results/reports/*.png`

## 6. Run tests
```bash
pytest -q
```

All steps complete within the GitHub Actions free‑tier limits (≈ 2.5 h, < 7 GB RAM). [UNRESOLVED-CLAIM: c_8be9f748 — status=not_enough_info] Synthetic data is **not** used for any scientific claim; it only confirms that the code executes correctly.
