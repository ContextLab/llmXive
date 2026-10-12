# Quick Start Guide

This guide walks you through executing the full pipeline on the test dataset.

## Prerequisites

- Python 3.11+
- `pip`
- ~14 GB free disk space
- Internet access (for data download)

## Installation

1. **Clone and Setup**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-252-exploring-the-correlation-between-atmosp
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies** (all versions are pinned/frozen):
 ```bash
 python -m pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline is executed via a series of scripts. Run them in order:

### 1. Seed Initialization (reproducibility)

This step sets the random seeds for NumPy and the built-in `random` module,
writes a log file confirming the operation, and prints a success message.
It is intended to be the first step of the quick-start pipeline to guarantee
reproducibility.

```bash
python code/seed_init.py
```

**Expected output**
- Prints `Pipeline completed successfully` to the console and exits with code 0.
- Creates `logs/seed_initialization.log` containing a confirmation that the
 seeds (`random.seed(42)` and `np.random.seed(42)`) were set and verified.

### 2. Download and Validate Data

```bash
python code/download.py
```

**Output**: `data/raw/` NOAA pressure files and the USGS earthquake catalog,
plus `data/processed/config.yaml` and `logs/download_success.log`.

### 3. Preprocess Data

```bash
python code/preprocess.py
```

**Output**: `data/interim/masked_events.csv`, `data/interim/clean_events.csv`,
`data/interim/anomalies_raw.csv`, `data/interim/deduplicated_with_anomalies.csv`,
`data/processed/master_dataset.parquet`, `data/processed/validation_report.json`.

### 4. Generate Master Dataset

```bash
python code/generate_master_dataset.py
```

**Output**: `data/processed/master_dataset.parquet`

### 5. Run Statistical Analysis

```bash
python code/analysis.py
```

**Output**: `data/processed/statistical_results.json`

### 6. Run Robustness and Sensitivity Analysis

```bash
python code/generate_robustness_report.py
```

**Output**: `data/processed/robustness_report.json`

### 7. Generate Final Report

```bash
python code/generate_pilot_report.py
```

**Output**: `docs/pilot_report.md`

## Required-Input Provenance

- **Earthquake catalog**: USGS FDSN event API
 (`https://earthquake.usgs.gov/fdsnws/event/1/query`), 2013-2023,
 M >= 4.0, depth <= 70 km. No authentication required.
- **Atmospheric pressure**: NOAA NCEP/NCAR reanalysis daily sea-level
 pressure archive (`).
 The full global 2013-2023 download is currently blocked (see
 `docs/deviations.md`, DEV-001); the pilot uses the verified Alaska test
 subset shipped under `data/`.
- **Random seeds**: fixed at 42 via `code/__init__.py` and
 `code/seed_init.py` for full reproducibility.

## Validation

To verify the installation and data integrity:

```bash
pytest tests/ -v
```

This will run unit tests for data loading and contract tests for schema
validation.

## Notes on Scope

- This is a **pilot study** validating the methodology.
- Global data (FR-001) is blocked; only the 2018 Alaska subset (N=12) is used [UNRESOLVED-CLAIM: c_24ce3f11 — status=not_enough_info].
- Climate indices (ENSO/PDO) are not stratified (FR-011).
- Refer to `docs/deviations.md` for full details on limitations.
