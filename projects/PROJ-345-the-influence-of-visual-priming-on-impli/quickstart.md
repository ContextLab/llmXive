# Quick Start Guide

This guide provides a step-by-step walkthrough to get the research pipeline up and running quickly.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Git (for cloning the repository)

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd <project-directory>
```

## Step 2: Set Up the Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3: Verify Directory Structure

Ensure the following directories exist:

```
data/raw
data/processed
data/primes
data/targets
code/
tests/
state/
```

If any are missing, run:

```bash
python code/setup_directories.py
```

## Step 4: Initialize State

```bash
python code/run_state_init.py
```

## Step 5: Run the Full Pipeline

The main script orchestrates the entire pipeline:

```bash
python code/main.py
```

This will:
1. Ingest data from verified sources.
2. Preprocess and validate data.
3. Fit statistical models.
4. Generate reports and visualizations.

## Step 6: Validate Results

Run the validation script to ensure all outputs are correct:

```bash
python code/validation/validate_quickstart.py
```

This script checks:
- Directory structure
- Data ingestion completeness
- Preprocessing outputs
- Model convergence and metrics
- Report generation

## Step 7: Review Outputs

Key output files:

- `data/processed/linked_trials.csv`: Trial-level data with stimulus linkage.
- `data/processed/confounding_report.json`: Confounding analysis results.
- `data/processed/sensitivity_analysis.csv`: Sensitivity analysis across alpha levels.
- `state/model_convergence_metrics.json`: Model convergence statistics.
- `figures/`: Generated plots and visualizations.
- `reports/`: Final PDF report.

## Troubleshooting

### Missing Data

If data ingestion fails, verify network connectivity and the availability of the OSF/HF URLs. The system will halt if >10% images are missing.

### Model Convergence Issues

If models fail to converge, the pipeline will retry with alternative optimizers. Check `state/model_convergence_metrics.json` for details.

### PII Detection

If PII is detected in the data, the pipeline will halt and generate a security report. Review `data/security_report.json` for details.

## Next Steps

- Customize configuration in `code/config.py`.
- Extend the pipeline with additional analyses.
- Contribute to the project by submitting pull requests.

## Support

For issues or questions, please open an issue on the project repository.
