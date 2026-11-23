# Quickstart Guide

This guide describes how to run the full pipeline from data acquisition to analysis and reporting.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Run the Pipeline

The pipeline is executed in steps. You can run them sequentially or use the `main.py` entry point.

### Step 1: Data Acquisition and Preprocessing
```bash
python code/main.py --step download_preprocess --subjects 50
```
*Note: This step downloads HCP/ADHD data and preprocesses it. It requires network access.*

### Step 2: Metric Extraction
```bash
python code/main.py --step extract_metrics
```
*Extracts functional connectivity and graph metrics.*

### Step 3: PCA and Correlation Analysis
```bash
python code/analysis/pca_runner.py
python code/analysis/run_correlations.py
python code/analysis/generate_full_metrics.py
```
*These steps perform PCA, run correlations with FD covariate, and generate the full metrics file.*

### Step 4: Visualization and Reporting
```bash
python code/main.py --step viz_report
```
*Generates plots and the final report.*

## Output Files

- `data/analysis/pca_loadings.csv`
- `data/analysis/factor_scores.csv`
- `data/analysis/full_metrics.csv`
- `data/analysis/correlations.csv`
- `figures/*.png`
- `docs/report.md`

## Troubleshooting

- If you encounter `ImportError`, ensure `code/` is in your `PYTHONPATH`.
- If data files are missing, check that Step 1 completed successfully.
- For memory issues, reduce the `--subjects` count or adjust `MEMORY_LIMIT` in `code/config.py`.