# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Configure environment variables (if needed):
 ```bash
 export HCP_CREDENTIALS="your_credentials"
 ```

## Running the Pipeline

The pipeline is executed via `code/main.py` with specific steps.

### Step 1: Download and Preprocess Data
```bash
python code/main.py --step download_preprocess --subjects 50
```

### Step 2: Extract Metrics
```bash
python code/main.py --step extract_metrics
```

### Step 3: Analyze (Correlations, PCA, Power)
```bash
python code/main.py --step analyze
```
*This step generates `data/analysis/full_metrics.csv`.*

### Step 4: Visualize and Report
```bash
python code/main.py --step viz_report
```

### Run All Steps
```bash
python code/main.py --step all --subjects 50
```

## Output Artifacts

- `data/analysis/full_metrics.csv`: Combined metrics and PCA scores.
- `figures/*.png`: Generated plots.
- `docs/report.md`: Final report.

## Validation

To validate the quickstart:
```bash
python code/tools/validate_quickstart.py
```
