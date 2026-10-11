# Quickstart: Predicting Species Distribution Shifts

Minimal steps to run the pipeline (single species or full species list).

## Prerequisites

- **Python**: 3.11+
- **System dependencies**: `gdal`, `libgeos` (for `geopandas`/`rasterio`).
- **Internet access** for GBIF and WorldClim downloads.

## Setup

```bash
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

On Ubuntu/Debian install system libs first:

```bash
sudo apt-get install libgdal-dev libgeos-dev
```

## Scaffold (one-time)

```bash
python code/scaffold.py
```

Creates `code/`, `data/raw/`, `data/processed/`, `models/`, `metrics/`,
`logs/`, `reports/`, `tests/`, `contracts/` with `.gitkeep` files.

## Configuration

Edit `code/config.py`:
- `SPECIES_LIST`: target bird species (Latin names).
- `THINNING_DISTANCE_KM`: minimum thinning distance in km (default 10).
- `SEED`: random seed (default 42).
- Paths for raw/processed data, models, and metrics.

## Run the pipeline

```bash
# 1. Download occurrences (GBIF) and climate rasters (WorldClim/CMIP6)
python code/download.py

# 2. Preprocess: breeding-season filter, thinning, climate extraction,
# VIF selection, data-sufficiency power analysis
python code/preprocess.py

# 3. Bias correction layer (run automatically before training)
python code/bias_correction.py

# 4. Train RF / Bioclim / MaxEnt-style models with spatial block CV
python code/train.py

# 5. Project to recent & 2050 climates, evaluate AUC/TSS, bootstrap
python code/evaluate.py
```

## Expected outputs

- `data/raw/occurrence_1970_2000.csv`, `data/raw/occurrence_2005_2020.csv`
- `data/raw/climate_historical/`, `data/raw/climate_recent/`, `data/raw/climate_future/`
- `data/processed/occurrence_full.csv`, `data/processed/occurrence_model.csv`
- `metrics/selected_climate_variables.json`, `metrics/data_sufficiency.json`
- `models/{species}_{algo}_historical.pkl`
- `metrics/training_metrics.csv`, `metrics/baseline_performance.csv`, `metrics/bias_null_metrics.csv`
- `metrics/evaluation_recent.csv`, `metrics/delta_suitability.csv`,
 `metrics/delta_auc_tss.csv`, `metrics/bootstrap_auc_tss.json`,
 `metrics/sensitivity_report.csv`, `metrics/final_results.csv`
- `reports/associational_disclaimer.txt`

## Troubleshooting

- **GDAL errors**: ensure `libgdal` is installed and `GDAL_DATA` is set.
- **GBIF rate limits**: the downloader sleeps between paginated requests.
- **Memory**: reduce `SPECIES_LIST` in `code/config.py`.
- **GPU detected**: the pipeline exits with code 1 (CPU-only constraint);
 see `logs/gpu_check.log`.