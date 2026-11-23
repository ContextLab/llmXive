# Validation & Reproducibility

## Validation Script
The `code/validation/validate_quickstart.py` script runs a full end-to-end validation of the pipeline.

## Steps
1. **Directory Structure**: Verifies all required directories exist.
2. **Data Ingestion**: Checks `data/processed/linked_trials.csv` for valid data.
3. **Preprocessing**: Validates `data/processed/stimulus_metadata.csv` and `confounding_report.json`.
4. **Modeling**: Ensures `state/model_convergence_metrics.json` is populated.
5. **Reporting**: Confirms `reports/final_analysis_report.pdf` exists and contains required sections.

## Running Validation
```bash
python code/validation/validate_quickstart.py
```

## Expected Output
- `ValidationResult` object with status `PASSED` or `FAILED`.
- Detailed logs for each step.

## Troubleshooting
If validation fails, check the logs for specific errors and ensure all prerequisites are met.
