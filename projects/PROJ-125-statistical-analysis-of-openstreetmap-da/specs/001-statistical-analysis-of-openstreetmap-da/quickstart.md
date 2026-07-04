# Quickstart: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to AWS Open Data (for MODIS/Landsat) - No API key required for public datasets, but credentials may be needed for some tools.
- Internet access (for Overpass API).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: This installs `rasterio`, `geopandas`, `pysal`, `mgwr`, `overpy`, `xarray`, `netCDF4`, `scikit-learn`, `statsmodels`.*

## Running the Pipeline

The pipeline is executed in sequential phases. Ensure you have sufficient disk space and RAM.

### Phase 1: Data Ingestion and Alignment
Downloads OSM data and satellite thermal imagery, then aligns them to a 30m grid.
```bash
python code/01_ingest/fetch_osm.py --cities NYC,CHI,LA
python code/01_ingest/fetch_thermal.py --years 2018,2019,2020,2021,2022
python code/01_ingest/align_rasters.py --output data/processed/aligned_grid
```

### Phase 2: Exploratory Data Analysis (EDA)
Calculates correlations, Moran's I, and VIF.
```bash
python code/02_eda/spatial_stats.py --input data/processed/aligned_grid --output data/processed/eda_results.json
```

### Phase 3: Spatial Modeling
Fits OLS, GWR, and SAR models with spatial cross-validation.
```bash
python code/03_modeling/fit_models.py --input data/processed/aligned_grid --output data/processed/model_results.json
```

### Phase 4: Validation and Reporting
Performs permutation tests and generates final metrics.
```bash
python code/04_validation/perm_test.py --input data/processed/model_results.json --output data/processed/final_report.json
```

## Verifying Results

1.  Check `data/processed/final_report.json` for R² and RMSE values.
2.  Verify that `GWR` shows a statistically significant improvement over `OLS` (if the hypothesis holds).
3.  Ensure all p-values are corrected using Benjamini-Hochberg.

## Troubleshooting

- **Memory Error**: If the process exceeds 7GB RAM, reduce the tile size in `code/01_ingest/align_rasters.py`.
- **Overpass API Timeout**: The script includes retries. If it fails, check network connectivity or reduce the query area.
- **Missing Satellite Data**: The script skips pixels with >50% cloud cover. Ensure the `data/raw/thermal` directory contains valid files.
