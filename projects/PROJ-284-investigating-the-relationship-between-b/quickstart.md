# Quickstart Guide

This guide validates the pipeline execution.

## Prerequisites
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Steps

### 1. Download and Preprocess (T012, T013)
```bash
python code/main.py --step download_preprocess --subjects 5
```
*Note: This step requires HCP credentials or will use the ADHD dataset fallback for testing.*

### 2. Extract Metrics (T017)
```bash
python code/data/metrics.py --subject 100307 --nifti data/processed/sub-100307_preproc.nii.gz
```
*Output: data/processed/aggregated_metrics.csv*

### 3. Create Full Metrics (T017 + T023)
```bash
python code/analysis/create_full_metrics.py
```
*Output: data/analysis/full_metrics.csv*

### 4. Run Correlations (T024)
```bash
python code/analysis/run_correlations.py
```

### 5. Generate Report (T033)
```bash
python code/report/generate.py
```

## Validation
Verify that `data/analysis/full_metrics.csv` exists and contains columns:
- subject_id
- modularity
- global_efficiency
- participation_coefficient
- within_module_degree
- pca_factor_1
- pca_factor_2