# Data Model: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

## 1. Overview
This document defines the data structures used in the research pipeline, from raw session logs to processed statistical summaries. The model enforces strict types and constraints to ensure data integrity (Constitution Principle III).

## 2. Raw Data Structure (Session Log)
Data is collected as JSON objects per session, then aggregated.

**Fields**:
- `session_id`: UUID string.
- `participant_id`: Anonymized string (e.g., "P001").
- `timestamp`: ISO 8601 string.
- `interface_variant`: "traditional" | "explainable".
- `order`: "T->X" | "X->T".
- `task_results`: Object containing `completion_time` (float), `error_count` (int), `explanation_engagement_time` (float).
- `sus_responses`: Array of 10 integers (1-5).
- `status`: "complete" | "incomplete".

## 3. Processed Data Structure (Cleaned Sessions)
After validation and imputation (FR-005), data is stored in `data/processed/cleaned_sessions.csv`.

**Schema**:
| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `session_id` | string | Unique ID | Not Null, Unique |
| `participant_id` | string | Anonymized ID | Not Null |
| `interface_variant` | string | Condition | "traditional" or "explainable" |
| `order` | string | Counterbalancing | "T->X" or "X->T" |
| `completion_time` | float | Seconds | > 0 |
| `error_count` | integer | Errors | >= 0 |
| `sus_score` | float | 0-100 | Calculated from responses |
| `status` | string | Session status | Only "complete" included |

**Transformation Logic**:
1. **Filter**: Exclude rows where `status` != 'complete'.
2. **Impute SUS**: If `sus_responses` has exactly one missing value, replace with participant mean. If >1 missing, mark session as 'incomplete' (and thus excluded).
3. **Calculate SUS**: Standard formula: $( \sum (odd\_items - 1) + \sum (5 - even\_items) ) \times 2.5$.

## 4. Aggregated Data Structure (Metrics Summary)
Stored in `data/processed/metrics_summary.csv`.

**Schema**:
| Column | Type | Description |
| :--- | :--- | :--- |
| `metric` | string | "completion_time", "error_count", "sus_score" |
| `interface_variant` | string | "traditional" | "explainable" |
| `mean` | float | Mean value |
| `std` | float | Standard deviation |
| `n` | integer | Sample size |
| `median` | float | Median |

## 5. Statistical Output Structure
Stored in `data/processed/analysis_results.json`.

**Schema**:
- `anova_results`: Object with `metric`, `F_statistic`, `p_value`, `df_num`, `df_denom`.
- `corrected_p_values`: Object with `metric`, `raw_p`, `holm_corrected_p`, `significant` (bool).
- `power_analysis`: Object with `metric`, `effect_size`, `power`, `n_observed`.

## 6. Data Lineage
1. `data/raw/sessions_*.json` -> (Validation/Imputation) -> `data/processed/cleaned_sessions.csv`
2. `cleaned_sessions.csv` -> (Aggregation) -> `metrics_summary.csv`
3. `cleaned_sessions.csv` -> (ANOVA) -> `analysis_results.json`
4. `analysis_results.json` -> (Reporting) -> `data/processed/power_report.md`
