# API Documentation

## `code/config.py`

Manages project configuration, environment variables, and random seeds.

### Functions

- `load_config(path: str = "config.yaml") -> Dict`: Loads configuration from a YAML file.
- `set_seed(seed: int) -> None`: Sets the random seed for reproducibility.
- `verify_and_apply_seed() -> None`: Verifies seed existence and applies it, logging status.
- `get_dataset_url() -> str`: Returns the configured dataset download URL.
- `ensure_directories() -> None`: Creates required directories (`data/raw`, `data/processed`, `outputs`).

### Exceptions

- `ConfigError`: Raised when configuration is invalid or missing.

---

## `code/exceptions.py`

Custom exceptions for the research pipeline.

- `PowerLimitationError`: Raised when sample size is insufficient for statistical power.
- `MathematicalCouplingError`: Raised when variables are mathematically coupled (e.g., same variable used in predictor and outcome).
- `DataValidationError`: Raised when data fails schema or validity checks.
- `ConfigurationError`: Raised for configuration-related errors.

---

## `code/ingest.py`

Handles data download and schema validation.

### Functions

- `download_data(url: str, output_path: Path) -> Path`: Downloads dataset from URL.
- `validate_schema(df: pd.DataFrame, required_cols: List[str]) -> bool`: Checks for required columns.
- `clean_data(df: pd.DataFrame) -> pd.DataFrame`: Performs initial cleaning.
- `main()`: Entry point for ingestion script.

---

## `code/clean.py`

Data cleaning and power checks.

### Functions

- `load_cleaned_data(path: Path) -> pd.DataFrame`: Loads data from CSV.
- `validate_cleaned_data(df: pd.DataFrame) -> bool`: Validates cleaned data integrity.
- `save_cleaned_data(df: pd.DataFrame, path: Path) -> None`: Saves cleaned data.
- `main()`: Entry point for cleaning script. Implements listwise deletion and power checks (halts if N < 30).

---

## `code/model.py`

Statistical modeling and analysis.

### Functions

- `calculate_correlation(df: pd.DataFrame, x: str, y: str) -> Dict`: Calculates Pearson/Spearman correlation.
- `fit_regression_model(df: pd.DataFrame) -> sm.OLSResults`: Fits OLS regression.
- `check_assumptions(results: sm.OLSResults) -> Dict`: Checks linearity, homoscedasticity, normality, VIF.
- `run_full_analysis(df: pd.DataFrame) -> Dict`: Runs correlation and regression.
- `main()`: Entry point for modeling script.

---

## `code/validity.py`

Construct validity checks.

### Functions

- `check_construct_validity(df: pd.DataFrame, var1: str, var2: str) -> bool`: Ensures variables are distinct. Raises `MathematicalCouplingError` if identical.

---

## `code/robustness.py`

Robustness checks.

### Functions

- `calculate_engagement_correlation(df: pd.DataFrame) -> float`: Correlation between engagement and news exposure.
- `select_high_engagement_subset(df: pd.DataFrame, threshold: float) -> pd.DataFrame`: Selects top 25% engagement.
- `run_robustness_check(df: pd.DataFrame) -> Dict`: Compares full model vs. subset model.
- `main()`: Entry point for robustness script.

---

## `code/viz.py`

Visualization generation.

### Functions

- `load_processed_data(path: Path) -> pd.DataFrame`: Loads processed data.
- `plot_scatter_with_regression(df: pd.DataFrame, x: str, y: str, output_path: Path) -> None`: Generates scatter plot with regression line and 95% CI.
- `main()`: Entry point for visualization script.

---

## `code/report_generator.py`

Report generation.

### Functions

- `generate_final_report(results: Dict, output_path: Path) -> None`: Generates markdown report.
- `main()`: Entry point for report generation.
