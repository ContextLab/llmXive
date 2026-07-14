# Quick Start Guide for PROJ-179

This guide shows how to run the complete analysis pipeline for the metacognitive awareness study.

## Prerequisites

- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`

## Data Pipeline

1. **Download dataset** (T005):
 ```bash
 python code/data/download.py
 ```

2. **Validate dataset** (T006):
 ```bash
 python code/data/validate_data.py
 ```

3. **Preprocess data** (T012):
 ```bash
 python code/data/preprocess.py
 ```

## Analysis Pipeline

4. **Compute correlation metrics** (T014):
 ```bash
 python code/src/analysis/correlation.py
 ```

5. **Run bootstrap analysis** (T015):
 ```bash
 python code/src/analysis/bootstrap.py
 ```

6. **Run regression analysis** (T020):
 ```bash
 python code/src/analysis/regression.py
 ```

7. **Run diagnostics** (T021):
 ```bash
 python code/src/analysis/diagnostics.py
 ```

8. **Filter by modality** (T026):
 ```bash
 python code/src/analysis/filter.py
 ```

9. **Run robustness analysis** (T027):
 ```bash
 python code/src/analysis/robustness.py
 ```

10. **Generate reports** (T016, T022, T028):
 ```bash
 python code/src/report/generate.py
 ```

## Validation

11. **Run quickstart validator**:
 ```bash
 python code/quickstart_validator.py
 ```

## Expected Outputs

After successful completion, the following files will be created:

- `data/derived/trial_data.csv`
- `data/derived/visual_trials.csv`
- `data/derived/auditory_trials.csv`
- `data/results/bootstrap_config.json`
- `data/results/primary_analysis.json`
- `data/results/regression_analysis.json`
- `data/results/robustness_analysis.json`

## Notes

- All scripts exit with code 0 on success, non-zero on failure.
- Logs are printed to stdout with timestamps.
- The pipeline requires a valid behavioral dataset with `confidence_rating` and `source_label` columns.
