# Quickstart Guide

## Prerequisites

- Python 3.11+
- Materials Project API key (set as `MP_API_KEY` environment variable)

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Set your API key:
 ```bash
 export MP_API_KEY="your_api_key_here"
 ```

## Run the Pipeline

Execute the full pipeline:

```bash
# Step 1: Download CIF files (T007, T008)
python code/download.py --limit 50 --output data/raw/cif/

# Step 2: Construct networks (T009, T010, T011, T012)
python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/

# Step 3: Compute metrics (T013, T014, T015, T015b)
python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv

# Step 4: Analyze correlations (T016, T017, T018)
python code/analyze.py --input data/processed/metrics.csv --output results/

# Step 5: Generate report (T025)
python code/report.py --output results/final_report.md
```

## Validate Results

Check that all artifacts were created:

```bash
python code/validate_artifacts.py
```

Expected outputs:
- `data/raw/cif/` - Contains ≥50 CIF files
- `data/processed/networks/` - Contains ≥50 graph pickle files
- `data/processed/metrics.csv` - Network metrics and thermal conductivity
- `results/correlations.json` - Correlation analysis results
- `results/model_performance.json` - Model performance metrics
- `results/final_report.md` - Final research report

## Troubleshooting

- If you get rate limit errors, wait a few minutes and retry.
- Ensure your API key is valid and has access to thermal conductivity data.
- Check logs in `logs/` directory for detailed error messages.