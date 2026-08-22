# Quickstart Guide: Atmospheric River Gravity Correlation

This guide provides instructions for installing dependencies, running the analysis pipeline, understanding data sources, and verifying expected outputs for the PROJ-267 project.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Access to the internet (for data fetching)

## Installation

1. Navigate to the project root directory:
 ```bash
 cd projects/PROJ-267-exploring-the-relationship-between-atmos
 ```

2. Install the required dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Project Structure

- `code/`: Python scripts for data ingestion, preprocessing, analysis, and visualization.
- `data/raw/`: Raw downloaded datasets (GRACE-FO and NOAA AR).
- `data/processed/`: Processed and merged datasets.
- `contracts/`: Schema definitions for data validation.
- `tests/`: Unit and integration tests.
- `docs/`: Documentation files.
- `state/`: Project state and metadata.
- `specs/`: Feature specifications and design documents.

## Data Sources

The project utilizes two primary real-world datasets:

1. **GRACE-FO Mascon Solutions**:
 - **Source**: PO.DAAC CMR Search API
 - **URL**: `
 - **Description**: L2 Mascon RL06 data for gravity field variations.
 - **Region**: West Coast North America (35°N-50°N, 120°W-125°W).

2. **NOAA CPC Atmospheric River Catalog**:
 - **Source**: NOAA ERDDAP
 - **URL**: `
 - **Description**: Integrated Water Vapor Transport (IWVT) and AR event data.
 - **Region**: West Coast North America (35°N-50°N, 120°W-125°W).

## Run Commands

Execute the pipeline steps in the following order. Ensure you have internet access for data fetching steps.

### 1. Data Ingestion

Fetch raw GRACE-FO data:
```bash
python code/01_data_ingestion_grace.py
```

Fetch raw NOAA AR data:
```bash
python code/01_data_ingestion_noaa.py
```

### 2. Preprocessing and Merging

Apply corrections (degree-1, C20, Gaussian smoothing) and merge datasets:
```bash
python code/02_preprocessing.py
```
*Output*: `data/processed/merged_monthly.csv`

### 3. Statistical Correlation Analysis

Compute Pearson correlations with lag windows and bootstrap corrections:
```bash
python code/03_correlation.py
```

Apply bootstrap resampling and FDR correction:
```bash
python code/04_bootstrap_correction.py
```

### 4. Control Validation

Validate signal against noise floor and control regions:
```bash
python code/05_control_validation.py
```

### 5. Visualization and Reporting

Generate time-series overlay:
```bash
python code/06_visualization_timeseries.py
```

Generate scatter regression plot:
```bash
python code/07_visualization_scatter.py
```

Generate spatial anomaly map:
```bash
python code/08_visualization_spatial.py
```

Generate sensitivity report:
```bash
python code/09_sensitivity_report.py
```

### 6. Verification

Run contract tests to verify schema compliance:
```bash
pytest tests/contract/
```

Run integration tests:
```bash
pytest tests/integration/
```

## Expected Outputs

After successful execution of the pipeline, the following artifacts should exist:

- **Raw Data**:
 - `data/raw/grace-fo/` (contains downloaded GRACE-FO files with checksums)
 - `data/raw/noaa-ar/` (contains downloaded NOAA AR files with checksums)

- **Processed Data**:
 - `data/processed/merged_monthly.csv`: Monthly merged dataset containing gravity anomalies and AR intensity metrics.

- **Analysis Results**:
 - Correlation coefficients, p-values, and bootstrap confidence intervals (saved in `data/processed/` or `state/` as JSON/CSV).

- **Visualizations**:
 - `output/timeseries_overlay.png`: Time-series overlay of gravity and AR intensity.
 - `output/scatter_regression.png`: Scatter plot with regression line.
 - `output/spatial_anomaly_map.png`: Spatial map of gravity anomalies.

- **Reports**:
 - `docs/sensitivity_report.md`: Sensitivity analysis results.
 - `docs/temporal_bias_analysis.md`: Temporal aggregation bias documentation.

## Troubleshooting

- **Data Fetching Failures**: Ensure internet connectivity and that the PO.DAAC and NOAA ERDDAP endpoints are reachable. Check network proxies if behind a firewall.
- **Missing Dependencies**: Re-run `pip install -r code/requirements.txt` if import errors occur.
- **Schema Validation Errors**: Ensure that the `contracts/` directory contains the correct schema files (`dataset.schema.yaml`, `output.schema.yaml`).

## Citation Verification

Run the citation verification script to ensure all referenced URLs are valid:
```bash
python code/00_verify_citations.py
```

## License

This project is for research purposes. Data usage is subject to the terms of the respective data providers (NASA/PO.DAAC and NOAA).