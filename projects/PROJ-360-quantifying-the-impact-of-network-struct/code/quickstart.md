# Quickstart Guide: Quantifying Network Structure Impact on Thermal Conductivity

## Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`
- Set `MP_API_KEY` environment variable (for T007/T008)

## Environment Setup
```bash
export MP_API_KEY="your_materials_project_api_key"
```

## Pipeline Execution Steps
The following commands execute the full pipeline sequentially.

### 1. Setup Directories
```bash
python code/setup_directories.py
```

### 2. Download CIF Files (T007, T008)
```bash
python code/download.py --limit 50 --output data/raw/cif/
```

### 3. Construct Networks (T009, T010, T011)
```bash
python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/
```

### 4. Validate Graphs (T012)
```bash
python code/validate_graphs.py --input data/processed/networks/
```

### 5. Compute Metrics (T013, T014, T015)
```bash
python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv
```

### 6. Analyze Correlations (T016, T017, T018)
```bash
python code/analyze.py --task correlations
```

### 7. VIF & Filtering (T020, T021)
```bash
python code/analyze.py --task vif_filter
```

### 8. Train Model (T022, T023, T024)
```bash
python code/analyze.py --task train_model
```

### 9. Generate Report (T025, T025b)
```bash
python code/report.py
```

### 10. Validate Outputs (T028)
```bash
python code/validate_outputs.py
```

## Full Pipeline Run
To run the entire pipeline end-to-end:
```bash
python code/runtime_monitor.py
```

## Verification
Check `results/final_report.md` and `results/correlations.json` for output.