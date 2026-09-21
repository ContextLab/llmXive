# Quickstart Guide

## Prerequisites
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Data Preparation
1. Download or place raw data in `data/raw/`
2. Ensure `data/config.yaml` exists with required fields (mass, radius, material_type, etc.)

## Run the Pipeline

### Step 1: Generate Test Data (Optional, for verification)
```bash
python code/generate_test_params.py
python code/generate_test_data.py
```

### Step 2: Ingest Data and Calculate Energies
```bash
python code/ingestion.py --data-source data/raw/your_data.csv --seed 42
```

### Step 3: Run Full Analysis
```bash
python code/main.py
```

## Expected Outputs
- `data/derived/energy_samples.csv`: Final energy data
- `artifacts/statistical_results.json`: Statistical analysis results
- `artifacts/regression_results.json`: Regression analysis results

## Troubleshooting
- Ensure `logs/` directory exists for logging
- Check `data/config.yaml` for required fields
- Verify data source path is correct
