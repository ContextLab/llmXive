# Quick Start Guide: Atmospheric River Gravity Correlation

This guide provides instructions for installing dependencies, obtaining data, and running the analysis pipeline for the "Exploring the Relationship Between Atmospheric Rivers and Gravity Anomalies" project (PROJ-267).

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Access to the internet for data fetching
- Sufficient disk space (~15 GB for raw and processed data)

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

4. Verify installation by running the citation verification script:
 ```bash
 python code/00_verify_citations.py
 ```
 This script validates all data source citations against primary metadata. It must exit with code 0 to proceed.

## Data Sources

The pipeline relies on two primary real-world datasets. The ingestion script (`01_data_ingestion.py`) will automatically download these if they are not present in `data/raw/`.

1. **GRACE-FO Mascon Solutions**
 - **Source**: NASA JPL GRACE-FO RL06 Mascons
 - **Access**: Programmatic download via `gracefo` package or direct URL.
 - **Storage**: `data/raw/grace-fo/`
 - **Note**: Requires acceptance of terms on the JPL server. The script logs the specific release version used.

2. **NOAA CPC Atmospheric River Catalog**
 - **Source**: NOAA National Centers for Environmental Information (NCEI)
 - **Access**: Direct CSV download from the NOAA AR Catalog API.
 - **Storage**: `data/raw/noaa-ar/`
 - **Note**: Contains integrated water vapor transport (IWVT) and event metadata.

## Running the Pipeline

Execute the pipeline scripts in the following order. Each script produces intermediate or final artifacts in the `data/` directory.

### Step 1: Data Ingestion
Fetches raw data from the sources listed above.
```bash
python code/01_data_ingestion.py
```
**Expected Output**:
- `data/raw/grace-fo/` (directory containing downloaded mascon files)
- `data/raw/noaa-ar/` (directory containing AR catalog CSVs)
- Log file: `logs/ingestion.log`

### Step 2: Preprocessing
Applies GRACE-FO corrections (degree-1, C20), Gaussian smoothing, and aggregates to monthly resolution.
```bash
python code/02_preprocessing.py
```
**Expected Output**:
- `data/processed/grace_monthly.csv`
- `data/processed/ar_monthly.csv`

### Step 3: Merge Output
Combines preprocessed datasets and validates schema compliance.
```bash
python code/03_merge_output.py
```
**Expected Output**:
- `data/processed/merged_monthly.csv` (Primary analysis dataset)
- Validation logs indicating schema compliance.

### Step 4: Correlation Analysis
Computes Pearson correlations with lag windows and bootstrap confidence intervals.
```bash
python code/04_correlation.py
```
**Expected Output**:
- `data/processed/correlation_results.json`

### Step 5: Bootstrap Correction
Applies Bonferroni correction and calculates final significance.
```bash
python code/05_bootstrap_correction.py
```
**Expected Output**:
- `data/processed/bootstrap_corrected_results.json`

### Step 6: Control Validation
Compares target region against control regions to validate signal magnitude.
```bash
python code/06_control_validation.py
```
**Expected Output**:
- `data/processed/control_validation_results.json`
- `data/processed/signal_noise_analysis.csv`

### Step 7: Visualization
Generates diagnostic plots.
```bash
python code/07_visualization_timeseries.py
python code/08_visualization_scatter.py
python code/09_visualization_spatial.py
```
**Expected Output**:
- `output/timeseries_overlay.png`
- `output/scatter_regression.png`
- `output/spatial_anomaly_map.png`

### Step 8: Sensitivity Report
Generates the final sensitivity analysis and validates report language.
```bash
python code/10_sensitivity_report.py
```
**Expected Output**:
- `docs/sensitivity_report.md`
- Validation log confirming absence of causal language.

## Expected Outputs Summary

Upon successful completion of the full pipeline, the following artifacts will exist:

| Path | Description |
|:--- |:--- |
| `data/processed/merged_monthly.csv` | Combined time-series of GRACE-FO gravity and AR intensity |
| `data/processed/correlation_results.json` | Raw correlation coefficients and p-values |
| `data/processed/bootstrap_corrected_results.json` | Results with multiple-comparison correction |
| `output/timeseries_overlay.png` | Visual overlay of gravity anomalies and AR events |
| `docs/sensitivity_report.md` | Final report with sensitivity analysis and bias documentation |

## Validation

To verify the entire pipeline against the specification:

```bash
# Run contract tests
pytest tests/contract/ -v

# Run integration tests (requires data/processed/merged_monthly.csv)
pytest tests/integration/ -v

# Validate output language compliance
python code/10_sensitivity_report.py --validate
```

## Troubleshooting

- **Citation Verification Failed**: If `00_verify_citations.py` exits with an error, check your internet connection and ensure the URLs in `specs/001-exploring-the-relationship-between-atmos/citations.yaml` are accessible.
- **Missing Data Files**: If the pipeline fails at Step 2, ensure Step 1 completed successfully and the `data/raw/` directories contain the expected files.
- **Memory Errors**: The GRACE-FO data processing is memory intensive. If you encounter `MemoryError`, ensure you have at least 7 GB of RAM available and close other applications.