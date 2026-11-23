# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Access to the Project Implicit dataset (see Data Requirements below)

## Setup

1. **Clone the repository** (if applicable)
2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
3. **Configure data source**:
 - Option A (Remote): Set the `DATA_SOURCE_URL` environment variable to the URL of the Project Implicit dataset.
 - Option B (Local): Place your CSV file in `data/raw/` and ensure `data/raw/README.md` documents the source.

## Execution

Run the full analysis pipeline:

```bash
python code/main.py
```

This command will:
1. Load the data from `data/raw/` or fetch from `DATA_SOURCE_URL`.
2. Perform MICE imputation and variable derivation.
3. Fit the primary linear regression model.
4. Run robustness checks (bootstrap, alpha sweep, covariates).
5. Save results to `results/` and processed data to `data/processed/`.

## Expected Outputs

After successful execution, you should find the following files:

- `data/processed/imputed_data.csv`: The processed dataset.
- `results/model_summary.csv`: Primary model coefficients and p-values.
- `results/robustness_metrics.csv`: Aggregated robustness metrics.
- `results/report.pdf`: The final analysis report.

## Troubleshooting

- **Missing Data**: Ensure `data/raw/` contains a valid CSV or `DATA_SOURCE_URL` is set.
- **Import Errors**: Verify all dependencies in `requirements.txt` are installed.
- **Memory Issues**: The pipeline is designed for CPU-only execution; reduce bootstrap iterations in `config.yaml` if needed.