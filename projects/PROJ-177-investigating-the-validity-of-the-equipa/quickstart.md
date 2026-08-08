# Quickstart Guide

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Running the Pipeline

The main entry point is `code/main.py`. It accepts a `--stage` argument to select the pipeline stage.

### Full Run

To run the entire pipeline from data ingestion to regression analysis:

```bash
python code/main.py --stage all --sample-ratio 0.1 --data-source zenodo:12345
```

### Individual Stages

- **Ingestion**: Ingest data and calculate energies.
 ```bash
 python code/main.py --stage ingest --sample-ratio 0.1 --data-source zenodo:12345
 ```

- **Statistics**: Perform statistical tests on energy distributions.
 ```bash
 python code/main.py --stage stats --alpha 0.01
 ```

- **Sensitivity**: Run sensitivity analysis on thresholds.
 ```bash
 python code/main.py --stage sensitivity --thresholds 0.01,0.05,0.10
 ```

- **Regression**: Perform regression analysis on deviation drivers.
 ```bash
 python code/main.py --stage regression
 ```

### Dry Run

Validate the environment without executing heavy computation:

```bash
python code/main.py --stage all --dry-run
```

## Output Files

- `data/derived/energy_samples.csv`: Calculated energy components.
- `artifacts/statistical_results.json`: Results of KS and Chi-squared tests.
- `artifacts/sensitivity_analysis_report.json`: Sensitivity analysis results.
- `artifacts/regression_results.json`: Regression coefficients and statistics.
