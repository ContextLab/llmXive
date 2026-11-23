# Quickstart Guide

## Prerequisites

- Python 3.11+
- Required packages in `code/requirements.txt`

## Installation

```bash
cd code
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline runs in 4 stages. Execute the main script with appropriate arguments:

```bash
# Stage 1: Download and preprocess data for a specific year
python main.py --year 2022 --input data/raw/delays_2022.csv --output data/processed/cleaned_delays.csv

# Stages 2-4: Run diagnostics and validation on existing cleaned data
python main.py --input data/processed/cleaned_delays.csv --output data/results/final_report.json
```

## Output Files

- `data/processed/cleaned_delays.csv`: Cleaned flight delay data
- `data/results/summary_report.json`: Data quality summary
- `data/results/model_comparison.json`: Model fitting metrics
- `data/results/tail_index_estimate.json`: Hill estimator results
- `data/results/log_normal_test.json`: Log-Normal discrimination test
- `data/results/model_rejection.json`: Model rejection status
- `data/results/final_report.json`: Complete pipeline results

## Validation

Run validation checks:
```bash
python validation.py
```
