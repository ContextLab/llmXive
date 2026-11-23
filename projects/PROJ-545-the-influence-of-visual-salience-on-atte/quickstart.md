# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip
- ~10GB free disk space for data artifacts

## Step 1: Setup Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Download Data

Run the download stage to fetch and subset the Moral Machine dataset:

```bash
python code/main.py --stage download
```

This produces `data/raw/moral_machine_subset.csv`.

## Step 3: Compute Salience

Compute visual and text-based salience scores:

```bash
python code/main.py --stage salience
```

Output: `data/processed/salience_enriched.csv`.

## Step 4: Fit aDDM Model

Fit the augmented drift-diffusion model:

```bash
python code/main.py --stage fit
```

Output: `data/processed/addm_fitted_params.json`.

## Step 5: Model Comparison

Compare salience-augmented vs. baseline models:

```bash
python code/main.py --stage compare
```

Output: `paper/results/comparison_report.md`.

## Validation

Run tests to ensure integrity:

```bash
pytest tests/ -v
```
