# Execution Guide

## Overview
This document details the execution flow of the PROJ-340 pipeline, from data ingestion to final report generation.

## Execution Flow

1. **Initialization**
 - `main.py` loads configuration from `data/config/`.
 - Checks for `data/config/real_data_sources.yaml`.
 - If `--mode synthetic` is passed, invokes `code/ingest.py` in synthetic mode.

2. **Ingestion & Validation**
 - `code/ingest.py` fetches data.
 - Validates against `data/config/required_variables.yaml`.
 - Detects outliers using IQR method.
 - Generates `data/results/outlier_report.json`.
 - Saves filtered data to `data/processed/filtered_data.parquet`.

3. **Analysis**
 - `code/analysis.py` checks data distribution (Shapiro-Wilk).
 - Selects method: ZINB (if zero-inflated) or Spearman/Pearson.
 - Runs correlation analysis.
 - Applies Benjamini-Hochberg FDR correction.
 - Saves `data/results/correlation_matrix.json`.

4. **Diagnostics**
 - `code/diagnostics.py` runs collinearity checks (VIF).
 - Performs sensitivity analysis (p<0.01, 0.05, 0.10).
 - Calculates power analysis.
 - Saves `data/results/sensitivity_analysis.csv` and `power_analysis_report.json`.

5. **Reporting**
 - `code/report.py` generates `data/results/report_draft.md`.
 - Scans for causal language. Halts if violations found.

6. **Finalization**
 - Records checksums in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml`.
 - Generates `data/results/timing_evidence.json`.

## Command Line Interface

```bash
# Full pipeline (Real Data)
python code/main.py

# Full pipeline (Synthetic Data)
python code/main.py --input data/raw/synthetic_data.csv --output data/results/

# Ingestion only
python code/ingest.py --mode synthetic --output data/raw/synthetic_data.csv

# Specific analysis steps
python code/analysis.py --input data/processed/filtered_data.parquet
python code/diagnostics.py --input data/processed/filtered_data.parquet
```

## Error Handling

- **Missing Variables**: `SystemExit` with message "No required variables loaded."
- **Real Data Fetch Fail**: `RealDataFetchError` with message "Failed to fetch real data."
- **Timeout**: `TimeoutError` if execution exceeds 6 hours.
- **Causal Language**: `SystemExit` if causal language detected in report.

## Output Verification

After execution, verify the following artifacts exist:
- `data/processed/filtered_data.parquet`
- `data/results/correlation_matrix.json`
- `data/results/sensitivity_analysis.csv`
- `data/results/power_analysis_report.json`
- `data/results/report_draft.md`
- `data/results/timing_evidence.json`
