# Quickstart Guide: The Influence of Metacognitive Awareness on Reality Testing

This guide walks you through the end-to-end execution of the analysis pipeline for Project PROJ-179.

## Prerequisites

- Python 3.9+
- Installed dependencies (see `requirements.txt`)

## Installation

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. (Optional) Configure environment variables in `.env` if needed:
 ```bash
 cp.env.example.env
 # Edit.env to set paths, seeds, etc.
 ```

## Execution

The full analysis pipeline is executed via the `code/analysis.py` script. This script orchestrates the following steps:

1. **Data Download & Validation**: Fetches the behavioral dataset (if not present) and validates required fields.
2. **Preprocessing**: Extracts trial-level data into `data/derived/trial_data.csv`.
3. **Correlation Analysis**: Computes Hold-Out correlation between metacognitive awareness and reality testing accuracy.
4. **Bootstrap**: Generates 95% confidence intervals via bootstrapping.
5. **Regression**: Performs hierarchical regression with covariates.
6. **Modality Filter & Robustness**: Splits data by stimulus modality and re-runs correlation.
7. **Report Generation**: Aggregates all results into JSON reports.

Run the pipeline:
```bash
python code/analysis.py
```

## Output Artifacts

Upon successful completion, the following files will be generated:

- `data/derived/trial_data.csv`: Preprocessed trial-level data.
- `data/results/bootstrap_config.json`: Bootstrap configuration and runtime stats.
- `data/results/primary_analysis.json`: Primary correlation results (r, p-value, CI).
- `data/results/regression_analysis.json`: Hierarchical regression results.
- `data/results/robustness_analysis.json`: Modality-specific robustness results.
- `data/validation_report.json`: Data validation status.

## Troubleshooting

- **Data Download Failed**: Ensure network access is available. The script attempts multiple sources; if all fail, the project is blocked (see `code/data/validate_data_availability.py`).
- **Missing Columns**: If validation fails, check the source dataset for `confidence_rating` and `source_label`.
- **Runtime Errors**: Check logs in `logs/` for stack traces.

## Validation

To verify the pipeline outputs, run:
```bash
python code/quickstart_validator.py
```
This script checks for the existence and schema validity of all declared deliverables.
