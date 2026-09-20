# API Reference

This document describes the public API of the PROJ-540 modules.

## `code/config.py`

Manages configuration, seeds, and environment.

- `load_config()`: Loads configuration from YAML or environment.
- `set_seed(seed: int)`: Sets the random seed for reproducibility.
- `verify_and_apply_seed()`: Verifies the seed is set and applies it.
- `log_seed_status()`: Logs the current seed status.
- `get_dataset_url()`: Returns the configured dataset URL.
- `ensure_directories()`: Creates necessary directories if they don't exist.

## `code/ingest.py`

Handles data ingestion.

- `download_data(url: str, output_path: Path)`: Downloads data. Raises exception on failure.
- `validate_schema(df: pd.DataFrame)`: Validates required columns.
- `clean_data(df: pd.DataFrame)`: Performs initial cleaning.
- `main()`: Entry point for ingestion script.

## `code/clean.py`

Handles data cleaning and power checks.

- `load_cleaned_data(path: Path)`: Loads raw data.
- `validate_cleaned_data(df: pd.DataFrame)`: Checks for nulls.
- `save_cleaned_data(df: pd.DataFrame, path: Path)`: Saves cleaned data.
- `main()`: Entry point for cleaning script.

## `code/model.py`

Statistical modeling.

- `calculate_correlation(df, x, y)`: Calculates Pearson/Spearman correlation.
- `fit_regression_model(df)`: Fits the OLS model.
- `check_assumptions(df)`: Checks linearity, homoscedasticity, normality.
- `run_full_analysis(df)`: Runs the complete analysis pipeline.
- `main()`: Entry point for modeling script.

## `code/validity.py`

Construct validity.

- `check_construct_validity(df)`: Checks for mathematical coupling. Raises `MathematicalCouplingError` if invalid.

## `code/robustness.py`

Robustness checks.

- `calculate_engagement_correlation(df)`: Correlates engagement with exposure.
- `select_high_engagement_subset(df)`: Selects top 25% engagement.
- `run_robustness_check(df)`: Runs the robustness check logic.
- `main()`: Entry point for robustness script.

## `code/viz.py`

Visualization.

- `plot_scatter_with_regression(df)`: Generates the main scatter plot.
- `plot_robustness_comparison(df_full, df_subset)`: Generates robustness comparison plot.
- `main()`: Entry point for visualization script.

## `code/report_generator.py`

Report generation.

- `generate_final_report(results)`: Generates the markdown report.
- `main()`: Entry point for report generation.
