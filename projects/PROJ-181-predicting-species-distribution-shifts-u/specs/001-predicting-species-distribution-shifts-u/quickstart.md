# Quickstart: Predicting Species Distribution Shifts

## Prerequisites

- **Python**: 3.11+
- **System Dependencies**: `gdal`, `libgeos` (for `geopandas`/`rasterio`).
- **Access**: Internet connectivity for GBIF and WorldClim downloads.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-181-predicting-species-distribution-shifts-u
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify system dependencies** (Linux/Mac):
 ```bash
 # Ensure GDAL and GEOS are installed
 brew install gdal geos # macOS
 sudo apt-get install libgdal-dev libgeos-dev # Ubuntu/Debian
 ```

## Configuration

Edit `code/config.py` to define:
- `SPECIES_LIST`: List of target bird species (Latin names).
- `THINNING_DISTANCE`: Minimum distance in km (default 10).
- `SEED`: Random seed for reproducibility (default 42).
- `DATA_PATHS`: Paths to raw and processed data directories.

## Running the Pipeline

The pipeline is executed sequentially via `main.py`.

### Step 1: Download Data
Downloads historical and recent occurrence records from GBIF and climate rasters from WorldClim/CMIP6.
```bash
python code/main.py download
```
*Output*: `data/raw/occurrence_1970_2000.csv`, `data/raw/occurrence_2005_2020.csv`, `data/raw/climate/`

### Step 2: Preprocess Data
Filters, thins, and extracts climate variables.
```bash
python code/main.py preprocess
```
*Output*: `data/processed/features.csv`, `metrics/data_sufficiency.json`

### Step 3: Train Models
Trains RF, Bioclim, and MaxEnt-style models with spatial block CV.
```bash
python code/main.py train
```
*Output*: `models/*.pkl`, `logs/gpu_check.log`

### Step 4: Evaluate & Project
Projects models to 2050, calculates AUC/TSS, and runs statistical tests on `delta_Suitability`.
```bash
python code/main.py evaluate
```
*Output*: `metrics/model_performance.json`, `results/summary_table.csv`

### Step 5: Generate Report
(Optional) Generates a summary report from metrics.
```bash
python code/main.py report
```

## Troubleshooting

- **GDAL Errors**: Ensure `libgdal` is installed and `GDAL_DATA` environment variable is set.
- **GBIF Rate Limit**: The script includes exponential backoff. If it fails repeatedly, wait and retry.
- **Memory Error**: Reduce `SPECIES_LIST` size or increase swap space on the runner.
- **GPU Detected**: The pipeline will exit with code 1 if a GPU is detected (enforcing CPU-only constraint). [UNRESOLVED-CLAIM: c_dc46bd5e — status=not_enough_info] Check `logs/gpu_check.log`.

## Expected Outputs

- `metrics/model_performance.json`: JSON file containing AUC, TSS, and statistical test results for each species (including `delta_suitability`).
- `metrics/data_sufficiency.json`: Log of species with <100 records (flagged as `INSUFFICIENT_DATA`), including specific record counts and power values.
- `results/summary_table.csv`: Aggregated performance metrics with multiple-comparison corrections applied, explicitly listing threshold deltas {0.01, 0.05, 0.10}.