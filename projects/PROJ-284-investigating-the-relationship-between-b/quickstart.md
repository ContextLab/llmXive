# Quickstart Guide: Brain Network Dynamics Pipeline

## Prerequisites
- Python 3.11+
- pip
- FSL and AFNI (for preprocessing, optional for validation)

## Installation

```bash
pip install -r requirements.txt
```

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

### Step 3: Analyze Correlations (Includes T023a, T023b)

```bash
python code/main.py --step correlations
```
**Output**: `data/analysis/correlations.csv`

This step performs:
- PCA on network metrics (T023a)
- Merges raw metrics with PCA scores to `data/analysis/full_metrics.csv` (T023b)
- Correlation analysis with FD covariate (T024)
- FDR correction (T025)

### Step 4: Visualization and Report

```bash
python code/main.py --step viz_report
```
**Output**: `figures/*.png`, `docs/report.md`

## Output Files

- `data/processed/aggregated_metrics.csv`: Raw network metrics per subject
- `data/analysis/pca_loadings.csv`: PCA component loadings
- `data/analysis/factor_scores.csv`: PCA factor scores per subject
- `data/analysis/full_metrics.csv`: **Combined raw metrics + PCA scores** (T023b output)
- `data/analysis/correlations.csv`: Correlation results with FDR correction
- `figures/*.png`: Generated plots
- `docs/report.md`: Final report

## Validation

To verify the pipeline produces all expected outputs:

```bash
python code/tools/validate_quickstart.py
```

This checks:
- All required files exist
- Imports are valid
- Scripts run without errors

## Troubleshooting

- **Missing `data/analysis/full_metrics.csv`**: Ensure `code/main.py --step correlations` runs successfully. This step invokes T023b logic.
- **Import errors**: Verify `requirements.txt` is installed and Python version is 3.11+.
- **FSL/AFNI errors**: These are expected on CI without Docker; use synthetic validation mode.
