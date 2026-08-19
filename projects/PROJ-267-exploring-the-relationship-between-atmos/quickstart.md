# Quickstart Guide: Atmospheric River Gravity Correlation

This guide covers installation, execution, data sources, and expected outputs for the PROJ-267 project investigating the relationship between atmospheric rivers and gravity anomalies.

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Internet access (for data fetching)

## Installation

1. Navigate to the project root:
 ```bash
 cd projects/PROJ-267-exploring-the-relationship-between-atmos
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Sources

The pipeline automatically fetches real data from the following sources:

1. **GRACE-FO Mascon Solutions**:
 - Source: NASA PO.DAAC (Physical Oceanography Distributed Active Archive Center)
 - Access: Programmatic download via `code/01_data_ingestion.py`
 - Note: Requires internet connectivity. Data is saved to `data/raw/grace-fo/`

2. **NOAA CPC Atmospheric River Catalog**:
 - Source: NOAA ERDDAP (Environmental Research Division's Data Access Program)
 - Access: Programmatic download via `code/01_data_ingestion.py`
 - Note: Requires internet connectivity. Data is saved to `data/raw/noaa-ar/`

## Running the Pipeline

Execute the following scripts in order. Each script produces specific output files.

### 1. Data Ingestion
Fetches raw data from external sources.
```bash
python code/01_data_ingestion.py
```
**Outputs**:
- `data/raw/grace-fo/` (raw GRACE-FO mascon files)
- `data/raw/noaa-ar/` (raw NOAA AR catalog files)

### 2. Preprocessing
Applies corrections (degree-1, C20), smoothing, and monthly aggregation.
```bash
python code/02_preprocessing.py
```
**Outputs**:
- Preprocessed intermediate files in `data/processed/` (internal use)

### 3. Merge Output
Combines GRACE-FO and NOAA data into a single dataset.
```bash
python code/03_merge_output.py
```
**Outputs**:
- `data/processed/merged_monthly.csv` (merged time-series data)

### 4. Correlation Analysis
Computes Pearson correlations with lag windows and bootstrap corrections.
```bash
python code/04_correlation.py
```
**Outputs**:
- Correlation results (internal JSON/CSV structures)

### 5. Bootstrap Correction
Applies FDR correction and confidence intervals.
```bash
python code/05_bootstrap_correction.py
```
**Outputs**:
- Corrected statistical results

### 6. Control Validation
Compares target vs. control regions.
```bash
python code/06_control_validation.py
```
**Outputs**:
- Validation metrics

### 7. Visualization
Generates diagnostic plots.
```bash
python code/07_visualization_timeseries.py
python code/08_visualization_scatter.py
python code/09_visualization_spatial.py
```
**Outputs**:
- `output/timeseries_overlay.png`
- `output/scatter_regression.png`
- `output/spatial_anomaly_map.png`

### 8. Sensitivity Report
Generates the final sensitivity analysis report.
```bash
python code/10_sensitivity_report.py
```
**Outputs**:
- `output/sensitivity_report.md`

## Expected Outputs

After running the full pipeline, verify the following files exist:

| File Path | Description |
|:--- |:--- |
| `data/raw/grace-fo/` | Raw GRACE-FO downloaded files |
| `data/raw/noaa-ar/` | Raw NOAA AR catalog files |
| `data/processed/merged_monthly.csv` | Merged monthly dataset (≥90% completeness) |
| `output/timeseries_overlay.png` | Time-series visualization |
| `output/scatter_regression.png` | Scatter plot with regression |
| `output/spatial_anomaly_map.png` | Spatial anomaly map |
| `output/sensitivity_report.md` | Final sensitivity analysis report |

## Verification

Run the citation verification script before starting the pipeline to ensure all data sources are reachable:
```bash
python code/00_verify_citations.py
```

Run contract tests to verify schema compliance:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Data Fetch Failures**: Ensure internet connectivity and that the project has not been blocked by the source (PO.DAAC/NOAA). The scripts will fail loudly with clear error messages if data cannot be retrieved.
- **Missing Dependencies**: Re-run `pip install -r code/requirements.txt`.
- **Memory Issues**: The pipeline is optimized for 7GB RAM. If errors occur, check system resources.