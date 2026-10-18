# Quickstart: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Prerequisites

- Python 3.11 or newer
- `git`
- Internet access (for data download)
- ~Adequate free disk space (approximately GB)

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
pytest tests/   # should exit with a success status

# Step 1: Download raw datasets (NOAA pressure and USGS earthquake catalog)
python -m code.download

# Step 2: Preprocess – interpolation, anomaly calculation, filtering
python code/preprocess.py

# Step 3: Statistical analysis (KS test, permutation, bootstrap, sensitivity, FDR correction)
python code/analysis.py

# Step 4: Generate the final report
python code/report.py
```

### Expected Outputs

- `data/raw/pressure.nc` – full NOAA NCEP/NCAR sea‑level pressure NetCDF file (2013‑2023).  
- `data/raw/usgs_2013_2023.csv` – USGS earthquake catalog (M ≥ 4.0, depth ≤ 70 km).  
- `logs/download_success.log` – log confirming successful download and record counts.  
- `data/processed/analysis_ready.parquet` – analysis‑ready table.  
- `data/processed/analysis_results.json` – statistical results, effect sizes, and robustness metrics.  
- `docs/pilot_report.md` – human‑readable summary with pilot disclaimer and associational framing.  

## Validation

Run the contract tests to ensure schema compliance:

```bash
pytest tests/contract/
```

All tests must pass (exit code 0) before proceeding to manuscript preparation.
