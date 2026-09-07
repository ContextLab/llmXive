# Quickstart Guide: Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

This guide outlines the steps to reproduce the research results for PROJ-319.

## Prerequisites

- Python 3.11+
- Dependencies listed in `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Execution

The pipeline is executed in three main phases corresponding to the User Stories.

### Step 1: Generate Synthetic Data (T006)

Generates N synthetic planetary nebulae with known ground truth.

```bash
python code/main.py --mode generate --n-images 50 --output data/synthetic
```

*Output*: `data/synthetic/synth_*.fits`, `data/synthetic/gt_metadata.json`

### Step 2: Process Artifacts (T014, T021)

Injects noise and saturation artifacts into the synthetic data.

```bash
python code/main.py --mode process --input data/synthetic --output data/processed
```

*Output*: `data/processed/noise_sweep_*.fits`, `data/processed/sat_*.fits`

### Step 3: Run Sensitivity Sweep (T024)

Aggregates saturation results and performs statistical analysis.

```bash
python code/analysis/sensitivity_sweep.py
```

*Output*: `data/processed/saturation_sweep.csv`, `data/processed/saturation_sweep_summary.md`

### Step 4: Run Calibration & Validation (T027, T028, T030)

Fits regression models and validates corrections.

```bash
python code/analysis/regression.py
python code/analysis/validation.py
python code/analysis/power_analysis.py
```

*Output*: `data/processed/calibration_functions.json`, `data/validation/power_analysis_report.md`

## Full Pipeline Run

To run the entire pipeline sequentially:

```bash
python code/main.py --run-all
```

*Note*: Ensure `data/synthetic/gt_metadata.json` exists before running US1/US2.
Ensure `data/processed/noise_trend_report.csv` and `data/processed/saturation_sweep.csv` exist before US3.