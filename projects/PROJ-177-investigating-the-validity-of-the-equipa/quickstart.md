# Quickstart Guide: Investigating the Validity of the Equipartition Theorem

This guide walks you through running the full analysis pipeline for granular systems.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Configuration

Ensure `data/config.yaml` exists with required fields:
```yaml
mass: 0.01
inertia: 0.0001
frequency_bins: [10, 20, 30, 40, 50]
material_type: steel
```

## Running the Pipeline

### 1. Dry Run (Validation)

Validate the environment and dependencies without executing:
```bash
python code/main.py --stage all --dry-run
```

### 2. Full Execution

Run the complete pipeline with a sample ratio of 0.1:
```bash
python code/main.py --stage all --sample-ratio 0.1
```

### 3. Individual Stages

You can also run specific stages:

**Ingestion:**
```bash
python code/main.py --stage ingest --data-source data/raw/particle_tracking.csv --sample-ratio 0.1
```

**Statistics:**
```bash
python code/main.py --stage stats --alpha 0.01
```

**Sensitivity:**
```bash
python code/main.py --stage sensitivity --thresholds 0.01,0.05,0.10
```

**Regression:**
```bash
python code/main.py --stage regression
```

## Output Artifacts

After successful execution, the following artifacts will be generated:

- `data/derived/energy_samples.csv`: Calculated energy components
- `artifacts/statistical_results.json`: Statistical test results
- `artifacts/sensitivity_analysis_report.json`: Sensitivity analysis report
- `artifacts/regression_results.json`: Regression analysis results
- `artifacts/regression_diagnostic.png`: Regression diagnostic plot

## Troubleshooting

- **Missing dependency errors**: Ensure previous stages have completed successfully.
- **Data source not found**: Verify the path provided in `--data-source` exists.
- **Configuration errors**: Check `data/config.yaml` for required fields.

## Notes

- The `--sample-ratio` parameter controls the fraction of data used for large datasets.
- The `--alpha` parameter sets the significance level for hypothesis tests.
- The `--thresholds` parameter accepts a comma-separated list of alpha values for sensitivity analysis.
