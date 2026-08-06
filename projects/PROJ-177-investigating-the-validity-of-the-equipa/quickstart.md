# Quickstart Guide

This guide provides the commands to run the full analysis pipeline for the project.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`
- Real data source configured in `data/config.yaml` (see T062)

## Running the Pipeline

The pipeline consists of several stages that can be run individually or all at once.

### Run All Stages

To run the complete pipeline from raw data checksum to regression analysis:

```bash
python code/main.py --stage all --sample-ratio 0.1
```

### Run Individual Stages

You can also run specific stages:

```bash
# Step 1: Ingestion (compute energies)
python code/main.py --stage ingest --sample-ratio 0.1

# Step 2: Statistical Analysis (KS and Chi-squared tests)
python code/main.py --stage stats --alpha 0.01

# Step 3: Sensitivity Analysis (threshold sweeps)
python code/main.py --stage sensitivity --thresholds 0.01,0.05,0.10

# Step 4: Regression Analysis
python code/main.py --stage regression
```

## Output Files

The pipeline produces the following key outputs:

- `data/derived/energy_samples.csv` - Computed energy components for each particle/frame
- `artifacts/statistical_results.json` - Results of KS and Chi-squared tests
- `artifacts/sensitivity_analysis_report.json` - Sensitivity analysis results
- `artifacts/regression_results.json` - Regression model parameters

## Troubleshooting

### Data Source Not Configured

If you see "ERROR: Data source not configured", ensure you have updated `data/config.yaml` with a valid Zenodo or UCI dataset ID (see T062).

### Missing Dependency Files

If you see "ERROR: Dependency file data/derived/energy_samples.csv missing", run the ingestion stage first:
```bash
python code/main.py --stage ingest
```

### Test Data Rejected

The pipeline rejects files with 'test_' prefix as primary scientific input. Ensure you are using real data, not synthetic test datasets.
