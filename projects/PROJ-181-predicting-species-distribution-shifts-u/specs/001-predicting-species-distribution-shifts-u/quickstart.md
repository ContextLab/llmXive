# Quickstart: Predicting Species Distribution Shifts

## Prerequisites
- **Python** 3.11 or newer
- **System libraries**: GDAL ≥ 3.0, GEOS ≥ 3.8 (required by `geopandas` & `rasterio`)
- **Internet** access for GBIF and WorldClim downloads
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
   The project root contains a `.flake8` file (required by T001). Run:  
   ```bash
   flake8 .
   ```

## Configuration
Edit `code/config.py` to set:
- `SPECIES_LIST`: list of **10** target bird species (Latin names) to stay within CI limits.  
- `THINNING_DISTANCE_KM`: default minimum distance for spatial thinning (default = 10 km).  
- `SEED`: random seed for reproducibility (default = 42).  
- `DATA_PATHS`: dictionary with keys `raw`, `processed`, `climate`, `models`, `metrics`, `logs`.

## Running the Pipeline
The pipeline is orchestrated via `code/main.py`. Each sub‑command creates the required artifacts and logs.

### Step 0 – Scaffold verification (T001)
```bash
python code/main.py scaffold
```
Creates missing `.gitkeep` files in `metrics/` and `logs/`, places a `.flake8` file at the **repository root**, and generates an empty `requirements.txt`. This satisfies the scaffold requirements of T001 and Constitution I‑VII.

### Step 1 – Download Data (T004, T010)
```bash
python code/main.py download
```
- Streams GBIF/eBird occurrence records using the verified `pygbif` recipe.  
- Streams WorldClim v2.1 and CMIP6 rasters tile‑by‑tile to keep RAM low.  
- Downloads accompanying `.md5` checksum files, converts them to SHA‑256, **verifies each raster against its `climate_raster.schema.yaml` entry**, and **aborts on mismatch** (fulfills T010).  
- Populates `data/manifest.json` with SHA‑256, file size, and download timestamp.

### Step 2 – Preprocess (T003)
```bash
python code/main.py preprocess
```
- Filters breeding‑season records, removes duplicates, creates a bias‑layer raster, applies bias‑corrected background sampling, performs spatial thinning, conducts VIF‑based collinearity mitigation, and extracts climate variables.  
- Writes structured logs to `logs/preprocess.log` via `utils/logging_config.py`.  
- Generates `logs/preprocess_counts.yaml` (validated against `contracts/log_counts.schema.yaml`).  
- Writes `data/processed/features.csv`, `data/processed/bias_layer.tif`, and `metrics/data_sufficiency.json` (validated against `contracts/data_sufficiency.schema.yaml`).  
- Validates raw occurrence CSVs against `contracts/occurrence.schema.yaml` and the processed feature CSV against `contracts/occurrence_record.schema.yaml`.  

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
- **Calibration check** on recent test set (Brier score, calibration curve).  
- Calculates AUC/TSS on recent occurrences (2005‑2020).  
- Projects models onto 2050 climate, computes **MOP (Mobility‑Oriented Parity) similarity** to assess extrapolation risk, and derives a **composite niche‑stability score** (calibrated AUC change + MOP proportion).  
- Runs hierarchical bootstrap (**2 000** iterations) and Benjamini‑Hochberg correction across three probability thresholds (0.49, 0.55, 0.60).  
- Outputs `metrics/model_performance.json`, `results/summary_table.csv`, and `logs/evaluate.log`.  

### Step 5 – Generate Report
```bash
python code/main.py report
```
Creates `reports/findings.md` containing tables, ROC curves, calibration plots, MOP maps, bootstrap CI plots, and the mandatory disclaimer:  
> **Findings are associational and assume niche stability** (FR‑008).

All generated files conform to the JSON/YAML schemas in `specs/001-predicting-species-distribution-shifts/contracts/`.

---

