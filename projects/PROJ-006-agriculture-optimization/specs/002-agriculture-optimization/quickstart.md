# Quickstart: Correlational Analysis of Climate‑Smart Agricultural Practices and Yield Stability Independent of Financial Access

## 1. Prerequisites

- **Python**: 3.11+
- **Dependencies**: `requirements.txt` (pinned versions)
- **Data**: 
    - LSMS-ISA dataset (Malawi or Tanzania) for the relevant year.
    - Sentinel-2 or Landsat 8/9 surface reflectance data for the corresponding growing season.
    - *Note*: If data is not available for automatic download, use the `--use-synthetic` flag to generate mock data for pipeline validation.

## 2. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Setup

### Option A: Automatic Download (if URLs are available)
Run the ingestion script:
```bash
python src/cli/run_pipeline.py --stage ingest
```
*Note: This step may fail if the required datasets (LSMS-ISA, Sentinel-2) are not accessible via public, unauthenticated URLs. Check logs for `MISSING_DATA` errors.*

### Option B: Synthetic Data (for CI/Validation)
If real data is unavailable, generate a statistically realistic mock dataset:
```bash
python src/cli/run_pipeline.py --stage ingest --use-synthetic
```
*This creates `data/raw/synthetic_survey.csv` and `data/raw/synthetic_satellite.nc`.*

### Option C: Manual Data Placement
1. Download LSMS-ISA data and place it in `data/raw/survey_data.csv`.
2. Download Sentinel-2/Landsat data and place it in `data/raw/satellite_data.nc`.
3. Ensure checksums are recorded in `state/projects/PROJ-006-agriculture-optimization.yaml`.

## 4. Running the Analysis

### Full Pipeline
Execute the entire pipeline (Ingest -> Process -> Analyze -> Report):
```bash
python src/cli/run_pipeline.py --stage full
```

### Individual Stages
- **Ingest**: `python src/cli/run_pipeline.py --stage ingest`
- **Process**: `python src/cli/run_pipeline.py --stage process`
- **Analyze**: `python src/cli/run_pipeline.py --stage analyze`
- **Report**: `python src/cli/run_pipeline.py --stage report`

## 5. Validation

### Schema Validation
Validate the processed dataset against the contract:
```bash
python src/cli/validate.py --input data/processed/analysis_dataset.csv --contract contracts/dataset.schema.yaml
```

### Unit Tests
Run unit tests for data processing and modeling:
```bash
pytest tests/unit/
```

### Contract Tests
Run contract validation tests:
```bash
pytest tests/contract/
```

## 6. Output

- **Analysis Dataset**: `data/processed/analysis_dataset.csv`
- **Regression Results**: `data/processed/regression_results.json`
- **Sensitivity Analysis**: `data/processed/sensitivity_analysis.csv` and `data/processed/sensitivity_plot.png`
- **Final Report**: `reports/final_report.pdf`

## 7. Troubleshooting

- **Error: `MISSING_DATA`**: The required datasets (LSMS-ISA or Sentinel-2) could not be downloaded. Use `--use-synthetic` for validation or place files manually in `data/raw/`.
- **Error: `SPATIAL_OVERLAP_LOW`**: Fewer than 300 households matched. The pipeline will automatically aggregate to village level. If N < 100, it will switch to bivariate correlation.
- **Error: `VIF_HIGH`**: High collinearity detected. The report will include a warning; interpret coefficients with caution.
- **Error: `POWER_LOW`**: Sample size too small for multiple regression. The pipeline will switch to bivariate analysis and flag the limitation.