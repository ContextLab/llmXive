# Quickstart for PROJ-433

This document describes the minimal commands required to run the full
analysis pipeline on a small test subset. All paths are relative to the
repository root.

## Step 1 – Verify data directories
```bash
python -c "import pathlib, sys; \
[print(p) for p in ['data/raw','data/processed','data/results','code','tests','contracts'] \
if not pathlib.Path(p).exists()]"
```

## Step 2 – Run preprocessing (example)
```bash
python code/preprocess.py --subject sub-01 --mode ci
```

## Step 3 – Compute metrics (example)
```bash
python code/metrics.py --subject sub-01 --input-dir data/raw --output-dir data/processed
```

## Step 4 – Generate permutation test report
The original script `code/permutation_report.py` creates the PNG file.
We now invoke a thin wrapper that also logs the creation:

```bash
python code/log_permutation_report_creation.py
```

After this command finishes, you should find:
- `data/results/permutation_report.png`
- a new line in `data/analysis_log.txt` confirming the report creation.