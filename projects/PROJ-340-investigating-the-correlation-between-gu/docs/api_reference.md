# API Reference

## Core Modules

### `code/ingest.py`
- `fetch_real_data()`: Fetches data from configured source.
- `validate_variables()`: Validates data against schema.
- `detect_outliers_iqr()`: Detects outliers using IQR method.
- `filter_outliers()`: Filters outliers and saves data.
- `save_outlier_report()`: Saves outlier report to JSON.

### `code/analysis.py`
- `check_distribution()`: Checks data normality.
- `select_correlation_method()`: Selects analysis method.
- `run_correlation_analysis()`: Runs correlation analysis.
- `benjamini_hochberg_fdr()`: Applies FDR correction.
- `save_method_selection_log()`: Logs method selection.

### `code/diagnostics.py`
- `detect_perfect_multicollinearity()`: Checks for multicollinearity.
- `calculate_vif()`: Calculates VIF.
- `run_sensitivity_analysis()`: Runs sensitivity analysis.
- `calculate_power()`: Calculates statistical power.

### `code/report.py`
- `generate_report()`: Generates markdown report.
- `scan_causal_language()`: Scans for causal language.

### `code/main.py`
- `run_ingestion_and_validation()`: Runs ingestion pipeline.
- `run_analysis()`: Runs analysis pipeline.
- `run_diagnostics()`: Runs diagnostics pipeline.

## Configuration Files

- `data/config/required_variables.yaml`: Schema definition.
- `data/config/real_data_sources.yaml`: Data source configuration.
- `data/config/method_selection_log.json`: Method selection log.

## Output Files

- `data/processed/filtered_data.parquet`: Cleaned data.
- `data/results/outlier_report.json`: Outlier details.
- `data/results/correlation_matrix.json`: Correlation results.
- `data/results/sensitivity_analysis.csv`: Sensitivity results.
- `data/results/power_analysis_report.json`: Power analysis.
- `data/results/report_draft.md`: Final report.
- `data/results/timing_evidence.json`: Timing metrics.
