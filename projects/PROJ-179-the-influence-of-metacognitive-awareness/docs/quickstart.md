# Quickstart Guide

This guide outlines the steps to run the full analysis pipeline for the project "The Influence of Metacognitive Awareness on Reality Testing".

## Prerequisites

- Python 3.9+
- `pip`
- Internet connection (for data download)

## Installation

1. Navigate to the project root:
 ```bash
 cd projects/PROJ-179-the-influence-of-metacognitive-awareness
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline consists of several stages. Run them in order:

### 1. Validate Data Availability
Checks if a valid dataset exists.
```bash
python code/data/validate_data_availability.py
```

### 2. Download Dataset
Fetches the dataset if not present.
```bash
python code/data/download.py
```

### 3. Validate Downloaded Data
Ensures the downloaded file has required columns.
```bash
python code/data/validate_data.py
```

### 4. Preprocess Data
Extracts trial-level data.
```bash
python code/data/preprocess.py
```

### 5. Primary Analysis (Correlation)
Computes the main correlation using Hold-Out design.
```bash
python code/src/analysis/correlation.py
python code/src/analysis/bootstrap.py
```

### 6. Regression Analysis
Performs hierarchical regression with covariates.
```bash
python code/src/analysis/regression.py
python code/src/analysis/diagnostics.py
```

### 7. Robustness Analysis
Runs modality-specific analysis.
```bash
python code/src/analysis/filter.py
python code/src/analysis/robustness.py
```

### 8. Generate Reports
Consolidates results into final JSON reports.
```bash
python code/src/report/generate.py
```

## Output Artifacts

Upon successful completion, the following files will be generated:

- `data/validation_report.json`
- `data/derived/trial_data.csv`
- `data/derived/visual_trials.csv`
- `data/derived/auditory_trials.csv`
- `data/results/bootstrap_config.json`
- `data/results/primary_analysis.json`
- `data/results/regression_analysis.json`
- `data/results/robustness_analysis.json`

## Troubleshooting

- **Missing Data**: Ensure `data/validate_data_availability.py` passes before running other steps.
- **Configuration Errors**: Check `code/config/env_config.py` for correct path settings.
- **Runtime Limits**: If bootstrap analysis takes too long, it will automatically reduce the number of resamples as per `code/src/analysis/bootstrap.py`.
