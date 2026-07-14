# Quickstart Guide

This guide provides the commands to run the full analysis pipeline for the project "The Influence of Metacognitive Awareness on Reality Testing".

## Prerequisites

- Python 3.8+
- Install dependencies: `pip install -r requirements.txt`

## Execution Order

Run the following commands in sequence. Each step depends on the previous one completing successfully.

### Step 1: Validate Data Availability (T004)
Checks for the existence of a valid behavioral dataset.
```bash
python code/data/validate_data_availability.py
```

### Step 2: Download Data (T005)
Fetches the valid behavioral dataset identified in Step 1.
```bash
python code/data/download.py
```

### Step 3: Validate Downloaded Data (T006)
Validates the downloaded dataset for required fields.
```bash
python code/data/validate_data.py
```

### Step 4: Preprocess Data (T012)
Extracts trial-wise data into a clean CSV format.
```bash
python code/data/preprocess.py
```

### Step 5: Run Full Analysis Pipeline (T014, T015, T020, T026, T027, T016, T022, T028)
Executes the complete analysis including correlation, bootstrap, regression, modality filtering, robustness checks, and report generation.
```bash
python code/analysis.py
```

### Step 6: Validate Outputs (Optional)
Validates that all expected output files were generated.
```bash
python code/quickstart_validator.py
```

## Expected Outputs

After successful execution, the following files should exist in the `data/` directory:

- `data/derived/trial_data.csv`
- `data/derived/visual_trials.csv`
- `data/derived/auditory_trials.csv`
- `data/results/bootstrap_config.json`
- `data/results/primary_analysis.json`
- `data/results/regression_analysis.json`
- `data/results/robustness_analysis.json`