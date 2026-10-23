# Quickstart: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Prerequisites
- Python 3.11+
- Git
- Internet access (for data download)
- Sufficient free disk space (≈ 5 GB) for the streamed pressure dataset.

## Setup
```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-252-exploring-the-correlation-between-atmosp

# 2. Create and activate a virtual environment
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Run the Full Pipeline
```bash
# Step 0 – Verify installation (optional)
pytest tests/ # should exit with a successful status

# Step 0b – Initialise random seed (creates logs/seed_initialization.log)
python -m code.seed_init

# Verify seed log exists
if [ ! -f logs/seed_initialization.log ]; then
 echo "Seed initialization failed" >&2
 exit 1
fi

# Step 1 – Download required datasets (pressure + USGS catalog)
python -m code.download # performs both downloads and writes logs

# Step 2 – Preprocess the data
python -m code.preprocess

# Step 3 – Primary statistical analysis
python -m code.analysis

# Step 4 – Generate the short Markdown report
python -m code.report
```

### Expected Outputs
- `data/raw/pressure.nc` – streamed NOAA NCEP/NCAR sea‑level pressure NetCDF file.
- `data/raw/usgs_2013_2023.csv` – filtered USGS earthquake catalog (M ≥ 4.0, depth ≤ 70 km, 2013‑2023).
- `data/processed/config.yaml` – records SHA‑256 digests, record counts, and other metadata.
- `logs/download_success.log` – confirms successful acquisition with lines like:
 ```
 Pressure data downloaded: 4010 days [UNRESOLVED-CLAIM: c_81961b68 — status=not_enough_info]
 USGS catalog rows: <row‑count>
 ```
- Subsequent pipeline stages (preprocess, analysis, report) will generate additional
 artifacts under `data/interim/`, `data/processed/`, `logs/`, and `docs/`.

## Validation
Run the contract tests to ensure schema compliance:
```bash
pytest tests/contract/
```
All tests must pass (exit code 0) before proceeding to manuscript preparation.