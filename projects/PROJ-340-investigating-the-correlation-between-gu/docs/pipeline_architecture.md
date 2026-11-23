# Pipeline Architecture

## Component Overview

### 1. Ingestion (`code/ingest.py`)
- **Responsibility**: Data loading, schema validation, outlier detection.
- **Key Functions**:
 - `fetch_real_data()`: Retrieves data from configured source.
 - `validate_variables()`: Checks for required predictors/outcomes.
 - `detect_outliers_iqr()`: Identifies statistical outliers.
 - `filter_outliers()`: Removes outliers and saves filtered data.

### 2. Analysis (`code/analysis.py`)
- **Responsibility**: Statistical correlation analysis.
- **Key Functions**:
 - `check_distribution()`: Determines data normality.
 - `select_correlation_method()`: Chooses ZINB, Spearman, or Pearson.
 - `run_correlation_analysis()`: Executes the selected method.
 - `benjamini_hochberg_fdr()`: Corrects p-values.

### 3. Diagnostics (`code/diagnostics.py`)
- **Responsibility**: Quality control and robustness checks.
- **Key Functions**:
 - `detect_perfect_multicollinearity()`: Checks for linear dependencies.
 - `calculate_vif()`: Variance Inflation Factor calculation.
 - `run_sensitivity_analysis()`: Tests stability across thresholds.
 - `calculate_power()`: Statistical power estimation.

### 4. Reporting (`code/report.py`)
- **Responsibility**: Report generation and language validation.
- **Key Functions**:
 - `generate_report()`: Constructs markdown report.
 - `scan_causal_language()`: Checks for prohibited causal terms.

### 5. Orchestration (`code/main.py`)
- **Responsibility**: Workflow coordination.
- **Flow**:
 1. Setup paths and config.
 2. Run Ingestion.
 3. Run Analysis.
 4. Run Diagnostics.
 5. Generate Report.
 6. Verify Integrity.

## Data Flow

```
[Raw Data] -> [Ingest] -> [Filtered Data] -> [Analysis] -> [Correlation Results]
 -> [Diagnostics] -> [Stability Metrics]
 -> [Report]
```

## Configuration Files

- `data/config/required_variables.yaml`: Defines schema.
- `data/config/real_data_sources.yaml`: Defines data sources.
- `data/config/method_selection_log.json`: Logs method choices.
- `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml`: Checksum state.
