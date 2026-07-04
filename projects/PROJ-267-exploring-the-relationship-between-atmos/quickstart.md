# Quickstart Guide: Atmospheric River Gravity Correlation

This guide provides step-by-step instructions to install dependencies, acquire real data sources, run the analysis pipeline, and verify expected outputs for the Atmospheric River Gravity Correlation project.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Installation

1. Navigate to the project root directory:
 ```bash
 cd projects/PROJ-267-exploring-the-relationship-between-atmos
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install required dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Sources

This project requires two real-world datasets. The pipeline will attempt to fetch them automatically, but manual download is available if network restrictions apply.

### 1. GRACE-FO Mascon Solutions
- **Source**: NASA GRACE-FO RL06 Mascon Solutions (CSR)
- **URL**:
- **Format**: NetCDF (.nc)
- **Region**: West Coast NA (35°N-50°N, 120°W-125°W)
- **Storage**: `data/raw/grace-fo/`

### 2. NOAA CPC Atmospheric River Catalog
- **Source**: NOAA CPC Atmospheric River Catalog
- **URL**:
- **Format**: CSV
- **Storage**: `data/raw/noaa-ar/`

*Note: The ingestion script (`01_data_ingestion.py`) includes checksum verification and version logging per Constitution Principle III and VI.*

## Running the Pipeline

Execute the following scripts in order. Each script produces specific artifacts in the `data/` or `output/` directories.

### Step 1: Data Ingestion
Fetches raw data from NASA and NOAA sources.
```bash
python code/01_data_ingestion.py
```
**Output**: Raw files in `data/raw/grace-fo/` and `data/raw/noaa-ar/` with checksums.

### Step 2: Preprocessing
Applies GRACE-FO corrections (degree-1, C20), smoothing, and monthly aggregation.
```bash
python code/02_preprocessing.py
```
**Output**: Preprocessed time-series data in `data/processed/` (intermediate files).

### Step 3: Merge Output
Combines AR and gravity data into a single CSV.
```bash
python code/03_merge_output.py
```
**Output**: `data/processed/merged_monthly.csv`

### Step 4: Correlation Analysis
Computes Pearson correlation with lag windows and bootstrap corrections.
```bash
python code/04_correlation.py
```
**Output**: Intermediate correlation results.

### Step 5: Bootstrap Correction
Applies Bonferroni correction and calculates confidence intervals.
```bash
python code/05_bootstrap_correction.py
```
**Output**: `data/processed/correlation_results.json`

### Step 6: Control Validation
Compares target region against control regions to validate signal.
```bash
python code/06_control_validation.py
```
**Output**: `data/processed/control_validation_results.json`

### Step 7: Visualization
Generates diagnostic plots.
```bash
python code/07_visualization_timeseries.py
python code/08_visualization_scatter.py
python code/09_visualization_spatial.py
```
**Output**: PNG files in `output/` directory.

### Step 8: Sensitivity Report
Sweeps correlation thresholds and validates language compliance.
```bash
python code/10_sensitivity_report.py
```
**Output**: `docs/sensitivity_report.md`

## Expected Outputs

After running the full pipeline, verify the following artifacts exist:

| File Path | Description |
|:--- |:--- |
| `data/processed/merged_monthly.csv` | Merged monthly time-series (AR intensity vs. Gravity Anomaly) |
| `data/processed/correlation_results.json` | Correlation coefficients, p-values, and bootstrap CIs |
| `data/processed/control_validation_results.json` | Control region comparison and noise floor analysis |
| `output/timeseries_overlay.png` | Time-series overlay of AR and Gravity |
| `output/scatter_regression.png` | Scatter plot with regression line |
| `output/spatial_anomaly_map.png` | Spatial map of gravity anomalies |
| `docs/sensitivity_report.md` | Sensitivity analysis and language compliance report |

## Verification

Run the contract tests to ensure schema compliance and data integrity:
```bash
pytest tests/contract/ -v
```

Run the integration tests to verify the full pipeline end-to-end:
```bash
pytest tests/integration/ -v
```

## Troubleshooting

- **Network Errors**: If data fetching fails, ensure your environment has internet access or manually download the datasets from the URLs listed above and place them in the respective `data/raw/` subdirectories.
- **Missing Dependencies**: Ensure `requirements.txt` was installed in the active virtual environment.
- **Schema Validation Failures**: Check `data/processed/merged_monthly.csv` for NaN values in primary columns; the pipeline should have logged warnings during `03_merge_output.py`.

## Documentation Requirements (FR-007)

This guide satisfies FR-007 by providing:
1. Installation instructions
2. Data source URLs and formats
3. Exact run commands for all pipeline stages
4. Expected output files and their locations