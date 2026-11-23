# Quickstart: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Prerequisites
- Python 3.11+  
- Git  
- Internet access (for data download)  
- ~Adequate free disk space (on the order of gigabytes) is required for streaming pressure data.

## Setup
```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-252-exploring-the-correlation-between-atmosp

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Run the Full Pipeline
```bash
# Step 0 – Verify installation (optional)
pytest tests/   # should exit with a successful status

# Step 0b – Initialise random seed (creates logs/seed_initialization.log)
python -m code.seed_init

# Verify seed log exists
if [ ! -f logs/seed_initialization.log ]; then
  echo "Seed initialization failed" >&2
  exit 1
fi

# Step 1 – Download the verified USGS earthquake catalog
python -m code.download_usgs

# Step 2 – Stream and download NOAA pressure reanalysis (verified URL)
python -m code.download_pressure   # streams data, no large disk footprint

# Step 3 – Preprocess: clean earthquakes, apply ocean mask, interpolate pressure,
#            compute anomalies, generate simple random control windows
python -m code.preprocess

# Step 4 – Primary statistical analysis (block‑permutation test, bootstrap CI, power analysis)
python -m code.analysis

# Step 5 – Generate the short Markdown report
python -m code.report
```

### Expected Outputs
- `data/raw/usgs_all_month.csv` – raw USGS catalog.  
- `data/interim/earthquakes_clean.parquet` – cleaned earthquake dataset.  
- `data/processed/analysis_ready.parquet` – analysis‑ready table with pressure anomalies and control windows.  
- `logs/seed_initialization.log` – records the fixed random seed (required by Constitution I).  
- `docs/report.md` – report summarizing data validation, pressure‑anomaly statistics, primary permutation‑test results (p‑value, Cohen’s d, 95 % CI), power analysis outcome, hierarchical FDR‑adjusted secondary results, and limitations.

### Extending the Pipeline (When Additional Datasets Arrive)
When verified ENSO/PDO and ERA5 temperature/humidity datasets become available, run the extended steps:

```bash
python -m code.download_climate   # streams ENSO/PDO and ERA5 covariates
python -m code.preprocess_extended
python -m code.analysis_extended
python -m code.report_extended
```

## Validation
Contract tests ensure schema compliance:

```bash
pytest tests/contract/
```

All tests must pass (exit code 0) before proceeding to manuscript preparation.
