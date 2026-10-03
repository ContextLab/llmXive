# Quickstart Guide

This guide outlines the steps to run the full analysis pipeline for the project.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`
- `MP_API_KEY` environment variable set (for data download)

## Run the Pipeline

Execute the following commands in order. Each command produces specific artifacts required by the next.

### 1. Setup Directories
```bash
python code/setup_directories.py
```

### 2. Download CIF Files (Requires MP_API_KEY)
```bash
python code/download.py --limit 50 --output data/raw/cif/
```

### 3. Save CIFs and Checksums
```bash
python code/save_cifs_and_checksums.py
```

### 4. Construct Networks
```bash
python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/
```

### 5. Save Networks and Checksums
```bash
python code/save_networks.py
```

### 6. Validate Graphs
```bash
python code/validate_graphs.py
```

### 7. Compute Metrics
```bash
python code/compute_metrics.py
```

### 8. Analyze (Correlations, VIF, Filter)
```bash
python code/analyze.py
```

### 9. Train Model
```bash
python code/train_model.py
```

### 10. Stratified Cross-Validation (T023)
```bash
python code/stratified_cv.py
```

### 11. Generate Final Report
```bash
python code/report.py
```

### 12. Validate Artifacts
```bash
python code/validate_artifacts.py
```

## Expected Outputs

- `data/raw/cif/*.cif`: Downloaded CIF files
- `data/processed/networks/*.pkl`: Constructed network graphs
- `data/processed/metrics.csv`: Computed metrics
- `data/processed/filtered_features.csv`: Features after VIF filtering
- `models/thermal_predictor.pkl`: Trained linear regression model
- `results/model_performance.json`: Cross-validation results
- `results/final_report.md`: Final analysis report

## Troubleshooting

- **MP_API_KEY not set**: Ensure the environment variable is exported before running `download.py`.
- **Missing dependencies**: Run `pip install -r requirements.txt`.
- **CUDA errors**: This pipeline is CPU-only. If you encounter CUDA errors, ensure no GPU-specific code is inadvertently executed.