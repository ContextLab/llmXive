# Quickstart Guide

## Prerequisites

- Python 3.11+
- Required packages in `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline is executed in steps. Ensure each step completes successfully before proceeding.

### Step 1: Data Download and Preprocessing

```bash
python code/main.py --step download_preprocess --subjects 50
```

### Step 2: Metric Extraction

```bash
python code/main.py --step metrics
```

### Step 3: PCA and Correlation Analysis

This step performs PCA on network metrics and generates correlation results.

```bash
python code/analysis/pca_runner.py
```

### Step 4: Visualization and Report Generation

```bash
python code/main.py --step viz_report
```

## Output Files

- `data/analysis/pca_loadings.csv`: PCA component loadings
- `data/analysis/factor_scores.csv`: Subject factor scores
- `data/analysis/full_metrics.csv`: Combined raw metrics and PCA scores
- `data/analysis/correlations.csv`: Correlation results with FDR correction
- `figures/`: Generated plots

## Validation

To validate the pipeline execution:

```bash
python code/tools/validate_quickstart.py
```