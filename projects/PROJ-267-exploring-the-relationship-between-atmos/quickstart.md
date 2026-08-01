# Quickstart Guide: Atmospheric River Gravity Correlation

This guide provides instructions for installing dependencies, obtaining data, running the analysis pipeline, and verifying expected outputs for the PROJ-267 project.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- At least 15 GB of free disk space (for raw data and processed outputs)
- Internet connection (for data download and citation verification)

## Installation

1. **Navigate to the project directory**:
 ```bash
 cd projects/PROJ-267-exploring-the-relationship-between-atmos
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install --upgrade pip
 pip install -r code/requirements.txt
 ```

 The `requirements.txt` file includes:
 - `pandas`, `numpy`, `scipy`, `statsmodels`: Data processing and statistical analysis
 - `requests`: HTTP requests for data fetching
 - `matplotlib`, `seaborn`: Visualization
 - `pyyaml`: Configuration parsing

## Data Sources

This project relies on two primary real-world datasets. The pipeline will automatically attempt to fetch these during the ingestion phase.

### 1. GRACE-FO Mascon Solutions
- **Source**: NASA GRACE-FO Level 3 Mascon Data (RL06)
- **Access**: Fetch via the `01_data_ingestion.py` script using the NASA Earthdata API or direct download links.
- **Region**: West Coast North America (35°N-50°N, 120°W-125°W)
- **Storage**: `data/raw/grace-fo/`

### 2. NOAA CPC Atmospheric River Catalog
- **Source**: NOAA Climate Prediction Center (CPC) Atmospheric River Catalog
- **Access**: Fetch via `01_data_ingestion.py` from the NOAA public FTP/HTTP endpoints.
- **Region**: Global, filtered to West Coast NA in preprocessing.
- **Storage**: `data/raw/noaa-ar/`

> **Note**: If you encounter authentication issues with NASA Earthdata, ensure you have registered for an account and set the `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment variables.

## Running the Pipeline

The pipeline consists of sequential steps. Execute them in order from the project root.

### Step 1: Verify Citations
Validates that all referenced data sources and papers are accessible and metadata matches.
```bash
python code/00_verify_citations.py
```
- **Expected Output**: Exit code 0 if all citations are valid; non-zero if any fail.

### Step 2: Data Ingestion
Fetches raw GRACE-FO and NOAA AR data.
```bash
python code/01_data_ingestion.py
```
- **Expected Output**: Raw CSV/netCDF files in `data/raw/grace-fo/` and `data/raw/noaa-ar/`.

### Step 3: Preprocessing
Applies GRACE-FO corrections (degree-1, C20), smoothing, and monthly aggregation.
```bash
python code/02_preprocessing.py
```
- **Expected Output**: Preprocessed time-series data in `data/processed/`.

### Step 4: Merge Output
Combines GRACE-FO and AR data into a single schema-validated CSV.
```bash
python code/03_merge_output.py
```
- **Expected Output**: `data/processed/merged_monthly.csv`

### Step 5: Correlation Analysis
Computes Pearson correlations with lag windows and bootstrap corrections.
```bash
python code/04_correlation.py
python code/05_bootstrap_correction.py
```
- **Expected Output**: Correlation results in `data/processed/correlation_results.json`.

### Step 6: Control Validation
Compares target region against control regions to validate signal-to-noise.
```bash
python code/06_control_validation.py
```
- **Expected Output**: Validation report in `data/processed/control_validation.json`.

### Step 7: Visualization & Reporting
Generates time-series plots, scatter plots, and sensitivity reports.
```bash
python code/07_visualization_timeseries.py
python code/08_visualization_scatter.py
python code/09_visualization_spatial.py
python code/10_sensitivity_report.py
```
- **Expected Output**:
 - `output/timeseries_overlay.png`
 - `output/scatter_regression.png`
 - `output/spatial_anomaly_map.png`
 - `docs/sensitivity_report.md`

## Expected Outputs

Upon successful completion of the pipeline, you should find the following artifacts:

| File Path | Description |
|:--- |:--- |
| `data/processed/merged_monthly.csv` | Merged dataset with ≥90% completeness, no NaN in primary columns. |
| `data/processed/correlation_results.json` | Pearson correlations, p-values, and bootstrap CIs for lags 0-3. |
| `data/processed/control_validation.json` | Signal-to-noise analysis and null result handling. |
| `output/timeseries_overlay.png` | Time-series overlay of AR intensity and gravity anomaly. |
| `output/scatter_regression.png` | Scatter plot with regression line. |
| `output/spatial_anomaly_map.png` | Spatial map of gravity anomalies. |
| `docs/sensitivity_report.md` | Sensitivity analysis and threshold sweep results. |

## Troubleshooting

- **Citation Verification Failed**: Ensure your internet connection is active and the URLs in `docs/citations.yaml` are correct.
- **Data Fetch Errors**: If NASA/NOAA endpoints are unreachable, check the network or try again later. The script will fail loudly without synthetic fallback.
- **Memory Errors**: If processing large datasets fails, ensure you have at least 7 GB of RAM available. The pipeline is optimized for CPU-only execution.
- **Schema Validation Errors**: If `merged_monthly.csv` fails validation, check the `contracts/dataset.schema.yaml` definition and ensure the preprocessing steps are complete.

## Validation

To verify the entire pipeline end-to-end:
```bash
# Run the final validation script
python code/10_sensitivity_report.py --validate

# Run contract tests
pytest tests/contract/
```