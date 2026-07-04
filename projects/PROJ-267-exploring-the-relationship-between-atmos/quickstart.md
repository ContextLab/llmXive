# Quickstart Guide: Atmospheric River Gravity Correlation

This guide provides instructions for installing dependencies, obtaining data sources, running the analysis pipeline, and verifying expected outputs for the PROJ-267 project.

## Installation

1. **Clone the repository** and navigate to the project root:
 ```bash
 cd projects/PROJ-267-exploring-the-relationship-between-atmos
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python3 -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies** from `code/requirements.txt`:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Sources

This project relies on two primary external datasets. The ingestion scripts (`code/01_data_ingestion.py`) will automatically fetch these if they are not present in `data/raw/`.

### 1. GRACE-FO Mascon Solutions
- **Source**: NASA JPL GRACE-FO Mascon Solutions (RL06)
- **URL**: `
- **Description**: Monthly gravity field solutions in mascon format.
- **Local Path**: `data/raw/grace-fo/`
- **Access**: The ingestion script uses the `requests` library to download netCDF or CSV exports. Ensure your environment has internet access.

### 2. NOAA CPC Atmospheric River Catalog
- **Source**: NOAA Climate Prediction Center (CPC) AR Catalog
- **URL**: `
- **Description**: Daily atmospheric river event data including Integrated Water Vapor Transport (IWVT).
- **Local Path**: `data/raw/noaa-ar/`
- **Access**: The ingestion script fetches CSV archives directly from the NOAA server.

## Run Commands

Execute the pipeline in the following order to reproduce the analysis:

### Step 1: Verify Citations (Optional but Recommended)
Validates that all external data sources and references are reachable and consistent.
```bash
python code/00_verify_citations.py
```
*Exits with code 1 if any citation fails.*

### Step 2: Data Ingestion
Downloads raw data and saves to `data/raw/`.
```bash
python code/01_data_ingestion.py
```
*Outputs*:
- `data/raw/grace-fo/grace-fo-raw.csv` (or netCDF)
- `data/raw/noaa-ar/noaa-ar-raw.csv`

### Step 3: Preprocessing
Applies corrections (degree-1, C20), smoothing, and monthly aggregation.
```bash
python code/02_preprocessing.py
```
*Outputs*:
- `data/processed/grace-fo-preprocessed.csv`
- `data/processed/noaa-ar-preprocessed.csv`

### Step 4: Merge Output
Combines datasets into a single time-series.
```bash
python code/03_merge_output.py
```
*Outputs*:
- `data/processed/merged_monthly.csv`

### Step 5: Correlation Analysis
Computes Pearson correlations with lag windows and bootstrap corrections.
```bash
python code/04_correlation.py
python code/05_bootstrap_correction.py
```
*Outputs*:
- `data/processed/correlation_results.json`

### Step 6: Control Validation
Validates results against a control region and noise floor.
```bash
python code/06_control_validation.py
```
*Outputs*:
- `data/processed/control_validation_report.md`

### Step 7: Visualization & Reporting
Generates plots and the final sensitivity report.
```bash
python code/07_visualization_timeseries.py
python code/08_visualization_scatter.py
python code/09_visualization_spatial.py
python code/10_sensitivity_report.py
```
*Outputs*:
- `output/timeseries_overlay.png`
- `output/scatter_regression.png`
- `output/spatial_anomaly_map.png`
- `docs/sensitivity_report.md`

## Expected Outputs

Upon successful completion of the full pipeline, the following artifacts must exist:

| File Path | Description |
|:--- |:--- |
| `data/processed/merged_monthly.csv` | Merged time-series of AR intensity and gravity anomalies. |
| `data/processed/correlation_results.json` | Statistical results including p-values and confidence intervals. |
| `output/timeseries_overlay.png` | Time-series plot of AR events vs. gravity anomalies. |
| `output/scatter_regression.png` | Scatter plot with regression line. |
| `output/spatial_anomaly_map.png` | Spatial map of gravity anomalies. |
| `docs/sensitivity_report.md` | Final report with threshold stability analysis. |

**Note**: If `data/raw/` is empty, the ingestion scripts will attempt to download data from the URLs listed above. If network access is restricted, download the datasets manually from the source URLs and place them in the corresponding `data/raw/` subdirectories.

## Validation

To verify the integrity of the output schema and language compliance:
```bash
python -m pytest tests/contract/ -v
```

To run the full integration test:
```bash
python -m pytest tests/integration/ -v
```