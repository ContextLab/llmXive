# Quickstart Guide

This guide describes how to run the full analysis pipeline for the "Effects of Gamified Habit Tracking" project.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Execution

The entire pipeline is orchestrated via a single entry point script.

### Run Full Pipeline

```bash
python code/main.py --seed 42 --n_users 500 --weeks 50
```

This command performs the following steps in order:
1. **Data Generation**: Creates `data/raw/synthetic_data.csv` and the marker file.
2. **Ingestion**: Validates schema and group sizes.
3. **Aggregation**: Converts daily logs to weekly bins.
4. **Merging**: Produces `data/processed/merged_data.csv`.
5. **Validation**: Calculates Cronbach's Alpha (`data/processed/psychometrics.json`).
6. **Modeling**: Fits mixed-effects logistic regression.
7. **Survival**: Runs Kaplan-Meier and Cox models.
8. **Robustness**: Executes bootstrapping.
9. **Reporting**: Generates `data/reports/final_analysis.html`.
10. **Versioning**: Updates `state.yaml`.

### Verify Outputs

After successful execution, verify the following files exist:
- `data/raw/synthetic_data.csv`
- `data/processed/merged_data.csv`
- `data/processed/psychometrics.json`
- `data/reports/final_analysis.html`
- `state.yaml`
