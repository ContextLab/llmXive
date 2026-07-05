# Data Model: Assessing the Validity of Statistical Power

## 1. Entity Overview

The data model consists of three primary entities: `StudyRecord`, `PredictorVariable`, and `RegressionResult`. Data flows from raw OSF API responses to a normalized CSV for analysis.

## 2. Entity Definitions

### 2.1 StudyRecord
Represents a single pre-registered study. This is the core unit of analysis.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `osf_id` | string | Unique OSF identifier. | OSF API |
| `field` | string | Broad category (e.g., "Social", "Natural"). | Extracted from metadata |
| `planned_power` | float | Target power (e.g., 0.80). | Extracted (FR-001) |
| `target_n` | integer | Planned sample size. | Extracted (FR-001) |
| `effect_size_assumption` | float | Assumed effect size (e.g., Cohen's d). | Extracted (FR-001) |
| `test_type` | string | Statistical test used (e.g., "t-test", "ANOVA"). | Extracted (FR-001) |
| `actual_sample_size` | integer | Actual N used in analysis. | Extracted (FR-002) |
| `observed_effect_size` | float | Observed effect size (point estimate). | Extracted (FR-002) |
| `sensitivity_power` | float | Power calculated using `actual_n` and `assumed_effect_size`. | Calculated (FR-003) |
| `power_gap` | float | `planned_power` - `sensitivity_power`. | Calculated (FR-004) |
| `missing_planned_data` | boolean | Flag if planned variables were missing. | Extraction Logic |
| `assumption_mismatch` | boolean | Flag if extracted assumptions differ from those implied by reported power. | Extraction Logic |
| `source_citation` | string | `page_number:paragraph_id` or `json_path`. | Extraction Logic |

### 2.2 PredictorVariable
Derived categorical/ordinal variables for regression.

| Field | Type | Description |
| :--- | :--- | :--- |
| `field_category` | string | Normalized field (Social, Natural, etc.). |
| `effect_size_domain` | string | Domain of effect size (e.g., "Cohen's d", "Pearson's r"). |
| **Note**: `sample_size_category` is **excluded** to prevent mathematical coupling with `power_gap`. |

### 2.3 RegressionResult
Output of the statistical model.

| Field | Type | Description |
| :--- | :--- | :--- |
| `coefficient` | float | Beta weight for the predictor. |
| `standard_error` | float | Standard error of the coefficient. |
| `p_value` | float | Significance value. |
| `vif_score` | float | Variance Inflation Factor. |
| `r_squared` | float | Model fit metric. |

## 3. Data Flow

1.  **Raw Ingestion**: `data/raw/osf_studies.json` (List of raw API responses).
2.  **Extraction**: `code/extraction.py` parses raw JSON -> `data/derived/study_records.csv`.
3.  **Calculation**: `code/power_calc.py` reads CSV -> adds `sensitivity_power`, `power_gap` -> `data/derived/power_analysis.csv`.
4.  **Modeling**: `code/regression.py` reads `power_analysis.csv` -> generates `data/derived/regression_results.json`.

## 4. Constraints & Validation

- **Power Gap**: Must be in range [-1.0, 1.0].
- **Sample Size**: Must be > 0.
- **Effect Size**: Must be numeric.
- **Missing Data**: Rows with `missing_planned_data=True` are excluded from regression but included in audit logs.
- **Coupling Check**: Ensure `sample_size_category` is not used as a predictor for `power_gap`.

