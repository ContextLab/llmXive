# Quickstart Guide: Atmospheric River Gravity Correlation

This guide provides instructions for installing dependencies, fetching real data, running the analysis pipeline, and verifying expected outputs for the `PROJ-267-exploring-the-relationship-between-atmos` project.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Access to the internet (required for fetching real data from PO.DAAC and NOAA ERDDAP)

## Installation

1. Navigate to the project root directory:
 ```bash
 cd projects/PROJ-267-exploring-the-relationship-between-atmos
 ```

2. Install the required Python dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. (Optional) Verify citation validity before running the pipeline:
 ```bash
 python code/00_verify_citations.py
 ```
 This script validates that all referenced citations in `specs/001-atmospheric-river-gravity/spec.md` are reachable and match their primary sources.

## Data Sources

The pipeline relies on two real, external datasets. These are fetched automatically during the ingestion step.

1. **GRACE-FO Mascon Solutions**:
 - **Source**: NASA PO.DAAC (Physical Oceanography Distributed Active Archive Center)
 - **Endpoint**: ` (via programmatic access)
 - **Content**: Level-3 GRACE-FO mascon solutions (RL06) for terrestrial water storage anomalies.
 - **Access**: Requires no API key for public datasets, but programmatic access follows standard PO.DAAC protocols.

2. **NOAA CPC Atmospheric River Catalog**:
 - **Source**: NOAA National Centers for Environmental Information (NCEI) via ERDDAP
 - **Endpoint**: `
 - **Content**: Global Atmospheric River detection events with Integrated Water Vapor Transport (IWVT) metrics.

**Note**: The scripts are designed to fail loudly if these real sources are unreachable. Do not expect synthetic fallback data.

## Running the Pipeline

Execute the pipeline steps in the following order. Each step reads from the previous step's output or the raw data sources.

### Step 1: Data Ingestion
Fetches raw GRACE-FO and NOAA AR data and saves them to `data/raw/`.
```bash
python code/01_data_ingestion.py
```
**Expected Output**:
- `data/raw/grace-fo/`: Raw mascon data files (NetCDF/CSV).
- `data/raw/noaa-ar/`: Raw AR catalog data files (CSV).
- Console logs confirming dataset versions and checksums.

### Step 2: Preprocessing
Applies GRACE-FO corrections (degree-1, C20, smoothing) and aggregates both datasets to monthly resolution.
```bash
python code/02_preprocessing.py
```
**Expected Output**:
- `data/processed/grace-fo_monthly.csv`: Preprocessed gravity anomaly data.
- `data/processed/noaa-ar_monthly.csv`: Preprocessed AR intensity data.

### Step 3: Merge Output
Merges the preprocessed datasets into a single time-series CSV.
```bash
python code/03_merge_output.py
```
**Expected Output**:
- `data/processed/merged_monthly.csv`: The primary analysis dataset.
- **Schema Validation**: The script validates this file against `contracts/dataset.schema.yaml`.

### Step 4: Correlation Analysis
Computes Pearson correlations with lag windows, bootstrap confidence intervals, and FDR correction.
```bash
python code/04_correlation.py
```
```bash
python code/05_bootstrap_correction.py
```
**Expected Output**:
- `data/processed/correlation_results.json`: Statistical results including coefficients, p-values, and bootstrap CIs.

### Step 5: Control Validation
Validates results against a control region to distinguish signal from noise.
```bash
python code/06_control_validation.py
```
**Expected Output**:
- `data/processed/control_validation_report.json`: Comparison metrics and noise floor analysis.

### Step 6: Visualization & Reporting
Generates diagnostic plots and the final sensitivity report.
```bash
python code/07_visualization_timeseries.py
python code/08_visualization_scatter.py
python code/09_visualization_spatial.py
python code/10_sensitivity_report.py
```
**Expected Output**:
- `output/timeseries_overlay.png`
- `output/scatter_regression.png`
- `output/spatial_anomaly_map.png`
- `docs/sensitivity_report.md`

## Verification

To verify the entire pipeline and schema compliance:

1. **Run Contract Tests**:
 ```bash
 pytest tests/contract/
 ```

2. **Run Integration Tests**:
 ```bash
 pytest tests/integration/
 ```

3. **Validate Output Language**:
 ```bash
 python code/10_sensitivity_report.py --validate
 ```
 This ensures the final report contains no prohibited causal language (e.g., "causes", "effect") as per FR-007.

## Troubleshooting

- **"Name or service not known" errors**: Ensure your network connection is active. The scripts require internet access to fetch real data.
- **Missing `data/raw` files**: If `01_data_ingestion.py` fails, check the logs for specific URL access issues. The script will not generate synthetic data.
- **Schema Validation Errors**: If `03_merge_output.py` fails schema validation, inspect `data/processed/merged_monthly.csv` for missing columns or unexpected data types.