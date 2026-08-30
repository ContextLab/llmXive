# Atmospheric River Gravity Correlation - Quickstart Guide

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-267-exploring-the-relationship-between-atmos
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Sources

This project uses two primary data sources:

- **GRACE-FO Mascon Solutions**: NASA's GRACE Follow-On mission data for gravitational potential anomalies.
 - URL: Configured in `config/urls.yaml` (PO.DAAC CMR search API)
 - Format: NetCDF files, processed to monthly CSVs

- **NOAA CPC Atmospheric River Catalog**: NOAA's catalog of atmospheric river events.
 - URL: Configured in `config/urls.yaml` (NOAA ERDDAP endpoint)
 - Format: CSV/JSON, aggregated to monthly intensity metrics

**Note**: Ensure `config/urls.yaml` is populated with valid URLs before running the pipeline.

## Running the Pipeline

Execute the full analysis pipeline in order:

```bash
# 1. Verify citations and URLs
python code/00_verify_citations.py

# 2. Ingest raw data
python code/01_data_ingestion_grace.py
python code/01_data_ingestion_noaa.py

# 3. Preprocess data
python code/02_preprocessing_grace.py
python code/02_preprocessing_noaa.py

# 4. Merge and validate datasets
python code/02_preprocessing_merge.py

# 5. Run correlation analysis
python code/03_correlation_analysis.py

# 6. Generate visualizations
python code/06_visualization_timeseries.py
python code/07_visualization_scatter.py
python code/08_visualization_spatial.py

# 7. Generate sensitivity and bias reports
python code/09_sensitivity_report.py
python code/10_temporal_bias_analysis.py

# 8. Validate frame of reference documentation
python code/11_validate_frame_of_reference.py
```

## Expected Outputs

After successful execution, the following artifacts will be generated:

### Data Artifacts
- `data/processed/merged_monthly.csv`: Merged time-series of AR intensity and gravity anomalies.
- `data/processed/correlation_results.csv`: Statistical correlation results with lags, p-values, and confidence intervals.

### Visualization Artifacts
- `output/timeseries_overlay.png`: Time-series overlay of AR intensity and gravity anomalies.
- `output/scatter_regression.png`: Scatter plot with regression line.
- `output/spatial_anomaly_map.png`: Spatial map of gravity anomalies (if spatial data available).

### Reports
- `output/sensitivity_report.md`: Sensitivity analysis of correlation thresholds.
- `output/temporal_bias_analysis.md`: Analysis of temporal aggregation bias.
- `docs/runtime_report.md`: Pipeline runtime and resource usage metrics.

## Validation

Run the completeness verification script to ensure all deliverables are present:

```bash
python code/verify_completeness.py --threshold 0.90
```

This script checks for:
- Existence and non-emptiness of all required CSV and plot files.
- Minimum row counts and absence of critical NaN values in data files.
- Presence of required documentation sections.

## Troubleshooting

- **Missing Data Files**: Ensure `data/raw/` contains downloaded files. Re-run ingestion scripts if needed.
- **Schema Validation Errors**: Check `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for format requirements.
- **Citation Verification Failure**: Update `config/urls.yaml` with correct, reachable URLs.
- **Runtime Errors**: Check `logs/` directory for detailed error traces.

## License

This project is provided for research purposes. Data usage must comply with the respective data source licenses (NASA/NOAA).