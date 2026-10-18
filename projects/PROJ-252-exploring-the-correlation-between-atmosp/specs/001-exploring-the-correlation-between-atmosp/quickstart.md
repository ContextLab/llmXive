# Quickstart: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Prerequisites

- Python 3.11 or newer
- `git`
- Internet access (for data download)
- ~Adequate free disk space (≈ 2 GB; pressure data is streamed)

## Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd projects/PROJ-252-exploring-the-correlation-between-atmosp

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install frozen dependencies (exact versions are pinned in requirements.txt)
pip install -r requirements.txt
```

## Run the Full Pipeline

The pipeline follows the ordered steps required by the specification.

```bash
# Step 0: Verify installation (optional)
pytest tests/   # should exit with status 0

# Step 0b: Initialise random seed (creates logs/seed_initialization.log)
python -m code.seed_init

# Step 1: Download raw datasets (USGS catalog, pressure via verified HuggingFace subset, ENSO/PDO, ERA5 covariates)
python -m code.download

# Step 2: Preprocess – interpolation, anomaly calculation, filtering, control‑window matching
python code/preprocess.py

# Step 3: Statistical analysis (KS test, block‑permutation, hierarchical bootstrap, bootstrap resampling, sensitivity, FDR correction, mixed‑effects supplement)
python code/analysis.py

# Step 4: Generate the final report
python code/report.py
```

### Expected Outputs

- `data/raw/usgs_2013_2023.csv` – USGS earthquake catalog (M ≥ 4.0, depth ≤ 70 km).  
- Pressure data is **streamed** from `noaa/ncep-reanalysis-pressure`; no persistent NetCDF file is written.  
- `data/raw/enso_pdo.csv` – ENSO/PDO climate indices.  
- `data/raw/era5_covariates.parquet` – temperature & humidity covariates used for matching.  
- `logs/seed_initialization.log` – confirms random seed set (required by FR‑008).  
- `data/processed/analysis_ready.parquet` – analysis‑ready table.  
- `data/processed/analysis_results.json` – statistical results, effect sizes, robustness metrics.  
- `docs/pilot_report.md` – human‑readable summary with associational framing, power‑analysis note, and all reporting metrics.  

## Validation

Run the contract tests to ensure schema compliance:

```bash
pytest tests/contract/
```

All tests must pass (exit code 0) before proceeding to manuscript preparation.
