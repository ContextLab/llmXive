# Quickstart: Correlational Analysis of Climate-Smart Agricultural Practices

## 1. Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with same specs).

## 2. Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd PROJ-006-agriculture-optimization
 ```

2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Dependencies include: `pandas`, `numpy`, `statsmodels`, `geopandas`, `pytest`, `pyyaml`.*

## 3. Data Setup

### 3.1 Downloading Data
The pipeline attempts to download data from verified sources.
```bash
python src/cli/run_pipeline.py --stage download
```
*Note: If LSMS-ISA or Sentinel-2 are unavailable, the script will switch to Structural Validation Mode using a generic UCI dataset or synthetic data.*

### 3.2 Verifying Data
Ensure the data files exist and pass schema validation:
```bash
python src/cli/validate.py --input data/processed/analysis_dataset.csv
```
Expected output: `Validation PASSED: 0 errors`.

## 4. Running the Analysis

Execute the full pipeline (Ingest -> Process -> Model -> Report):
```bash
python src/cli/run_pipeline.py --full
```

This will:
1. Ingest data (or generate synthetic proxy).
2. Perform spatial join and feature engineering.
3. Run regression models with robust SE.
4. Perform VIF diagnostics.
5. Run sensitivity analysis (cloud cover & model specification).
6. Generate `reports/final_report.pdf`.

## 5. Running Tests

Execute the test suite to verify implementation correctness:
```bash
pytest tests/ -v
```

**Key Tests**:
- `tests/contract/test_dataset_schema.py`: Validates data structure.
- `tests/integration/test_pipeline.py`: Verifies end-to-end flow.
- `tests/unit/test_feature_engineering.py`: Checks CSA Index and Stability Score logic.

## 6. Expected Outputs

- `data/processed/analysis_dataset.csv`: The final analysis-ready dataset.
- `data/processed/regression_results.json`: Coefficients, p-values, VIF scores.
- `reports/final_report.pdf`: The scientific report with disclaimers.
- `data/logs/ingestion_errors.log`: Any records excluded during processing.

## 7. Troubleshooting

- **Error: "NO_DATA_AVAILABLE"**: The verified datasets (LSMS-ISA) are not accessible. The pipeline has switched to Structural Validation Mode (UCI/Synthetic). Check `data/processed/analysis_dataset.csv` for `is_synthetic=True`.
- **Error: "VIF > 5"**: Collinearity detected. Check `data/logs/diagnostics.log` for flagged variables.
- **Error: "Spatial Join Failed"**: Coordinates may be missing or fuzzed too aggressively. Check `data/logs/linkage_validation.json`.
- **Error: "LOW_POWER"**: Sample size is insufficient even after aggregation. Check `data/logs/power_analysis.log`.