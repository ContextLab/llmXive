# Data Model: Developing Novel Solutions to Address Energy Inequity in Low-Income Communities

## 1. Entity Relationship Overview

The data model centers on the `Household` entity, which is transformed into a `MatchedPair` during the PSM phase, and finally aggregated into an `AnalysisResult`. A separate `ScalingResult` entity is defined for the descriptive scaling analysis.

### Key Entities

1.  **Household**: The atomic unit of analysis. Represents a single residential unit.
2.  **MatchedPair**: A linkage created during PSM between one treated household and one (or more) control households.
3.  **AnalysisResult**: The final output containing the ATT estimate, confidence intervals, and balance metrics.
4.  **ScalingResult**: The output of the descriptive scaling law analysis (tract-level).

## 2. Data Schema Definitions

### Household (Raw & Processed)

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `household_id` | String | Unique identifier for the household. | EIA RECS |
| `income` | Float | Annual household income (USD). | EIA RECS |
| `energy_cost` | Float | Annual energy expenditure (USD). | EIA RECS |
| `log_energy_cost` | Float | Natural log of energy cost (Primary Causal Outcome). | Derived |
| `energy_cost_burden` | Float | `energy_cost / income` (Descriptive Only). | Derived |
| `housing_type` | Categorical | Type of dwelling (e.g., single-family, multi-unit). | EIA RECS |
| `location` | String | Census tract or ZIP code. | EIA RECS |
| `treatment` | Binary | 1 if clean-energy adopted, 0 otherwise. | Constructed |
| `propensity_score` | Float | Estimated probability of treatment. | Model Output |
| `home_value` | Float | Estimated home value. | EIA RECS |
| `home_value_change` | Float | Change in home value (if longitudinal data exists). | EIA RECS (Optional) |
| `weight` | Float | Survey weight (if applicable). | EIA RECS |

### MatchedPair

| Field | Type | Description |
| :--- | :--- | :--- |
| `pair_id` | String | Unique ID for the matched set. |
| `treated_id` | String | Reference to the treated household. |
| `control_id` | String | Reference to the control household. |
| `smd_income` | Float | Standardized mean difference for income. |
| `smd_housing` | Float | Standardized mean difference for housing type. |
| `smd_location` | Float | Standardized mean difference for location. |

### AnalysisResult

| Field | Type | Description |
| :--- | :--- | :--- |
| `method` | String | "PSM" or "DiD" or "Skipped_DiD_Data_Unavailable". |
| `att_estimate` | Float | Average Treatment Effect on the Treated (on `log(energy_cost)`). |
| `p_value` | Float | Statistical significance (two-tailed). |
| `ci_lower` | Float | Lower bound of 95% CI. |
| `ci_upper` | Float | Upper bound of 95% CI. |
| `caliper_used` | Float | The propensity score caliper applied. |
| `balance_status` | Boolean | True if all SMD <= 0.1. |
| `sample_size_treated` | Integer | Number of treated units in final sample. |
| `sample_size_control` | Integer | Number of control units in final sample. |

### ScalingResult (Descriptive Only)

| Field | Type | Description |
| :--- | :--- | :--- |
| `tract_id` | String | Census tract identifier. |
| `population` | Integer | Population of the tract. |
| `total_energy` | Float | Total energy consumption of the tract. |
| `scaling_exponent` | Float | Estimated scaling exponent (beta). |
| `r_squared` | Float | Goodness of fit for the scaling model. |
| `is_causal` | Boolean | **False** (Strictly descriptive). |

## 3. Transformation Logic

1.  **Ingestion**: Load raw CSV/Parquet. Validate columns against `Household` schema.
2.  **Filtering**:
    *   Filter `income < 150% * Federal_Poverty_Line`.
    *   Filter `energy_cost > 0` (handle zeros via winsorization or log-transform).
3.  **Feature Engineering**:
    *   `treatment`: `1` if `solar` or `microgrid` indicator is present.
    *   `log_energy_cost`: `log(energy_cost + 1)` (to handle zeros).
    *   `burden`: `energy_cost / income` (for reporting only).
4.  **PSM**:
    *   Fit Logistic Regression on covariates (`income`, `housing_type`, `location`).
    *   Calculate `propensity_score`.
    *   Apply common support filter (exclude scores near 0 or 1).
    *   Match 1:1 (or 1:k) using nearest neighbor with caliper.
5.  **Balance Check**:
    *   Calculate SMD for all covariates.
    *   If `max(SMD) > 0.1`, trigger fallback or adjustment.
6.  **Estimation**:
    *   Run OLS: `log_energy_cost ~ treatment + covariates` on matched sample.
    *   Cluster standard errors by `pair_id`.
    *   **Note**: `burden` is NOT used in this regression.

## 4. Data Quality Constraints

*   **Missing Data**: Rows with missing `income`, `energy_cost`, or `treatment` are dropped or imputed (median) with a flag.
*   **Outliers**: `energy_cost` and `income` are winsorized at 1st and 99th percentiles.
*   **Consistency**: `treatment` must be 0 or 1. `propensity_score` must be in (0, 1).
*   **Longitudinal Check**: If `home_value_change` or pre/post variables are missing, the system flags `did_available = False`.