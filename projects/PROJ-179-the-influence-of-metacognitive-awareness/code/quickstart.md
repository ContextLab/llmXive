# PROJ-179: Quickstart Guide

## Overview

This project analyzes the influence of metacognitive awareness on reality testing accuracy.
The pipeline validates data availability, downloads behavioral datasets, preprocesses trials,
computes signal detection theory metrics, and performs correlation and regression analyses.

## Prerequisites

- Python 3.9+
- Required packages listed in `requirements.txt`

## Setup

```bash
cd projects/PROJ-179-the-influence-of-metacognitive-awareness
python -m venv code/.venv
source code/.venv/bin/activate # On Windows: code\\.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Execution Pipeline

Run the following commands in order to execute the full analysis pipeline:

```bash
# Phase 2: Foundational (Data Validation & Download)
python code/data/validate_data_availability.py
python code/data/download.py
python code/data/validate_data.py

# Phase 3: User Story 1 - Primary Analysis
python code/data/preprocess.py
python code/src/analysis/correlation.py
python code/src/analysis/bootstrap.py
python code/src/report/generate.py

# Phase 4: User Story 2 - Hierarchical Regression
python code/src/analysis/regression.py
python code/src/analysis/diagnostics.py

# Phase 5: User Story 3 - Modality-Specific Robustness
python code/src/analysis/filter.py
python code/src/analysis/robustness.py

# Validation
python code/quickstart_validator.py
```

## Expected Outputs

After successful execution, the following files should exist:

- `data/validation_report.json` - Data validation status
- `data/derived/trial_data.csv` - Preprocessed trial data
- `data/results/primary_analysis.json` - Correlation results
- `data/results/regression_analysis.json` - Regression results
- `data/results/robustness_analysis.json` - Modality-specific results
- `data/results/bootstrap_config.json` - Bootstrap configuration

## Troubleshooting

- If `validate_data_availability.py` fails, check that a valid behavioral dataset exists.
- If `download.py` fails, verify network connectivity and dataset URL.
- If analysis scripts fail, check that all prerequisite files exist in `data/`.
