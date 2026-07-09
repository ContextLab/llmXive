# Quick Start Guide

This guide walks you through executing the full pipeline on the test dataset.

## Prerequisites

- Python 3.11+
- pip
- Git (for cloning)

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 git clone <repo-url>
 cd exploring-the-correlation-between-atmosp
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution

The pipeline consists of the following stages. Run them in order:

### 1. Download and Validate Data

Fetches USGS earthquake data and verifies the absence of global pressure sources (per FR-001 deviation).

```bash
python code/download.py
```

**Output**: `data/raw/earthquake_*.csv`, `data/raw/pressure_*.csv`

### 2. Preprocess Data

Interpolates pressure grids, calculates anomalies, and filters events.

```bash
python code/preprocess.py
```

**Output**: `data/interim/processed_earthquakes.csv`, `data/interim/pressure_anomalies.csv`, `data/interim/validation_report.json`

### 3. Generate Master Dataset

Pairs earthquakes with pressure anomalies and assigns control labels.

```bash
python code/generate_master_dataset.py
```

**Output**: `data/processed/master_dataset.csv`

### 4. Run Statistical Analysis

Performs KS tests, permutation tests, and calculates effect sizes.

```bash
python code/analysis.py
```

**Output**: `data/processed/statistical_results.json`

### 5. Run Robustness and Sensitivity Analysis

Stratifies by magnitude/region and sweeps anomaly cutoffs.

```bash
python code/generate_robustness_report.py
```

**Output**: `data/processed/robustness_report.json`

### 6. Generate Final Report

Compiles all findings into a pilot report.

```bash
python code/generate_pilot_report.py
```

**Output**: `docs/pilot_report.md`

## Validation

To verify the pipeline execution:

1. Check that `data/processed/master_dataset.csv` contains exactly 12 rows (the Alaska 2018 test subset).
2. Verify `docs/pilot_report.md` exists and references `docs/deviations.md`.
3. Run the test suite:
 ```bash
 pytest tests/ -v
 ```

## Troubleshooting

- **Missing Dependencies**: Ensure you are using Python 3.11 and have installed all packages from `code/requirements.txt`.
- **Data Download Failures**: The pipeline explicitly checks for the absence of global NOAA sources. If it fails to download the test subset, verify your internet connection and USGS API availability.
- **Permission Errors**: Ensure you have write access to the `data/` and `docs/` directories.

## Notes on Scope

- This is a **pilot study** validating the methodology.
- Global data (FR-001) is blocked; only the 2018 Alaska subset (N=12) is used.
- Climate indices (ENSO/PDO) are not stratified (FR-011).
- Refer to `docs/deviations.md` for full details on limitations.
