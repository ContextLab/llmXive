# Quickstart Guide

This guide outlines the steps to run the full pipeline for predicting cognitive fatigue from resting-state EEG.

## Prerequisites

- Python 3.11+
- Virtual environment activated

## Installation

```bash
pip install -r code/requirements.txt
```

## Execution Steps

Run the following commands in order. Each step depends on the output of the previous one.

### 1. Download and Validate Data

Fetches the EEG dataset and validates the presence of fatigue ratings.

```bash
python code/download.py
```

Expected output: `data/processed/validation_report.json` and raw data in `data/raw/`.

### 2. Preprocess Data

Applies bandpass (1-40Hz) and notch (50Hz) filters, and rejects artifacts.

```bash
python code/preprocess.py
```

Expected output: `data/processed/cleaned_eeg.fif` and `logs/exclusion_log.csv`.

### 3. Extract Features

Calculates Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE).

```bash
python code/features.py
```

Expected output: `data/processed/lzc_metrics.csv` and `data/processed/pe_metrics.csv`.

### 4. Run Analysis

Performs correlation analysis and Benjamini-Hochberg correction.

```bash
python code/analysis.py
```

Expected output: `data/analysis/correlation_results.json` and `data/analysis/sensitivity_table.csv`.

### 5. Run Collinearity Diagnostics (T023)

Checks for multicollinearity among complexity metrics using Variance Inflation Factor (VIF).

```bash
python code/collinearity.py
```

Expected output: `data/analysis/collinearity_report.json` containing VIF scores and pass/fail status.

### 6. Generate Report

Compiles the final report with all statistical findings.

```bash
python code/report.py
```

Expected output: `docs/final_report.md`.

## Verification

After running all steps, verify that the following files exist:
- `data/processed/cleaned_eeg.fif`
- `data/processed/lzc_metrics.csv`
- `data/processed/pe_metrics.csv`
- `data/analysis/collinearity_report.json`
- `docs/final_report.md`
