# Quickstart: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to the internet (for Overpass API and AWS data)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `osmnx`, `geopandas`, `rasterio`, `pysal`, `statsmodels`.*

## Configuration

Edit `code/config.py` to define:
- `CITIES`: List of cities to analyze (e.g., `["New York", "Chicago"]`).
- `CRS`: Target projection (default: EPSG:3857).
- `RESOLUTION`: Default 30.

## Running the Pipeline

### 1. Ingest and Align Data
Download OSM data and Landsat thermal rasters, then align them to 30m.
```bash
python code/main.py --step ingest --city "New York"
```
*Output*: `data/processed/new_york_aligned.tif`

### 2. Exploratory Data Analysis (EDA)
Calculate Moran's I and correlation matrices.
```bash
python code/main.py --step eda --input data/processed/new_york_aligned.tif
```
*Output*: `data/results/eda_report.json`, `data/results/moran_i.png`

### 3. Spatial Modeling
Fit OLS, GWR, and SAR models with spatial cross-validation.
```bash
python code/main.py --step model --input data/processed/new_york_aligned.tif --cv-folds 5
```
*Output*: `data/results/model_metrics.csv`, `data/results/model_coefficients.json`

### 4. Sensitivity Analysis
Run GWR bandwidth sweep.
```bash
python code/main.py --step sensitivity --input data/processed/new_york_aligned.tif --bandwidths 100,200,500,1000
```
*Output*: `data/results/sensitivity_analysis.csv`

## Verification

- Check `data/results/model_metrics.csv` for RMSE and R² values.
- Verify `data/results/eda_report.json` contains a non-zero Moran's I.
- Ensure no `ERROR` logs regarding resolution mismatch or cloud cover thresholds.

## Troubleshooting

- **Memory Error**: Reduce the study area or enable subsampling in `config.py`.
- **Overpass API Timeout**: Increase `TIMEOUT` in `config.py` or retry.
- **Cloud Cover**: If the single date has >20% cloud, the pipeline will attempt to fetch a composite (ensure `MULTI_DATE` is enabled).
