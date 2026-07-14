# Quickstart Guide: The Influence of Metacognitive Awareness on Reality Testing

This guide provides the commands to run the full analysis pipeline for PROJ-179.
Ensure all dependencies are installed and the project structure is correct before running.

## Prerequisites

1. Python 3.9+
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution Flow

The pipeline consists of the following steps executed in order:

1. **Data Availability Check (T004)**: Validates that a real behavioral dataset is available.
2. **Data Download (T005)**: Downloads the dataset if not present.
3. **Data Validation (T006)**: Checks for required columns (`confidence_rating`, `source_label`).
4. **Preprocessing (T012)**: Extracts trial-level data.
5. **Correlation Analysis (T014)**: Computes Hold-Out correlation (Type-2 AUC vs d').
6. **Bootstrap (T015)**: Generates 95% confidence intervals.
7. **Regression (T020)**: Hierarchical regression with covariates.
8. **Filter (T026)**: Splits data by stimulus modality.
9. **Robustness (T027)**: Modality-specific analysis.
10. **Report Generation (T016, T022, T028)**: Generates final JSON reports.

## Running the Pipeline

Execute the main analysis script which orchestrates all steps:

```bash
python code/analysis.py
```

This single command runs the full sequence:
`validate_data_availability` -> `download` -> `validate_data` -> `preprocess` -> `correlation` -> `bootstrap` -> `regression` -> `filter` -> `robustness` -> `generate_report`.

## Output Artifacts

Upon successful completion, the following files will be generated:

- `data/derived/trial_data.csv`: Preprocessed trial data.
- `data/derived/visual_trials.csv`: Visual modality subset.
- `data/derived/auditory_trials.csv`: Auditory modality subset.
- `data/results/bootstrap_config.json`: Bootstrap configuration and counts.
- `data/results/primary_analysis.json`: Primary correlation results.
- `data/results/regression_analysis.json`: Regression coefficients and diagnostics.
- `data/results/robustness_analysis.json`: Modality-specific results with corrections.

## Troubleshooting

- **Data Download Failed**: Check network connectivity and ensure the dataset URL in `code/data/download.py` is accessible.
- **Validation Failed**: Ensure the downloaded dataset contains `confidence_rating` and `source_label` columns.
- **Runtime Errors**: Check logs for specific traceback details.

## Validation

To verify the outputs:

```bash
python code/quickstart_validator.py
```