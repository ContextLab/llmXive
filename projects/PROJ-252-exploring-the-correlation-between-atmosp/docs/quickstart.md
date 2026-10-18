# Quickstart: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Prerequisites

- Python 3.11 or newer
- `git`
- Internet access (for data download)
- Sufficient free disk space

## Setup & Run

```bash
# Install exact dependency versions and run the full pipeline
pip install -r requirements.txt && python -m code.seed_init && python -m code.main
```

This single command:
1. Installs the frozen dependencies listed in `requirements.txt`.
2. Initializes deterministic random seeds (writes `logs/seed_initialization.log` containing the line **“Seeds set to 42”**).
3. Executes the project's main entry point (`code/main.py`) which runs the complete analysis pipeline.

## Expected Outputs

- `logs/seed_initialization.log` – confirms seed initialization.
- `data/processed/analysis_ready.parquet` – analysis‑ready dataset.
- `data/processed/analysis_results.json` – statistical results and conclusions.
- `paper/results.md` – human‑readable report summarising findings.

## Validation

After the command completes, verify that `logs/seed_initialization.log` exists and contains the exact string:

```
Seeds set to 42
```

If the log file is present and the command exits with status 0, the quick‑start has succeeded.