# Quick Start Guide for Granular System Analysis

## Prerequisites

- Python 3.11+
- Required packages listed in `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`. Below are the commands for each stage.

### 1. Ingestion (User Story 1)

This stage ingests particle tracking data and driving logs, computes energy components, and outputs `data/derived/energy_samples.csv`.

```bash
python code/main.py --stage ingest --data-source data/raw/particle_tracking.csv --sample-ratio 0.1
```

**Note**: Replace `data/raw/particle_tracking.csv` with the path to your actual input data.

### 2. Statistical Analysis (User Story 2)

This stage performs KS and Chi-squared tests to assess deviation from Maxwell-Boltzmann distribution.

```bash
python code/main.py --stage stats --alpha 0.01
```

### 3. Sensitivity Analysis (User Story 3)

This stage performs sensitivity analysis on decision thresholds.

```bash
python code/main.py --stage sensitivity --thresholds 0.01,0.05,0.10
```

### 4. Regression Analysis (User Story 4)

This stage performs regression analysis to relate deviation magnitude to driving frequency and material roughness.

```bash
python code/main.py --stage regression
```

### 5. Full Run

To run the entire pipeline from ingestion to regression:

```bash
python code/main.py --stage all --data-source data/raw/particle_tracking.csv --sample-ratio 0.1
```

## Dry Run

To validate configuration without running computations:

```bash
python code/main.py --dry-run --data-source data/raw/particle_tracking.csv
```

## Output Artifacts

- `data/derived/energy_samples.csv`: Final energy samples with columns: particle_id, timestamp, E_trans, E_rot, E_pot, E_vib, pot_incomplete
- `artifacts/sampling_metadata.json`: Random seed and sampling rule
- `artifacts/energy_samples.hash`: SHA-256 hash of energy_samples.csv
- `artifacts/statistical_results.json`: Statistical test results
- `artifacts/sensitivity_analysis_report.json`: Sensitivity analysis report
- `artifacts/regression_results.json`: Regression analysis results
