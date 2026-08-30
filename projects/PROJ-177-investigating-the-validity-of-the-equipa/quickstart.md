# Quickstart Guide

This guide describes how to run the full pipeline to investigate the validity of the equipartition theorem.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`

## Running the Pipeline

The pipeline is executed via `code/main.py`.

### Full Run

To run the entire pipeline from ingestion to regression analysis:

```bash
python code/main.py --stage all --sample-ratio 0.1
```

### Individual Stages

You can also run specific stages:

```bash
# Ingestion (T014a, T016, T016a, T017, T018)
python code/main.py --stage ingest --sample-ratio 0.1

# Statistical Analysis (T024, T025, T026, T027, T028)
python code/main.py --stage stats --alpha 0.01

# Sensitivity Analysis (T032, T033, T034)
python code/main.py --stage sensitivity --thresholds 0.01,0.05,0.10

# Regression Analysis (T038, T039, T040)
python code/main.py --stage regression
```

## Output Artifacts

The pipeline generates the following key artifacts:

- `data/derived/driving_signals.csv`: Aligned driving signals.
- `data/derived/energy_intermediate.csv`: Intermediate energy calculations.
- `data/derived/energy_samples.csv`: Final energy data with exclusions applied.
- `artifacts/statistical_results.json`: Results of KS and Chi-squared tests.
- `artifacts/sensitivity_analysis_report.json`: Sensitivity analysis report.
- `artifacts/regression_results.json`: Regression analysis results.

## Troubleshooting

- Ensure `data/raw/` contains the required input data files.
- Check `data/config.yaml` for correct material properties and parameters.
- Use `--verbose` flag for detailed logging.