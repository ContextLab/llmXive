# Quick Start Guide

This guide outlines the steps to run the full analysis pipeline.

## Prerequisites
- Python 3.11+
- Docker (for fMRIPrep)
- OpenNeuro dataset access credentials (if required)

## Step 1: Environment Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Data Download (User Story 1)
Run the download script to fetch OpenNeuro ds004285 data:
```bash
python code/preprocessing/download_openneuro.py
```
This populates `data/raw/` with NIfTI files for at least 50 subjects. [UNRESOLVED-CLAIM: c_fa076bba — status=not_enough_info]

## Step 3: Preprocessing (User Story 1)
Execute fMRIPrep via the provided shell script:
```bash
bash code/preprocessing/run_fmriprep.sh
```
*Note: Requires Docker and sufficient disk space.*

## Step 4: Time Series Extraction (User Story 1)
```bash
python code/preprocessing/extract_timeseries.py
```

## Step 5: Behavioral Data Extraction (User Story 4)
```bash
python code/behavioral/extract_openneuro_scores.py
```

## Step 6: Merge Datasets (User Story 4)
```bash
python code/behavioral/merge_datasets.py
```

## Step 7: Compute Topology Metrics (User Story 2)
```bash
python code/topology/compute_connectivity.py
python code/topology/compute_metrics.py
```

## Step 8: Correlation Analysis (User Story 3)
```bash
python code/analysis/correlation_analysis.py
python code/analysis/generate_plots.py
```

## Step 9: Reproducibility Check
```bash
python code/analysis/reproducibility_check.py
```

## Expected Outputs
- `data/processed/merged_dataset.csv`: Combined fMRI and behavioral data
- `data/processed/topology_metrics_raw.json`: Network metrics
- `data/processed/report.md`: Final analysis report
- `data/figures/`: Generated plots

## Troubleshooting
- **Docker errors**: Ensure Docker daemon is running.
- **Missing data**: Verify OpenNeuro credentials and dataset availability.
- **Memory errors**: Reduce the number of subjects processed in parallel.
