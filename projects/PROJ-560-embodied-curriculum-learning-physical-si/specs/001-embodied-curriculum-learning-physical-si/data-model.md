# Data Model: Embodied Curriculum Learning

## Overview

This document defines the data structures used for the Embodied Curriculum Learning feature. All data is processed in memory or written to CSV/Parquet/JSON. No database is used.

## Core Entities

### 1. DatasetRecord

Represents a single participant's data point. Used for both public dataset rows and synthetic generation.

**Fields**:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `pre_test_score` | float | Yes | Score before instruction. |
| `post_test_score` | float | Yes | Score after instruction. |
| `instruction_type` | string | Yes | Values: `"embodied"` or `"static"`. |
| `concept_id` | string | No | Identifier for the mathematical concept (e.g., "fractions"). |
| `covariates` | dict | No | Optional dictionary of additional variables (e.g., `{"age": 25, "anxiety": 3.2}`). |

**Validation Rules**:
- `pre_test_score` and `post_test_score` must be numeric.
- `instruction_type` must be one of `["embodied", "static"]`.
- Missing `pre_test_score` or `post_test_score` results in row exclusion for gain calculation.

### 2. AnalysisResult

Represents the outcome of a statistical test (ANCOVA and t-test) between two conditions.

**Fields**:
| Field | Type | Description |
| :--- | :--- | :--- |
| `ancova_f_statistic` | float | The F-value from the ANCOVA model. |
| `ancova_p_value` | float | The uncorrected p-value from ANCOVA. |
| `ancova_effect_size` | float | Partial eta-squared from ANCOVA. |
| `t_statistic` | float | The t-value from the secondary t-test on gain scores. |
| `p_value` | float | The uncorrected p-value from the t-test. |
| `corrected_p_value` | float | Bonferroni-corrected p-value (if applicable). |
| `effect_size_cohen_d` | float | Cohen's d effect size from the t-test. |
| `confidence_interval` | list[float] | 95% CI for the mean difference [lower, upper]. |
| `inference_framing` | string | Always `"associational"` for this project. |
| `test_type` | string | `"ancova"` (primary) or `"student"`/`"welch"` (secondary). |
| `degrees_of_freedom` | float | Degrees of freedom (adjusted for Welch's or ANCOVA). |
| `power_achieved` | float | Calculated power for the observed effect. |
| `power_flag` | string | `"underpowered"` if power < 0.80, else `"adequate"`. |
| `collinearity_warnings` | list[str] | List of variable pairs with $|r| > 0.8$. |
| `concept_id` | string | The concept being analyzed (if multiple concepts exist). |

### 3. SensitivitySweep

Represents the output of the threshold sensitivity analysis.

**Fields**:
| Field | Type | Description |
| :--- | :--- | :--- |
| `threshold_value` | float | The gain score threshold used (e.g., 0.05). |
| `n_participants_retained` | int | Count of participants meeting the threshold. |
| `effect_size_cohen_d` | float | Effect size at this threshold. |
| `robustness_flag` | bool | `true` if effect size drops below 0.2 at this threshold. |

## Data Flow

1.  **Input**: Raw CSV/Parquet (Public) or Config (Synthetic).
2.  **Processing**:
    - Filter rows with missing `pre` or `post`.
    - Calculate `gain = post - pre`.
    - Apply threshold filter (if `--sweep` enabled).
3.  **Analysis**:
    - Group by `instruction_type`.
    - Run ANCOVA (primary) and t-test (secondary).
    - Calculate power and collinearity.
4.  **Output**: JSON report containing `AnalysisResult` and `SensitivitySweep` arrays.

## File Formats

- **Input**: CSV or Parquet.
- **Output**: JSON (strictly adhering to the schemas defined in `contracts/`).
- **Logs**: `skipped_records.log` (text) for excluded rows.