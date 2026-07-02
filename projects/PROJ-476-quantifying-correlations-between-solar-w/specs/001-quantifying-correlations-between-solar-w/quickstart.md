# Quickstart: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Prerequisites
- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (or a local machine with ≤ 7 GB RAM).

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-476-quantifying-correlations-between-solar-w
pip install -r code/requirements.txt
```

## Running the Pipeline

> **Important**: The NOAA Kp/Dst dataset currently lacks a verified download URL. The pipeline will abort with a clear error until a verified source is added (see Constitution Principle II).

### 1. Fetch & Validate
```bash
python code/main.py fetch --start 1998-01-01 --end 2020-12-31
```
Creates `data/processed/synced.csv` (no NaNs).

### 2. Compute Global Thresholds
```bash
python code/main.py compute-thresholds
```
Generates `artifacts/thresholds/global_threshold.json`.

### 3. Correlation Analysis
```bash
python code/main.py analyze --data data/processed/synced.csv --lags 0,1,2,3,6
```
Outputs `artifacts/correlations.csv`.

### 4. Validation (held‑out 2018‑2020)
```bash
python code/main.py validate --data data/processed/synced.csv --test-start 2018-01-01 --test-end 2020-12-31
```
Produces PNGs under `artifacts/plots/` (≤ 5 MB each) and `artifacts/reports/validation_report.md`.

## Expected Outputs
- `data/processed/synced.csv` – aligned, gap‑filled (no NaNs).  
- `artifacts/thresholds/global_threshold.json` – Neff & Bonferroni α_adj.  
- `artifacts/correlations.csv` – 30 rows of results.  
- PNG heatmaps & time‑series overlays (≤ 5 MB).  
- `validation_report.md` – summary of effect‑size and significance.
