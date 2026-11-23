# Quickstart Guide

This guide provides the minimal commands to run the full pipeline end-to-end.

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
pip install -r requirements.txt
```

## Run the Pipeline

Execute the main orchestration script:

```bash
python code/main.py
```

This will:
1. Ensure all directories exist
2. Fetch real diffusion data from NIST
3. Ingest and filter for FCC self-diffusion
4. Curate data and handle missing values
5. Train Random Forest and Gradient Boosting models
6. Perform statistical validation
7. Generate sensitivity analysis
8. Produce final reports and artifacts

## Verify Artifacts

After the pipeline completes, verify that all expected artifacts exist:

```bash
python code/validation/quickstart_validator.py
```

## Expected Outputs

The pipeline produces the following key artifacts:

- `data/raw/fetched_diffusion.csv` - Raw fetched data
- `data/curated/filtered.csv` - Curated FCC self-diffusion data
- `models/final_rf.pkl` - Trained Random Forest model
- `models/final_gb.pkl` - Trained Gradient Boosting model
- `models/linear_coef.json` - Linear regression coefficients
- `reports/validation_report.json` - Statistical validation results
- `reports/sensitivity_sweep.csv` - Threshold sensitivity analysis
- `reports/sensitivity_plot.png` - Sensitivity visualization
- `reports/final_summary.md` - Human-readable summary