# Quickstart Guide

This guide outlines the steps to run the full pipeline for investigating the relationship between brain network dynamics and anticipatory reward processing.

## Prerequisites

- Python 3.11+
- `pip` installed
- OpenNeuro credentials (if downloading fresh data)

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv env
 source env/bin/activate # On Windows: env\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

Execute the following commands in order to run the full analysis pipeline.
These commands assume you are in the project root directory.

### 1. Setup Directories
```bash
python code/setup_directories.py
```

### 2. Data Ingestion
Downloads HCP data for 50 subjects (or validates existing data). [UNRESOLVED-CLAIM: c_1dd88fb2 — status=not_enough_info]
```bash
python code/data_ingestion.py
```

### 3. Session Validation Metrics
Calculates pass rates for session distinctness.
```bash
python code/session_validation_metrics.py
```

### 4. Write Excluded Session IDs (T013c)
Writes the list of excluded subject IDs to CSV.
```bash
python code/write_excluded_session_ids.py
```

### 5. Preprocessing
Extracts BOLD time series using Power 264 atlas (excluding VS nodes) and VS ROI time series.
```bash
python code/preprocessing.py
```

### 6. Aggregate Ventral Striatum Activation (T016b)
Calculates mean VS activation per subject.
```bash
python code/aggregate_vs_activation.py
```

### 7. Connectivity Analysis
Computes dynamic functional connectivity and flexibility scores.
```bash
python code/connectivity.py
```

### 8. Correlation Analysis
Correlates flexibility scores with VS activation.
```bash
python code/analysis.py
```

### 9. Reporting
Generates the final markdown report.
```bash
python code/reporting.py
```

## Expected Outputs

After successful execution, the following files should exist in `data/processed/`:
- `excluded_session_ids.csv` (from T013c)
- `session_validation_metrics.json` (from T013b)
- `ventral_striatum_activation.csv` (from T016b)
- `correlation_plot.png` (from T032)
- `report.md` (from T033)