# Quickstart Guide

This guide describes how to run the full pipeline end-to-end.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Execution Order

The pipeline must be run in the following order to ensure data dependencies are met.

1. **Setup Directories**:
 ```bash
 python code/setup_directories.py
 ```

2. **Ingestion (T013)**: Download and filter MedMisBench.
 ```bash
 python code/ingestion.py
 ```
 *Output*: `data/raw/medmis_subset.csv`

3. **Static Ground Truth (T020)**: Fetch PubMed facts.
 ```bash
 python code/static_ground_truth.py
 ```
 *Output*: `data/raw/static_medical_facts.json`

4. **Feature Extraction (T014, T015)**: Extract linguistic features and flag undefined ratios.
 ```bash
 python code/features.py
 ```
 *Output*: `data/processed/features.csv`

5. **Labeling (T022-T025)**: Compute semantic scores and apply labels.
 ```bash
 python code/labeling.py
 ```
 *Output*: `data/interim/labeled_responses.csv`

6. **Modeling (T029-T035)**: Run regressions and sensitivity analysis.
 ```bash
 python code/modeling.py
 ```
 *Output*: `data/results/regression_results.csv`, `data/results/sensitivity_analysis.csv`

## Full Pipeline Run

To run the entire pipeline sequentially:

```bash
python code/main.py
```

*Note*: `code/main.py` is the orchestrator script that calls the above steps in order.
