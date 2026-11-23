# Quickstart Guide

## Prerequisites
- Python 3.11+
- Required packages (install via `pip install -r requirements.txt`)

## Running the Pipeline

### Step 1: Load and Process Datasets
```bash
python code/loaders.py --output data/processed/
```

### Step 2: Run Full Analysis Pipeline
```bash
python code/main.py --permutations 1000 --threshold 0.3 --sweep
```

### Step 3: View Results
- Processed data: `data/processed/`
- Results: `output/results/`
- Plots: `output/plots/`
- Reports: `output/reports/`

## Validation
Run the test suite:
```bash
python -m pytest tests/ -v
```

## Troubleshooting
- If dataset loading fails, check network connectivity and UCI archive availability.
- If runtime exceeds limits, reduce `--permutations` value.
- Ensure `data/raw/checksums.json` exists after first run.