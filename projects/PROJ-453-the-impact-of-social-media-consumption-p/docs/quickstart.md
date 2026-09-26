# Quickstart Guide

This guide outlines the steps to run the full analysis pipeline.

## 1. Setup

Ensure all directories are created and dependencies are installed:

```bash
python code/setup_directories.py
pip install -r code/requirements.txt
```

## 2. Feasibility Check

Verify dataset availability and schema:

```bash
python code/00_feasibility_check.py
```

## 3. Data Ingestion

Download and validate raw data:

```bash
python code/01_ingest.py
```

## 4. Variable Engineering

Compute derived variables and clean data:

```bash
python code/02_engineer.py
```

## 5. Model Fitting

Run regression analysis and sensitivity checks:

```bash
python code/03_model.py
```

## 6. Visualization

Generate plots and final report:

```bash
python code/04_visualize.py
```

## Expected Outputs

- `data/processed/participants_cleaned.csv`
- `results/models/regression_summary.json`
- `results/figures/regression_plot.png`
- `results/final_report.json`
