# Quickstart: 001-static-dynamic-gap-analysis

This guide demonstrates the minimal end‑to‑end execution of the
pipeline on a fresh environment.

## Run the dry‑run pipeline
```bash
python -m src.cli.run_pipeline --dry-run
```
The command will:

1. Create the required project directories (`data/`, `interim/`, `features/`,
 `models/`, `reports/`).
2. Pin the random seed for reproducibility.
3. Write a tiny CSV file `data/results/sample_run.csv` (≤ 10 rows) and
 print its location.

After the command finishes without error, you should see a line similar to:
```
Dry-run completed. Sample result at: data/results/sample_run.csv
```
You can inspect the file with:
```bash
cat data/results/sample_run.csv
```