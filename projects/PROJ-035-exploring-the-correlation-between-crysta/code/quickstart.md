# Quickstart Guide

This guide explains how to run the full pipeline for `PROJ-035-exploring-the-correlation-between-crysta`.

## Prerequisites

- Python 3.9+
- Installed dependencies (see `requirements.txt`)

## Running the Pipeline

The pipeline is orchestrated by `code/src/main.py`.

### 1. Setup and Data Ingestion (US1)

Fetch structures and thermal data, validate provenance, normalize, and merge.

```bash
python code/src/main.py --stage ingest --seed 42
```

This will produce:
- `data/raw/thermal_raw.csv`
- `data/cleaned/provenance_report.json`
- `data/cleaned/merged_perovskite.csv`

### 2. Descriptor Computation (US2)

Compute structural descriptors and stratify by chemistry.

```bash
python code/src/main.py --stage descriptors --seed 42
```

This will produce:
- `data/descriptors.csv`
- `data/cleaned/stratified_data.csv`

### 3. Correlation Analysis (US2)

Perform correlation analysis and sensitivity checks.

```bash
python code/src/main.py --stage correlation --seed 42
```

This will produce:
- `data/results/correlation_matrix.json`
- `data/results/stratified_summary.md`
- `data/results/sensitivity_analysis.json`

### 4. Full Run (All Stages)

To run the entire pipeline from scratch:

```bash
python code/src/main.py --stage full --seed 42
```

## Verification

After running, verify the output files:
- Check `data/results/correlation_matrix.json` for `stratified_results` and `corrected_p_values`.
- Check `data/results/sensitivity_analysis.json` for keys `0.01`, `0.05`, `0.1`.
- Ensure `data/cleaned/merged_perovskite.csv` has >= 50 rows.