# API Documentation: `code/analyze.py`

This module implements the statistical analysis pipeline for the study on linguistic complexity and trust in AI-generated text. It performs data loading, merging, regression analysis, power analysis, and result visualization.

## Functions

### `load_cleaned_responses() -> pd.DataFrame`

Loads the cleaned participant trust responses from the processed data directory.

**Returns:**
- `pd.DataFrame`: A DataFrame containing columns `participant_id`, `text_sample_id`, `trust_rating`, and `attention_check_status`.

**File Path:**
- `data/processed/cleaned_responses.csv`

---

### `load_generated_text_samples() -> pd.DataFrame`

Loads the generated AI text samples with computed complexity metrics.

**Returns:**
- `pd.DataFrame`: A DataFrame containing columns `text_id`, `raw_text`, `source_id`, `flesch_kincaid`, `mtld`, and `avg_sentence_length`.

**File Path:**
- `data/raw/generated_text.csv`

---

### `merge_datasets(cleaned_responses: pd.DataFrame, text_samples: pd.DataFrame) -> pd.DataFrame`

Merges the cleaned responses with the text samples on the `text_sample_id` (or `text_id`) column.

**Parameters:**
- `cleaned_responses` (pd.DataFrame): The cleaned trust responses.
- `text_samples` (pd.DataFrame): The generated text samples with metrics.

**Returns:**
- `pd.DataFrame`: A merged DataFrame containing both trust ratings and complexity metrics.

---

### `save_analysis_inputs(merged_df: pd.DataFrame, output_path: str) -> None`

Saves the merged dataset to a CSV file for downstream analysis or inspection.

**Parameters:**
- `merged_df` (pd.DataFrame): The merged DataFrame.
- `output_path` (str): The path to save the CSV file.

**Default Output Path:**
- `data/processed/analysis_inputs.csv`

---

### `run_univariate_regression(data: pd.DataFrame, metric: str) -> statsmodels.regression.linear_model.RegressionResults`

Runs a separate univariate linear regression for a specific complexity metric, including a quadratic term.

**Parameters:**
- `data` (pd.DataFrame): The merged dataset.
- `metric` (str): The name of the metric column to use (e.g., `"flesch_kincaid"`, `"mtld"`, `"avg_sentence_length"`).

**Returns:**
- `statsmodels.regression.linear_model.RegressionResults`: The regression results object.

**Model Specification:**
- Dependent Variable: `trust_rating`
- Independent Variables: `metric`, `metric**2` (quadratic term)

---

### `apply_bonferroni_correction(p_values: list, alpha: float = 0.05) -> list`

Applies Bonferroni correction to a list of p-values.

**Parameters:**
- `p_values` (list): A list of raw p-values.
- `alpha` (float): The significance level. Defaults to 0.05.

**Returns:**
- `list`: A list of adjusted p-values (or a boolean list indicating significance, depending on implementation details).

**Note:**
- Adjusted alpha = `alpha / k`, where `k` is the number of tests.

---

### `run_power_analysis(data: pd.DataFrame, metric: str, alpha: float = 0.05) -> dict`

Performs a post-hoc power analysis for the quadratic term of a specific metric.

**Parameters:**
- `data` (pd.DataFrame): The merged dataset.
- `metric` (str): The name of the metric column.
- `alpha` (float): The significance level.

**Returns:**
- `dict`: A dictionary containing:
 - `f_squared`: The calculated effect size (f²).
 - `power`: The calculated statistical power.
 - `min_detectable_f2`: The minimum detectable effect size for power ≥ 0.80.
 - `status`: "PASS" or "FAIL" based on SC-006 criteria.

---

### `run_ordinal_regression(data: pd.DataFrame, metric: str) -> statsmodels.miscmodels.ordinal_model.OrderedModel`

Runs an ordinal logistic regression as a sensitivity check for the linear model.

**Parameters:**
- `data` (pd.DataFrame): The merged dataset.
- `metric` (str): The name of the metric column.

**Returns:**
- `statsmodels.miscmodels.ordinal_model.OrderedModel`: The fitted ordinal regression model.

**Purpose:**
- Validates the interval-scale assumption of Likert data by comparing qualitative conclusions with the linear model.

---

### `generate_visualizations(data: pd.DataFrame, output_dir: str) -> None`

Generates visualizations (Trust vs. Complexity fitted curves with confidence intervals) using `seaborn`.

**Parameters:**
- `data` (pd.DataFrame): The merged dataset.
- `output_dir` (str): The directory to save the figure files.

**Default Output Path:**
- `data/outputs/figures/`

**Outputs:**
- One plot per metric (FK, MTLD, Sentence Length).

---

### `save_results(results_dict: dict, output_path: str) -> None`

Saves the final regression results to a JSON file.

**Parameters:**
- `results_dict` (dict): A dictionary containing regression coefficients, p-values, R-squared, Bonferroni adjusted p-values, and power analysis results.
- `output_path` (str): The path to save the JSON file.

**Default Output Path:**
- `data/outputs/regression_results.json`

---

### `main() -> None`

The entry point for the analysis pipeline.

**Workflow:**
1. Load cleaned responses and text samples.
2. Merge datasets.
3. Run univariate regressions for each metric.
4. Apply Bonferroni correction.
5. Run power analysis.
6. Run ordinal regression for sensitivity check.
7. Generate visualizations.
8. Save results to JSON.
9. Log verification checks (convergence, significance, sensitivity).

## Dependencies

- `os`, `sys`, `json`, `csv`, `logging`, `math` (standard library)
- `pandas`
- `numpy`
- `statsmodels`
- `seaborn`
- `scipy`