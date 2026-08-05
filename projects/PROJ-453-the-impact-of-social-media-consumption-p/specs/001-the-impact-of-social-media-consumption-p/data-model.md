# Data Model: The Impact of Social Media Consumption Patterns on Cognitive Flexibility

## Entity-Relationship Overview

The data model consists of a single primary table (`participants`) derived from the raw dataset, containing all variables required for the regression analysis.

### Participant Entity
Represents an individual survey respondent.

| Attribute | Type | Description | Source/Derivation |
|-----------|------|-------------|-------------------|
| `participant_id` | String | Unique identifier for the respondent. | Raw Dataset |
| `age` | Integer | Age in years. | Raw Dataset |
| `total_screen_time` | Float | Total daily screen time in hours. | Raw Dataset |
| `num_platforms` | Integer | Number of social media platforms used. | Raw Dataset |
| `switching_frequency` | Integer | Self-reported frequency of switching (e.g., 1-5 scale). | Raw Dataset |
| `switching_index` | Float | Derived: `num_platforms * switching_frequency`. | Computed (`02_engineer.py`) |
| `cognitive_flexibility_score` | Float | Standardized score from cognitive test (e.g., WCST). | Raw Dataset (or Proxy) |
| `exclusion_flag` | Boolean | True if `cognitive_flexibility_score` is missing. | Computed |
| `instrument_source` | String | Documentation of the survey instrument used for the cognitive measure (e.g., "WCST-64", "Trail Making B"). | Raw Dataset Metadata (Constitution Principle VI) |

### RegressionModel Entity
Represents the output of the statistical analysis.

| Attribute | Type | Description |
|-----------|------|-------------|
| `model_id` | String | Unique ID for the model run. |
| `r_squared` | Float | Coefficient of determination. |
| `coefficients` | Dict | Map of predictor name to beta coefficient. |
| `p_values` | Dict | Map of predictor name to raw p-value. |
| `p_values_corrected` | Dict | Map of predictor name to FDR-corrected p-value. |
| `vif_scores` | Dict | Map of predictor name to VIF score. |
| `interaction_significant` | Boolean | True if interaction term p-value < 0.05. |
| `collinearity_flag` | Boolean | True if any VIF > 5 or correlation > 0.7. |
| `residualized_model_used` | Boolean | True if the residualized model was used to mitigate mathematical coupling. |
| `interpretation` | String | Associational interpretation of the results. **MUST NOT contain causal language.** Validated programmatically. |

### SensitivityRun Entity
Represents a specific iteration of the sensitivity analysis.

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | String | Unique ID for the sensitivity run. |
| `predictor_definition` | String | e.g., "platform_count", "switching_frequency". |
| `beta_coefficient` | Float | Beta for the primary predictor. |
| `p_value` | Float | P-value for the primary predictor. |
| `p_value_corrected` | Float | FDR-corrected p-value. |
| `sample_size` | Integer | Number of observations used. |

## Data Flow

1.  **Raw Ingestion**: Download raw files (JSON/Parquet/CSV) to `data/raw/`.
2.  **Feasibility Check**: Verify presence of `switching_frequency` and `cognitive_flexibility_score`. **HALT** if missing.
3.  **Cleaning**: Parse, rename columns to standard schema, handle missing values.
4.  **Derivation**: Compute `switching_index` and `exclusion_flag`. Document instrument sources.
5.  **Modeling**: 
    -   Check correlation for mathematical coupling.
    -   Mean-center variables for interaction.
    -   Fit OLS (or GLM if assumptions violated).
    -   Compute diagnostics (VIF, correlation).
    -   Run sensitivity analysis with FDR correction.
    -   Validate `interpretation` string for causal language.
6.  **Output**: Write `results/models/` JSON and `results/figures/` plots.