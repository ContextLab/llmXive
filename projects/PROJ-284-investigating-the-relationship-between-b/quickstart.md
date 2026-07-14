# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip
- Internet access (for downloading datasets)

## Installation
```bash
pip install -r requirements.txt
```

## Running the Pipeline
The pipeline is executed in sequential steps using `code/main.py`.

### Step 1: Download and Preprocess Data
Downloads HCP/ADHD data and runs preprocessing (motion correction, normalization, smoothing).
```bash
python code/main.py --step download_preprocess --subjects 50
```
*Note: Requires FSL/AFNI for full preprocessing. For CI/synthetic validation, see `code/data/download.py`.*

### Step 2: Extract Metrics (T017)
Extracts time-series, calculates connectivity matrices, and computes graph metrics (including Participation Coefficient and Within-Module Degree).
**Output**: `data/analysis/aggregated_metrics.csv`
```bash
python code/main.py --step metrics
```

### Step 3: Analyze Correlations
Performs PCA, computes correlations with behavioral scores, and applies FDR correction.
**Output**:
- `data/analysis/pca_loadings.csv`
- `data/analysis/factor_scores.csv`
- `data/analysis/full_metrics.csv`
```bash
python code/main.py --step correlations
```

### Step 4: Visualization and Reporting
Generates scatter plots, network diagrams, and the final report.
**Output**:
- `figures/scatter_*.png`
- `figures/network_*.png`
- `docs/report.md`
```bash
python code/main.py --step viz_report
```

## Validation
Run the validation script to ensure all outputs are generated:
```bash
python code/tools/validate_quickstart.py
```

## Troubleshooting
- **Missing FSL/AFNI**: If preprocessing fails due to missing tools, the pipeline will attempt synthetic validation (see `code/data/download.py`).
- **Memory Errors**: Adjust `MEMORY_LIMIT` in `code/config.py`.
- **API Errors**: Check `code/config.py` for HCP credentials.
