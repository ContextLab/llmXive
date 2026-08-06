# Quickstart Guide

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`

## Running the Pipeline

The pipeline is executed via `code/main.py`. Each stage can be run independently.

### 1. Ingestion (Compute Energy Components)

This stage ingests raw tracking data and computes energy components.

```bash
python code/main.py --stage ingest --sample-ratio 0.1
```

**Output**: `data/derived/energy_samples.csv`

### 2. Statistical Analysis

This stage performs statistical tests on the energy data.

```bash
python code/main.py --stage stats --alpha 0.01
```

**Output**: `artifacts/statistical_results.json`

### 3. Sensitivity Analysis

This stage performs sensitivity analysis on thresholds.

```bash
python code/main.py --stage sensitivity --thresholds 0.01,0.05,0.10
```

**Output**: `artifacts/sensitivity_analysis_report.json`

### 4. Regression Analysis

This stage performs regression analysis on deviation drivers.

```bash
python code/main.py --stage regression
```

**Output**: `artifacts/regression_results.json`

### Full Run

To run the entire pipeline:

```bash
python code/main.py --stage all --sample-ratio 0.1
```

## Verification

After running, verify outputs:

- `data/derived/energy_samples.csv` exists and has correct schema
- `artifacts/energy_samples.hash` contains the SHA-256 hash of the CSV
- Statistical and regression outputs are generated in `artifacts/`
