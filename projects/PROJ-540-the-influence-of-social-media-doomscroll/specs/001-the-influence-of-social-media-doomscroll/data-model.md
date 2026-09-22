# Data Model: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Entity Definitions

### SurveyResponse

Represents a single participant record after cleaning.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | string | Unique anonymized identifier. | Non-null, unique. |
| `news_exposure_freq` | float | Frequency of negative news consumption (proxy: Media Exposure). | Non-null, ≥ 0. |
| `anxiety_score` | float | Outcome anxiety score (GAD-7). | Non-null, ≥ 0. |
| `baseline_anxiety` | float | Baseline/trait anxiety score. | Nullable. (Dropped if not distinct). |
| `age` | integer | Participant age in years. | Non-null, 18 ≤ age ≤ 100. |
| `gender` | string | Categorical gender. | One of: "Male", "Female", "Other". |
| `education_level` | integer | Education level (used for robustness). | Nullable. |
| `instrument_source` | string | Name of the anxiety instrument used. | Non-null. |
| `measurement_timepoint` | string | "pre", "post", or "trait". | Non-null. |
| `proxy_flag` | boolean | True if 'general_anxiety' was used as proxy. | Non-null. |
| `coupling_risk` | boolean | True if baseline and outcome risk mathematical coupling. | Non-null. |

### RegressionResult

Represents the output of the statistical model.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "OLS" |
| `n_samples` | integer | Number of observations used. |
| `r_squared` | float | Coefficient of determination. |
| `adj_r_squared` | float | Adjusted R-squared. |
| `f_statistic` | float | F-statistic for the model. |
| `f_pvalue` | float | P-value for the F-statistic. |
| `coefficients` | object | Map of variable names to coefficient values. |
| `std_errors` | object | Map of variable names to standard errors. |
| `p_values` | object | Map of variable names to p-values. |
| `vif_scores` | object | Map of variable names to VIF scores. |
| `assumption_checks` | object | Results of linearity, homoscedasticity, normality tests. |
| `robustness_result` | object | Optional results from the Education Level subset analysis. |
| `flags` | array | List of warnings (e.g., "Low Power", "Proxy Used", "High VIF", "No Baseline Control"). |
| `runtime` | number | Execution time in seconds (for SC-005). |

## Data Flow

1.  **Raw Data**: Downloaded from NHANES (Parquet/CSV).
2.  **Cleaned Data**: `SurveyResponse` records after listwise deletion.
3.  **Model Output**: `RegressionResult` JSON/CSV.
4.  **Visualization**: PNG/SVG files generated from `RegressionResult` and `Cleaned Data`.

## Assumptions & Constraints

- **Missing Data**: No imputation. Rows with nulls in key predictors are dropped.
- **Outliers**: No automatic outlier removal; outliers are analyzed via residual plots.
- **Categorical Encoding**: `gender` is one-hot encoded during model fitting.
- **Scale**: All continuous variables are assumed to be on a comparable scale or standardized if required by the model (OLS does not strictly require standardization for interpretation, but it helps with VIF).
- **Proxy**: If `anxiety_score` is derived from GAD-7, `proxy_flag` is set to True.
- **Baseline**: If `baseline_anxiety` is not distinct, it is dropped and `coupling_risk` is True.
