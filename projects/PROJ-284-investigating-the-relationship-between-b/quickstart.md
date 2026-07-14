# Quickstart Guide

This document outlines the steps to run the full pipeline.

## Prerequisites
- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`

## Installation

The pipeline is executed via `python code/main.py`.

### Step 1: Download and Preprocess Data

## Execution Steps

### Step 1: Download and Preprocess Data

### Step 1: Download & Preprocess
Downloads HCP/ADHD data and performs preprocessing (or synthetic validation).
```bash
python code/main.py --step download_preprocess --subjects 50
```
**Output**: `data/processed/` (NIfTI files, aggregated metrics)

### Step 2: Extract Metrics

```bash
python code/main.py --step metrics --subjects 50
```
**Output**: `data/analysis/full_metrics.csv`, `data/analysis/pca_loadings.csv`

### Step 3: Analyze (Correlations & FDR)

This step runs T024 and T025, generating `data/analysis/correlations.csv` and `data/analysis/full_metrics.csv`.

```bash
python code/main.py --step correlations
```
**Output**: `data/analysis/correlations.csv`

### Step 4: Visualization and Report

```bash
python code/main.py --step viz_report
```
**Output**: `figures/*.png`, `docs/report.md`

## Output Artifacts

- `data/processed/aggregated_metrics.csv`: Aggregated graph metrics per subject.
- `data/analysis/full_metrics.csv`: Combined metrics + PCA scores.
- `data/analysis/correlations.csv`: Correlation results with FD covariate (T024).
- `figures/`: Generated plots.
- `docs/report.md`: Final report.
