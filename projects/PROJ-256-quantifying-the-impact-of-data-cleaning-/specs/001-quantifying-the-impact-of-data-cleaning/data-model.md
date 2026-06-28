# Data Model: Quantifying the Impact of Data Cleaning on Statistical Inference

## Entities

### Dataset
Represents a public dataset from verified sources.
- `dataset_id` (string): Unique identifier (e.g., "uci_har_001")
- `source_url` (string): Verified URL used for download
- `sample_size` (integer): Number of rows
- `missingness_rate` (float): Proportion of missing values (0.0 to 1.0)
- `predictor_variables` (list): Names of numeric predictor columns
- `outcome_variable` (string): Name of numeric outcome column

### CleaningStrategy
Represents a cleaning intervention applied to a dataset.
- `strategy_id` (string): Unique identifier (e.g., "iqr_1.5", "mean_imp")
- `strategy_type` (string): "outlier_removal", "imputation", "recoding"
- `parameters` (object): e.g., `{"k": 1.5}` or `{"method": "mean"}`
- `rows_affected` (integer): Number of rows removed or modified

### AnalysisResult
Represents statistical output from a specific dataset/strategy combination.
- `result_id` (string): Unique identifier
- `dataset_id` (string): Foreign key to Dataset
- `strategy_id` (string): Foreign key to CleaningStrategy
- `test_type` (string): "t_test", "linear_regression"
- `p_value` (float): Rounded to ≥3 decimal places
- `ci_lower` (float): Lower bound of 95% CI
- `ci_upper` (float): Upper bound of 95% CI
- `effect_size` (float): Cohen's d or R²
- `sample_size` (integer): N used in analysis

### ComparisonReport
Represents cleaned-vs-baseline difference.
- `report_id` (string): Unique identifier
- `dataset_id` (string): Foreign key to Dataset
- `strategy_id` (string): Foreign key to CleaningStrategy
- `baseline_metrics` (object): p_value, ci_width, effect_size
- `cleaned_metrics` (object): p_value, ci_width, effect_size
- `absolute_diff` (float): |p_cleaned - p_baseline|
- `relative_diff` (float): % change in CI width
- `sensitivity_analysis` (object): Stratification bins (size, missingness)
- `bootstrap_ci` (object): 95% CI for the shift (lower, upper)
- `variance_method` (string): "bootstrap" or "jackknife"

## Relationships

- **Dataset** (1) → (N) **CleaningStrategy**: One dataset can have multiple cleaning variants.
- **CleaningStrategy** (1) → (N) **AnalysisResult**: One strategy can produce multiple test results (t-test, regression).
- **AnalysisResult** (1) → (1) **ComparisonReport**: Results are paired for comparison.

## Constraints

- `p_value` MUST be between 0 and 1.
- `missingness_rate` MUST be between 0 and 1.
- `source_url` MUST match a verified URL from the project's `# Verified datasets` block.
- All timestamps MUST be ISO 8601 format.
