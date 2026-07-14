# Quickstart Guide: Atmospheric River Gravity Correlation

This guide provides instructions for installing dependencies, obtaining data sources, running the analysis pipeline, and verifying expected outputs for the **Atmospheric River Gravity Correlation** project.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git (for cloning the repository)
- Internet connection (to fetch external datasets)

## Installation

1. **Navigate to the project root:**
 ```bash
 cd projects/PROJ-267-exploring-the-relationship-between-atmos
 ```

2. **Create and activate a virtual environment (recommended):**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies:**
 ```bash
 pip install -r code/requirements.txt
 ```
 *Dependencies include: pandas, numpy, scipy, statsmodels, requests, matplotlib, seaborn, pyyaml, flake8.*

4. **Verify citation integrity (Required before Phase 0):**
 Run the citation verification script to ensure all external references are valid and reachable per Constitution Principle II.
 ```bash
 python code/00_verify_citations.py
 ```
 *This script will exit with a non-zero status code if any URL is unreachable or if title-token overlap is below 0.7.*

## Data Sources

The pipeline requires two primary external datasets. These are fetched automatically by the ingestion script, but manual inspection is available.

1. **GRACE-FO Mascon Solutions:**
 - **Source:** NASA JPL RL06 GRACE-FO Mascon Solutions
 - **Access:** Fetched via `requests` from the official NASA PO.DAAC API or direct FTP mirror.
 - **Local Storage:** `data/raw/grace-fo/`
 - **Format:** NetCDF/CSV (processed to monthly averages)

2. **NOAA CPC Atmospheric River Catalog:**
 - **Source:** NOAA Climate Prediction Center (CPC)
 - **Access:** Fetched via HTTP from the NOAA CPC data archive.
 - **Local Storage:** `data/raw/noaa-ar/`
 - **Format:** CSV (Integrated Water Vapor Transport and AR event metadata)

## Running the Pipeline

Execute the scripts in the following order to reproduce the analysis.

### Step 1: Data Ingestion
Fetches raw data from external sources and saves to `data/raw/`.
```bash
python code/01_data_ingestion.py
```
*Expected Output:* Raw data files in `data/raw/grace-fo/` and `data/raw/noaa-ar/` with accompanying checksums.

### Step 2: Preprocessing
Applies GRACE-FO corrections (degree-1, C20), Gaussian smoothing, and monthly aggregation.
```bash
python code/02_preprocessing.py
```
*Expected Output:* Preprocessed CSVs in `data/processed/` (intermediate files).

### Step 3: Merge Output
Merges GRACE-FO and NOAA AR data into a single time-series.
```bash
python code/03_merge_output.py
```
*Expected Output:* `data/processed/merged_monthly.csv`

### Step 4: Correlation Analysis
Computes Pearson correlations with lag windows, bootstrap resampling, and autocorrelation correction.
```bash
python code/04_correlation.py
python code/05_bootstrap_correction.py
```
*Expected Output:* Correlation metrics and bootstrap confidence intervals printed to console and saved to `data/processed/correlation_results.json`.

### Step 5: Control Validation
Compares target region correlations against control regions and validates signal against noise floor.
```bash
python code/06_control_validation.py
```
*Expected Output:* Validation report in `data/processed/control_validation_results.json`.

### Step 6: Visualization & Reporting
Generates diagnostic plots and the final sensitivity report.
```bash
python code/07_visualization_timeseries.py
python code/08_visualization_scatter.py
python code/09_visualization_spatial.py
python code/10_sensitivity_report.py
```
*Expected Output:*
- `output/timeseries_overlay.png`
- `output/scatter_regression.png`
- `output/spatial_anomaly_map.png`
- `docs/sensitivity_report.md`

## Expected Outputs

Upon successful completion of the pipeline, the following artifacts should exist:

| Path | Description |
|:--- |:--- |
| `data/processed/merged_monthly.csv` | Merged dataset with ≥90% completeness, no NaN in primary columns. |
| `data/processed/correlation_results.json` | Correlation coefficients, p-values, and bootstrap CIs. |
| `data/processed/control_validation_results.json` | Control region comparison and noise floor validation. |
| `output/timeseries_overlay.png` | Time-series overlay of AR intensity and gravity anomalies. |
| `output/scatter_regression.png` | Scatter plot with regression line and confidence bands. |
| `output/spatial_anomaly_map.png` | Spatial distribution of gravity anomalies. |
| `docs/sensitivity_report.md` | Sensitivity analysis and causal language compliance check. |

## Troubleshooting

- **Network Errors:** Ensure internet connectivity is available for `01_data_ingestion.py`.
- **Missing Data:** If `merged_monthly.csv` has <90% rows, check `logs/preprocessing.log` for skipped months.
- **Citation Failures:** If `00_verify_citations.py` fails, update the `specs/citations.yaml` file with corrected URLs.

## Validation

To validate the entire pipeline end-to-end:
```bash
python code/10_sensitivity_report.py --validate
pytest tests/contract/test_output_schema.py
```