# Quickstart: Predicting Residual‑Stress Impact on Fatigue Life

> All commands assume you are in the repository root with Python 3.11 available.

## 1. Set up the environment

```bash
# Create a clean virtual environment in the directory ".venv"
python -m venv.venv
# Activate the virtual environment
source.venv/bin/activate
# Install the exact pinned dependencies
pip install -r requirements.txt
```

The `requirements.txt` pins all package versions (pandas 2.2.2, scikit‑learn 1.5.0,
torch 2.3.0, statsmodels 0.14.2, datasets 2.20.0, numpy 1.26.4, and supporting
packages). A clean `pip install -r requirements.txt` completes well within the
2‑minute budget on the GitHub Actions ubuntu‑latest runner (CPU‑only torch wheel).

## 2. Verify the environment

The repository provides an environment‑check script that installs any missing
dependencies and confirms that every required module can be imported:

```bash
bash scripts/env_check.sh
```

The command exits with status 0 only when all required modules import without error. [UNRESOLVED-CLAIM: c_2812e31a — status=not_enough_info]
The log is written to `results/env_check.log`.

## 3. Run the full pipeline (single command)

```bash
bash scripts/run_pipeline.sh
```

This orchestrates every stage – data ingestion, preprocessing, feature‑set
construction, model training, statistical evaluation, mediation analysis, and
report generation. Stages that belong to tasks not yet implemented are reported
as *skipped*; implemented stages will fail loudly on error.

## 4. Inspect results

- Unified dataset: `data/processed/unified_fatigue.csv`
- Model metrics: `results/performance.csv`
- Paired t‑test: `results/paired_t_test.csv`
- Cross‑material transfer: `results/cross_material.csv`
- Mediation summary (if run): `results/mediation_summary.csv`
- Figures: `results/figures/`
- Environment verification log: `results/env_check.log`

## 5. Run tests

```bash
pytest -q
```

All steps complete within the GitHub Actions free‑tier limits (≤ 6 h runtime,
< 7 GB RAM). Synthetic data is never used for scientific claims; the pipeline
ingests real public datasets from their canonical, version‑pinned URLs.
