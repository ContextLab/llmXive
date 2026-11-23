# Quick Start Guide

## Prerequisites
- Python 3.11+
- pip
- ~10GB disk space (for dataset + intermediates)

## Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Initialize Environment
Create necessary directories:
```bash
python code/scripts/setup_environment.py
```

## Step 3: Fetch Data
Download the EvalVerse dataset:
```bash
python code/scripts/run_pipeline.py --stage fetch
```
*This populates `data/raw/`.*

## Step 4: Run the Pipeline
Execute the full analysis (Extraction → Training → Evaluation → Reporting):
```bash
python code/scripts/run_pipeline.py
```

## Step 5: View Results
- **Correlation Results**: `data/results/correlation_results.csv`
- **Feasibility Report**: `reports/feasibility_profile.json`
- **Sensitivity Matrix**: `data/sensitivity_matrix_full.csv`

## Verification
Check that all gates passed by inspecting `state/validation_status.json` and `state/feasibility_gate.json`.
