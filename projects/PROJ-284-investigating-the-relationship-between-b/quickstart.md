# Quickstart Guide

## Prerequisites
- Python 3.11
- `pip install -r requirements.txt`

## Steps

1. **Download Data**
 ```bash
 python code/data/download.py
 ```
 This will fetch the ADHD dataset and save phenotypic data to `data/raw/phenotypic.csv`.

2. **Preprocess Data**
 ```bash
 python code/data/preprocess.py
 ```
 This will preprocess the downloaded data and save cleaned NIfTI files to `data/processed/`.

3. **Extract Metrics**
 ```bash
 python code/data/metrics.py
 ```
 This will extract graph metrics and save aggregated metrics to `data/processed/aggregated_metrics.csv`.

4. **Run PCA Analysis (T023a)**
 ```bash
 python code/analysis/pca_runner.py
 ```
 This will perform PCA on the network metrics and save:
 - `data/analysis/pca_loadings.csv`
 - `data/analysis/factor_scores.csv`
 - `data/analysis/full_metrics.csv`

5. **Run Correlation Analysis**
 ```bash
 python code/analysis/correlations.py
 ```
 This will run correlations with FD and apply FDR correction.

6. **Generate Visualizations and Report**
 ```bash
 python code/viz/scatter.py
 python code/viz/network.py
 python code/report/generate.py
 ```

## Validation
Ensure all output files are generated in the `data/` and `figures/` directories.
