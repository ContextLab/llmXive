# Quickstart Guide

This guide walks you through setting up and running the full pipeline for quantifying data artifact bias.

## Prerequisites

- Python 3.11+
- pip
- git (for reproducibility manifest)

## Step 1: Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Project Initialization

```bash
# Create directory structure
python code/setup_dirs.py

# Setup linting configuration
python code/setup_linting.py
```

## Step 3: Generate Synthetic Data

```bash
python code/main.py --mode generate --n-images 50 --output data/synthetic
```

This creates:
- `data/synthetic/synth_XXX.fits`: Synthetic nebula images.
- `data/synthetic/gt_metadata.json`: Ground truth ellipticity and asymmetry.

## Step 4: Run Full Pipeline

The single command to execute all user stories:

```bash
python code/main.py --run-all
```

This sequentially runs:
1. **US1**: Inject noise, measure ellipticity bias, run regression.
2. **US2**: Inject saturation, measure asymmetry bias, run regression.
3. **US3**: Aggregate data, fit calibration models, validate, generate report.

Alternatively, run individual modes:

```bash
# Process artifacts and compute metrics (US1 & US2)
python code/main.py --mode process --input data/synthetic --output data/processed

# Calibrate models (US3)
python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json

# Validate results
python code/main.py --mode validate --input data/processed/models.json --test-set data/synthetic/validation --output data/processed/validation_results.csv
```

## Step 5: Verify Results

Check that the following files exist:

- `data/processed/noise_sweep_data.csv`
- `data/processed/saturation_sweep.csv`
- `data/processed/noise_stats.csv`
- `data/processed/saturation_stats.csv`
- `data/processed/aggregated_bias.csv`
- `data/processed/calibration_functions.json`
- `data/processed/run_manifest.json`
- `data/validation/power_analysis_report.md`
- `docs/reports/001-final-bias-analysis.md`

## Step 6: Reproducibility

The `data/processed/run_manifest.json` file contains:
- Git commit hash
- Environment variables
- Artifact parameters used
- Timestamp

To reproduce exactly:
```bash
git checkout <commit-hash-from-manifest>
python code/main.py --run-all
```

## Troubleshooting

- **Missing ground truth**: Ensure `data/synthetic/gt_metadata.json` exists. Run `--mode generate` if missing.
- **Import errors**: Verify `PYTHONPATH` includes the project root or install the project in editable mode.
- **File not found**: Check that `data/` directories were created by `setup_dirs.py`.
