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

5. **Verify linting configuration**  
   The project root now contains a `.flake8` file (required by T001). Run:  
   ```bash
   flake8 .
   ```

## Configuration
Edit `code/config.py` to set:
- `SPECIES_LIST`: list of a limited set of target bird species (Latin names) to stay within CI limits.  
- `THINNING_DISTANCE_KM`: default minimum distance for spatial thinning (default = 10 km).  
- `SEED`: random seed for reproducibility (default = 42).  
- `DATA_PATHS`: dictionary with keys `raw`, `processed`, `climate`, `models`, `metrics`, `logs`.

## Repository Scaffold (T001)
The following placeholder files are required for CI compliance:
- `.gitkeep` in **metrics/** and **logs/** directories.  
- `.flake8` at the **repository root** (already created in step 5).  

## Running the Pipeline
The pipeline is orchestrated via `code/main.py`. Each sub‑command creates the required artifacts and logs.

### Step 0 – Scaffold verification (T001)
```bash
python code/main.py scaffold
```
Creates missing `.gitkeep` files in `metrics/` and `logs/`, places a `.flake8` file at the **repository root**, and generates an empty `requirements.txt`. Satisfies scaffold requirements of T001 and Constitution I‑VII.

### Step 1 – Download Data (T004, T010)
```bash
python code/main.py download
```
- Streams GBIF/eBird occurrence records using `pygbif`.  
- Streams WorldClim v2.1 and CMIP6 rasters tile‑by‑tile to keep RAM low.  
- Downloads accompanying checksum files, converts them to SHA‑256, **verifies each raster against its known checksum** (fails fast on mismatch).  
- Populates `data/manifest.json` with SHA‑256, file size, and download timestamp.  
- Runs the **Data‑Source Verification** task (Reference‑Validator) and records results in `data/manifest.json`.

### Step 2 – Preprocess (T003)
```bash
python code/main.py preprocess
```
- Filters breeding‑season records, removes duplicates, creates a bias‑layer raster, applies bias‑corrected background sampling (including the recent test set), performs spatial thinning, conducts VIF‑based collinearity mitigation, extracts climate variables, runs the **simulation‑based power analysis**, and writes `logs/preprocess_counts.yaml` (validated against `contracts/log_counts.schema.yaml`).  
- Writes `data/processed/features.csv`, `data/processed/bias_layer.tif`, `metrics/data_sufficiency.json`, **`metrics/data_acquisition_completeness.json`** (SC‑004 report), and logs before‑and‑after counts.

### Step 3 – Train Models (FR‑004)
```bash
python code/main.py train
```
- Checks for CUDA (`utils/gpu_check.py`) and exits with a clear log if a GPU is detected.  
- Performs spatial block CV, trains Random Forest, Bioclim, and MaxEnt‑style models (with VIF‑filtered or PCA‑reduced predictors).  
- Saves model pickles under `models/` and logs to `logs/train.log`.  
- **Validates each model artifact against `contracts/model_artifact.schema.yaml`.**

### Step 4 – Evaluate & Project (FR‑005, FR‑009, FR‑010)
```bash
python code/main.py evaluate
```
- **Bias‑corrected evaluation** on recent test set using the same bias‑layer created during preprocessing.  
- **Calibration check** (Brier < 0.2).  
- Calculates AUC/TSS on recent occurrences (2005‑2020).  
- Projects models onto 2050 climate, computes **MOP similarity** to assess extrapolation risk, and derives a **composite niche‑stability score** (calibrated ΔAUC + MOP proportion).  
- Runs hierarchical bootstrap (**500 iterations**) and Benjamini‑Hochberg correction across the five threshold tests **{0.40, 0.45, 0.50, 0.55, 0.60}** (FR‑005).  
- Outputs `metrics/model_performance.json`, `results/summary_table.csv`, and `logs/evaluate.log`.

### Step 5 – Generate Report
```bash
python code/main.py report
```
Creates `reports/findings.md` containing tables, ROC curves, calibration plots, MOP maps, bootstrap CI plots, and the mandatory disclaimer:  
> **Findings are associational and assume niche stability** (FR‑008).

All generated files conform to the JSON/YAML schemas in `specs/001-predicting-species-distribution-shifts/contracts/`.

---



