# Quickstart: Predicting Residual‑Stress Impact on Fatigue Life

> All commands assume you are in the repository root with Python 3.11 available.

## 1. Set up the environment

```bash
# Create a clean virtual environment
python -m venv.venv
# Activate the virtual environment
source.venv/bin/activate
# Install the exact pinned dependencies
pip install -r requirements.txt
```

## 2. Verify the environment

Run the environment check to ensure all dependencies are correctly installed and importable:

```bash
make env-check
# OR
bash scripts/env_check.sh
```

The command exits with status 0 only when all required modules import without error. The log is written to `results/env_check.log`.

## 3. Run the full pipeline (single command)

```bash
bash scripts/run_pipeline.sh
```

This orchestrates every stage – data ingestion, preprocessing, feature‑set construction, model training, statistical evaluation, mediation analysis, and report generation. Stages that belong to tasks not yet implemented are reported as *skipped*.

## 4. Inspect results

- Unified dataset: `data/processed/unified_fatigue.csv`
- Model metrics: `results/performance.csv`
- Paired t‑test: `results/paired_t_test.csv`
- Cross‑material transfer: `results/cross_material.csv`
- Mediation summary: `results/mediation_summary.csv`
- Figures: `results/figures/`

## 5. Run tests

```bash
pytest -q
```

All steps are designed to complete within the GitHub Actions free‑tier limits (≤ 6 h runtime, < 7 GB RAM).
