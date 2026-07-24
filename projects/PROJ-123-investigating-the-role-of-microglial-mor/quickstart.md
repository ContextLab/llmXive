# Quickstart Guide

## Prerequisites

- Python 3.11+
- Required packages (install via `pip install -r requirements.txt`)

## Installation

```bash
pip install -r requirements.txt
```

## Running the Pipeline

### 1. Generate Synthetic Data (for validation)

```bash
python code/main.py --mode generate-synthetic --output data/processed/synthetic_dataset.csv
```

### 2. Run Full Pipeline (Analysis + Output + Reports)

```bash
python code/main.py --mode run-full --data data/processed/synthetic_dataset.csv
```

This will:
- Run the analysis pipeline (normalization, VIF check, regression, CV, sensitivity)
- Generate morphological metrics CSV
- Generate regression reports (JSON and Markdown)
- Generate validation report

### 3. Run Individual Components

#### Analysis Pipeline Only

```bash
python code/main.py --mode run-analysis --data data/processed/synthetic_dataset.csv
```

#### Output Pipeline Only

```bash
python code/main.py --mode run-output
```

#### Report Generation Only

```bash
python code/main.py --mode run-report
```

#### Validation Report Only

```bash
python code/main.py --mode run-validation
```

## Expected Outputs

- `data/processed/synthetic_dataset.csv` - Synthetic input data
- `data/processed/morphological_metrics.csv` - Extracted morphological metrics
- `data/intermediate/normalized_cognitive_scores.csv` - Normalized cognitive scores
- `data/intermediate/vif_check.json` - VIF analysis results
- `data/intermediate/pca_model.pkl` - PCA model (or identity wrapper)
- `reports/regression_results.json` - Regression results in JSON
- `reports/regression_results.md` - Regression results in Markdown
- `reports/validation_report.md` - Validation report with CV and sensitivity metrics

## Troubleshooting

If you encounter errors:
1. Ensure all dependencies are installed
2. Check that input data exists at the specified path
3. Verify that output directories have write permissions
4. Review logs for specific error messages

## Next Steps

- For real data analysis, replace synthetic data with actual microscopy data
- Configure parameters in `code/config.py`
- Extend analysis in `code/analysis.py` for additional metrics