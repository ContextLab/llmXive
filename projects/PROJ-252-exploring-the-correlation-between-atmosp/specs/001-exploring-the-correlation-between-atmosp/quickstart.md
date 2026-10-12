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

The pipeline uses deterministic library calls; no custom download script is required.

```bash
# Step 0: Verify installation (optional)
pytest tests/   # should exit with a success status

# Step 1: Load raw datasets (USGS catalog, global pressure, ENSO/PDO indices)
python - <<'PY'
from datasets import load_dataset
import pandas as pd

# USGS earthquake catalog
eq = load_dataset("mnemoraorg/usgs-global-earthquake-catalog", split="train")
print(f"Loaded {len(eq)} earthquake records")

# Global pressure dataset (streamed NetCDF)
import xarray as xr
pressure = xr.open_dataset(
    "https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc",
    chunks={"time": 30}
)
print(f"Pressure dataset time dimension: {pressure.sizes['time']}")

# ENSO/PDO climate indices
enso = load_dataset("noaa/enso-pdo-indices", split="train")
print(f"Loaded ENSO/PDO index with {len(enso)} monthly records")
PY

# Step 2: Preprocess – interpolation, anomaly calculation, filtering
python code/preprocess.py   # deterministic implementation follows the plan specification

# Step 3: Statistical analysis (KS test, permutation, sensitivity, FDR correction)
python code/analysis.py

# Step 4: Generate the final report
python code/report.py
```

### Expected Outputs

- `data/processed/analysis_ready.parquet` – analysis‑ready table.  
- `data/processed/analysis_results.json` – p‑values, effect sizes, robustness metrics.  
- `paper/results.md` – human‑readable summary with pilot disclaimer, power‑analysis note, and climate‑index stratification details.  

## Validation

Run the contract tests to ensure schema compliance:

```bash
pytest tests/contract/
```

All tests must pass (exit code 0) before proceeding to manuscript preparation.

---

