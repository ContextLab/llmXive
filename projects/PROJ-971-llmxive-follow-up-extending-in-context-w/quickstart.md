# Quickstart: Minimal Auto‑ICWM Pipeline

**Feature**: `001-auto-icwm-latent-dynamics`
**Goal**: Run the minimal end‑to‑end pipeline on a small subset (50 clips) to produce the foundational descriptor and complexity datasets.

## Project Layout
- `code/src/pipeline/`: Contains the core research implementation (data generation, feature extraction, modeling).
- `data/raw/`: Storage for generated interaction clips (`.npz`).
- `data/processed/`: Structured statistical descriptors and complexity metrics.
- `results/`: Final validation results and summary reports.
- `specs/`: Feature specifications and data-model contracts (schemas).
- `scripts/`: Automation scripts for environment setup and minimal execution.

## Prerequisites
All dependencies are listed in `requirements.txt`. To use a local virtual environment:

```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## Run the Minimal Pipeline
The pipeline is orchestrated by two helper scripts in `scripts/`:

1. `scripts/quickstart.sh`: Configures the environment and `PYTHONPATH`.
2. `scripts/run_minimal.sh`: Executes the minimal data generation and extraction flow.

Execute the minimal pipeline with this single command:

```bash
bash -c "source scripts/quickstart.sh &&./scripts/run_minimal.sh"
```

## Verification
After completion, verify that the following artifacts were produced:

```bash
# Full descriptor table
ls data/processed/descriptors.csv
# Task complexity table
ls data/processed/task_complexity.csv
# Legacy subset shortcut
ls data/descriptors_subset.csv
```

## Pipeline Summary
| Step | Action | Output |
|------|--------|--------|
| 1 | Generate reproducible interaction clips | `data/raw/clip_*.npz` |
| 2 | Extract latent descriptors (variance, autocorr, spectral) | `data/processed/descriptors.csv` |
| 3 | Create legacy shortcut for 50 clips | `data/descriptors_subset.csv` |
| 4 | Compute task-complexity metric | `data/processed/task_complexity.csv` |