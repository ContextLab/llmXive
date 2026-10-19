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
- `SPECIES_LIST`: list of target bird species (Latin names).  
- `THINNING_DISTANCE_KM`: default minimum distance for spatial thinning (default = 10 km).  
- `SEED`: random seed for reproducibility (default = 42).  
- `DATA_PATHS`: dictionary with keys `raw`, `processed`, `climate`, `models`, `metrics`, `logs`.

## Running the Pipeline
The pipeline is orchestrated via `code/main.py`. Each sub‑command creates the required artifacts and logs.

### Step 0 – Scaffold verification (T001)
```bash
python code/main.py scaffold
```
Creates missing `.gitkeep` files in `metrics/` and `logs/`, verifies that `.flake8` exists at the repository root, and confirms required directory placeholders.

### Step 1 – Download Data (T004, T010)
```bash
python code/main.py download
```
- Fetches historical & recent GBIF/eBird occurrences using the verified `pygbif` recipe.  
- Streams WorldClim v2.1 and CMIP6 rasters tile‑by‑tile to keep RAM low.  
- Downloads accompanying `.md5` checksum files, computes SHA‑256 for each raster, and **aborts on mismatch** (fulfills T010).  
- Populates `data/manifest.json`.

### Step 2 – Preprocess (T003)
```bash
python code/main.py preprocess
```
- Filters breeding‑season records, removes duplicates, applies spatial thinning.  
- Extracts climate variables, logs counts before/after each operation to `logs/preprocess.log` (structured via `utils/logging_config.py`).  
- Writes `data/processed/features.csv` and `metrics/data_sufficiency.json`.

### Step 3 – Train Models (FR‑004)
```bash
python code/main.py train
```
- Checks for CUDA (`utils/gpu_check.py`) and exits if a GPU is detected.  
- Performs spatial block CV, trains RF, Bioclim, and MaxEnt‑style models.  
- Saves model pickles under `models/` and logs to `logs/train.log`.

### Step 4 – Evaluate & Project (FR‑005, FR‑009, FR‑010)
```bash
python code/main.py evaluate
```
- Calculates AUC/TSS on recent occurrences (2005‑2020).  
- Projects models onto 2050 climate, computes `delta_suitability`.  
- Runs hierarchical bootstrap (10 000 iterations) and Benjamini‑Hochberg correction.  
- Outputs `metrics/model_performance.json` and `results/summary_table.csv`.

### Step 5 – Generate Report
```bash
python code/main.py report
```
Creates `reports/findings.md` containing tables, ROC curves, bootstrap CI plots, and the mandatory disclaimer:  
> **Findings are associational and assume niche stability** (FR‑008).

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| **GDAL / GEOS import errors** | System libraries missing | Install via `brew` (macOS) or `apt-get` (Ubuntu) as shown above. |
| **GBIF rate‑limit errors** | Too many rapid API calls | The downloader implements exponential back‑off; re‑run after a short wait. |
| **GPU detected & pipeline aborts** | Runner has CUDA enabled (unlikely on free tier) | Ensure `torch` is not installed, or run on a pure‑CPU runner. |
| **Checksum mismatch** | Corrupted raster download | Delete the offending file, verify internet stability, and re‑run `code/main.py download`. |
| **Insufficient records for a species** | `<100` records after thinning | Species will be flagged as `INSUFFICIENT_DATA`; check `metrics/data_sufficiency.json`. |
| **Missing `.gitkeep` or `.flake8`** | Scaffold not run | Re‑run `python code/main.py scaffold`. |

All generated files conform to the JSON/YAML schemas in `specs/001-predicting-species-distribution-shifts/contracts/`.

---
