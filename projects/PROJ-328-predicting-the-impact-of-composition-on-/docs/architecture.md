# System Architecture

## Pipeline Overview

The research pipeline is designed as a modular, sequential workflow where each stage produces immutable artifacts consumed by the next.

### 1. Ingestion Phase
- **Sources**: Reads `data/config/sources.yaml` to fetch data from APIs and scrape PDFs.
- **Raw Storage**: Writes immutable raw files to `data/raw/` with SHA256 checksums.
- **Cleaning**: Validates composition sums, temperature, and element counts. Outputs `solder_hardness_cleaned.csv`.
- **Validation**: Generates `.ingestion_status.json` and `validation_metrics.yaml`.

### 2. Feature Engineering Phase
- **CLR Transform**: Applies centered log-ratio transform to compositional data (`clr_features.csv`).
- **Descriptor Engine**: Calculates physical properties (atomic mass, electronegativity, etc.) using `mendeleev` (`descriptors.csv`).
- **Collinearity**: Computes VIF scores and generates `vif_report.yaml`.

### 3. Modeling Phase
- **Training**: Trains XGBoost and Linear Regression models using CPU-only configurations.
- **Cross-Validation**: Performs k-fold CV and paired t-tests.
- **Bootstrap**: Calculates confidence intervals for R² and RMSE on the test set.
- **SHAP**: Generates feature importance rankings.

### 4. Evaluation & Visualization Phase
- **Sensitivity Analysis**: Sweeps R² thresholds and plots the fraction of samples exceeding each.
- **Plots**: Generates scatter plots and partial dependence plots.
- **Reporting**: Aggregates all metrics into `final_aggregated_report.yaml` and updates the paper draft.

## Data Flow Diagram

```
[Sources.yaml] -> [API Fetcher / Literature Scraper] -> [data/raw/]
 |
 v
[Cleaner] -> [data/processed/solder_hardness_cleaned.csv]
 |
 +-> [Validator] -> [.ingestion_status.json]
 |
 v
[Feature Engineering] -> [clr_features.csv] + [descriptors.csv]
 |
 v
[Model Training] -> [model_artifacts/] + [cv_scores.yaml]
 |
 v
[Evaluation] -> [test_metrics.yaml] + [sensitivity_analysis.yaml]
 |
 v
[Visualization] -> [data/outputs/*.png]
 |
 v
[Report Aggregation] -> [final_aggregated_report.yaml]
```

## Error Handling

- **Data Fetch Failures**: Raises `DataFetchError` and skips the source (no synthetic fallback).
- **Validation Failures**: Excludes invalid records and logs to `excluded_records.csv`.
- **Compute Limits**: `verify_runtime.py` ensures pipeline stays within resource budgets.

## Reproducibility

- **Seeding**: `code/seed.py` sets random seeds for Python, NumPy, and ML libraries.
- **CPU-Only**: All models configured to run on CPU to ensure portability.
- **Logging**: JSON-formatted logs written to `logs/pipeline.log`.
