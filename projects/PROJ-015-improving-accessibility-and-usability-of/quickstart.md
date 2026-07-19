# Quickstart Guide

This guide describes how to run the full research pipeline from raw data collection to final statistical analysis.

## Prerequisites

- Python 3.9+
- Dependencies installed: `pip install -r requirements.txt`

## Step 1: Data Collection (Simulation or Real)

### Option A: Run the Web Simulator (Real Data)
Run the Streamlit app to collect real participant data.
```bash
streamlit run code/simulator/app.py
```
*This generates JSON files in `data/raw/`.*

### Option B: Generate Simulated Data (CI/Pilot Only)
Use the deterministic simulator for testing the pipeline logic.
```bash
python -m code.simulator.simulator --n 50 --seed 42 --output data/raw/simulated_sessions.json
```
*Note: This is strictly for CI validation. Do not use for final research claims.*

## Step 2: Data Cleaning (T021c)

Run the cleaning pipeline to load raw JSON, exclude incomplete sessions, impute SUS scores, and coerce types.
**Output**: `data/processed/cleaned_sessions.csv`

```bash
python code/analysis/run_cleaning_pipeline.py
```

## Step 3: Statistical Analysis

Run the full analysis pipeline (ANOVA, Holm-Bonferroni, Power Analysis).
**Output**: `data/processed/metrics_summary.csv`, `data/processed/report_summary.txt`, `figures/*.png`

```bash
python code/analysis/run_analysis.py
```

## Step 4: Validation

Validate the Jupyter notebook execution.
```bash
python code/analysis/run_notebook_validation.py
```

## Verification

After running the pipeline, verify the existence of the following artifacts:
- `data/processed/cleaned_sessions.csv`
- `data/processed/metrics_summary.csv`
- `figures/completion_time.png`
- `figures/error_count.png`
- `figures/sus_score.png`

If all artifacts exist and the pipeline exits with code 0, the task is complete.