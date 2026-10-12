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

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The pipeline is executed via a series of scripts. Run them in order:

### 1. Seed Initialization (reproducibility)

This step sets the random seeds for NumPy and the built‑in random module,
writes a log file confirming the operation, and prints a success message.
It is intended to be the first step of the quick‑start pipeline to guarantee
reproducibility.

```bash
python code/seed_init.py
```

**Expected output**
- Prints `Pipeline completed successfully` to the console. [UNRESOLVED-CLAIM: c_41788b40 — status=not_enough_info]
- Creates `logs/seed_initialization.log` containing a confirmation that the seeds were set. [UNRESOLVED-CLAIM: c_b33adfbf — status=not_enough_info]

### 2. Download and Validate Data

```bash
python code/download.py
```

**Output**: `data/raw/earthquake_*.csv`, `data/raw/pressure_*.csv`

### 3. Preprocess Data

```bash
python code/preprocess.py
```

**Output**: `data/interim/processed_earthquakes.csv`, `data/interim/pressure_anomalies.csv`, `data/interim/validation_report.json`

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

## Validation

To verify the installation and data integrity:

```bash
pytest tests/ -v
```

This will run unit tests for data loading and contract tests for schema validation.

## Notes on Scope

- This is a **pilot study** validating the methodology.
- Global data (FR-001) is blocked; only the 2018 Alaska subset (N=12) is used. [UNRESOLVED-CLAIM: c_6e90039f — status=not_enough_info]
- Climate indices (ENSO/PDO) are not stratified (FR-011).
- Refer to `docs/deviations.md` for full details on limitations.