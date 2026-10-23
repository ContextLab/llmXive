# Quickstart: Predicting Species Distribution Shifts

## Prerequisites
- **Python** 3.11 or newer
- **System libraries**: GDAL ≥ 3.0, GEOS ≥ 3.8 (required by `geopandas` & `rasterio`)
- **Internet** access for GBIF/eBird and WorldClim downloads
- **Git** (to clone the repository)

## Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-181-predicting-species-distribution-shifts-u
   ```

2. **Create a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**  
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Install system dependencies** (Linux/macOS)  
   ```bash
   # macOS
   brew install gdal geos

   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y libgdal-dev libgeos-dev
   ```

5. **Verify linting configuration (T001 requirement)**  
   A `.flake8` file **must exist at the repository root**. If it is missing, run:  
   ```bash
   touch .flake8
   echo "[flake8]" > .flake8
   echo "max-line-length = 88" >> .flake8
   ```

## Repository Scaffold (T001)

Run the scaffold command to ensure required placeholder files exist:

```bash
python code/main.py scaffold
```

This command will:

- Create a `.gitkeep` file in **metrics/** and **logs/** (required by T001).  
- Ensure `.flake8` is present at the **project root** (not inside `code/`).  
- Create empty `requirements.txt` and `pyproject.toml` if they do not exist.  
- Populate each top‑level directory (`code/`, `data/raw/`, `data/processed/`, `models/`, `reports/`, `tests/`, `contracts/`) with a `.gitkeep`.  
- Populate **metrics/** and **logs/** with a `.gitkeep` to satisfy the scaffold requirement.

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`. Each sub‑command creates the required artifacts and logs.

### Step 1 – Download Data (T004, T010)
```bash
python code/main.py download
```
- Streams GBIF/eBird occurrence records (historical period covering the late 20th century up to 2000 and recent period 2005‑2020).  
- Streams WorldClim historical rasters and WorldClim CMIP6 2050 rasters tile‑by‑tile.  
- **Downloads accompanying SHA‑256 checksum files, computes local checksums, and aborts on mismatch** (fulfills FR‑016).  
- Implements exponential back‑off and retry logic to handle GBIF API rate limits (addresses T004 timeout).  
- Populates `data/manifest.json` with URLs, timestamps, file sizes, and checksums.  

### Step 2 – Preprocess (T003)
```bash
python code/main.py preprocess
```
- Filters breeding‑season records, removes duplicates, creates **two** bias‑layer rasters (historic & recent) as described in the plan, applies spatial thinning (≥ 10 km or dynamic 95th percentile), conducts VIF‑based collinearity mitigation, extracts climate variables, runs the **simulation‑based power analysis**, and writes `logs/preprocess_counts.yaml` (a non‑empty YAML list of count records conforming to `contracts/log_counts.schema.yaml`).  
- Writes `data/processed/features.csv`, `data/processed/bias_layer_historic.tif`, `data/processed/bias_layer_recent.tif`, `metrics/data_sufficiency.json`, **`metrics/data_acquisition_completeness.json`** (SC‑004 report), and logs before/after counts to `logs/preprocess_counts.yaml`.  
- All logs follow the configuration in `logs/logging_config.yaml`.

### Step 3 – Train Models (FR‑004)
```bash
python code/main.py train
```
- Checks for CUDA (`utils/gpu_check.py`) and exits with a clear log if a GPU is detected.  
- Performs spatial block CV, trains Random Forest, Bioclim, and MaxEnt‑style models (with VIF‑filtered or PCA‑reduced predictors).  
- Saves model pickles under `models/` with metadata fields **matching** `contracts/model_artifact.schema.yaml` (`modelID`, `species`, `algorithm`, `trainPeriod`, `testPeriod`, `auc`, `tss`, `filePath`, `seed`).  
- Validates each model artifact against `contracts/model_artifact.schema.yaml`.  

### Step 4 – Evaluate & Project (FR‑009, SC‑001, SC‑002)
```bash
python code/main.py evaluate
```
- **Bias‑corrected evaluation** on the recent 2005‑2020 test set using the **recent** bias‑layer (`bias_layer_recent.tif`).  
- **Calibration check** (Brier < 0.2) before any projection.  
- Calculates AUC, TSS, and Brier on recent occurrences; verifies that AUC ≥ 0.70 against a null model (SC‑001).  
- Projects models onto 2050 climate, computes **MESS** similarity, and derives a **composite niche‑stability score** (calibrated ΔAUC + MESS).  
- Runs hierarchical bootstrap (**≤ 500 iterations**) and Benjamini‑Hochberg correction across the five threshold tests **{0.40, 0.45, 0.50, 0.55, 0.60}** (FR‑009).  
- Writes `metrics/model_performance.json` (contains all fields required by `contracts/model_metrics.schema.yaml`), `results/summary_table.csv`, and `logs/evaluate.log`.  
- Generates individual `performance_metric.json` entries for each metric and validates them against `contracts/performance_metric.schema.yaml`.

### Step 5 – Generate Report
```bash
python code/main.py report
```
Creates `reports/findings.md` containing tables, ROC curves, calibration plots, MESS maps, bootstrap confidence intervals, and the mandatory disclaimer:  
> **Findings are associational and assume niche stability** (FR‑001 context).

All generated files conform to the JSON/YAML contracts in `specs/001-predicting-species-distribution-shifts/contracts/`.

---



