# Data Model: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Overview

This document defines the data structures for the meta-analysis pipeline. The system processes a list of `StudyRecord` objects, performs statistical aggregation, and outputs a `MetaAnalysisResult`.

## Core Entities

### StudyRecord

Represents a single extracted entry from the literature.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `author` | string | First author's last name. | Required. |
| `year` | integer | Publication year. | Required. |
| `tract_name` | string | Name of the white matter tract (e.g., "Arcuate Fasciculus"). | Required. |
| `harmonized_tract_id` | string | Standardized ID from JHU Atlas (e.g., "AF_L"). | Required for aggregation. Mapped from `tract_name`. |
| `metric` | string | dMRI metric used (e.g., "FA", "MD"). | Required. |
| `r` | float | Correlation coefficient. | Nullable. If null, `t_value` or `p_value` may be present. |
| `n` | integer | Sample size. | Required if `r` is present. |
| `t_value` | float | t-statistic. | Nullable. |
| `p_value` | float | p-value. | Nullable. |
| `direction` | string | "positive", "negative", or "mixed". | Optional. |
| `notes` | string | Any extraction notes or caveats. | Optional. |

**Unique Study Definition**: A study is uniquely identified by the tuple `(author, year)`. Multiple tracts from the same paper count as one study for the $N < 10$ threshold check, but as distinct comparisons for Bonferroni correction if $N \ge 10$ (subject to non-independence handling).

### MetaAnalysisResult

The aggregated output of the pipeline.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `synthesis_mode` | string | "quantitative" or "narrative". | Determined by study count. |
| `weighted_mean_r` | float | Pooled correlation coefficient (back-transformed). | Only if `synthesis_mode` == "quantitative". |
| `ci_95_lower` | float | Lower bound of 95% CI. | Only if `synthesis_mode` == "quantitative". |
| `ci_95_upper` | float | Upper bound of 95% CI. | Only if `synthesis_mode` == "quantitative". |
| `i_squared` | float | Heterogeneity statistic ($I^2$). | Only if `synthesis_mode` == "quantitative". |
| `egger_intercept` | float | Intercept from Egger's regression. | Only if $N \ge 10$. |
| `egger_p_value` | float | P-value from Egger's regression. | Only if $N \ge 10$. |
| `bonferroni_threshold` | float | Adjusted alpha threshold. | Only if $N \ge 10$ and $k \ge 2$. |
| `study_count` | integer | Number of unique (Author, Year) pairs. | Required. |
| `tract_count` | integer | Number of distinct tracts. | Required. |
| `narrative_summary` | string | Text summary of findings. | Only if `synthesis_mode` == "narrative". |
| `power_warning` | string | "Low Power" if N < 20 for small effects. | Nullable. |
| `warnings` | list[string] | List of warnings (e.g., "Convergence failed", "Egger's test skipped"). | Required. |

## Data Flow

1.  **Input**: `data/raw/studies_extracted.csv` (or JSON).
2.  **Processing**:
    *   Parse and validate `StudyRecord` fields.
    *   **Tract Harmonization**: Map `tract_name` to `harmonized_tract_id` using a standard ontology. Flag non-standard entries.
    *   Check `unique_study_count`.
    *   If `< 10`: Trigger `NarrativeSynthesis` module.
    *   If `>= 10`: Trigger `MetaAnalysis` module (Random-Effects, I², Egger's).
    *   **Non-Independence Check**: If multiple tracts from the same study are present, apply Robust Variance Estimation (RVE) or group as a single unit.
    *   Apply `BonferroniCorrection` if applicable.
    *   **Power Analysis**: Check if N < 20 and expected effect size is small. Add `power_warning` if so.
3.  **Output**: `data/derived/meta_analysis_result.json` and PNG plots.

## Constraints & Validation

- **Missing Data**: If `r` is missing, the system attempts to derive it from `t_value` or `p_value` using standard formulas. If derivation fails, the study is excluded and logged.
- **Collinearity**: If a study reports multiple tracts that are definitionally related (e.g., "Left Arcuate" and "Right Arcuate" treated as one tract type), they are counted as distinct comparisons for correction logic but the narrative summary must acknowledge the potential lack of independence.
- **Precision**: All floating-point results are rounded to 4 decimal places for storage, 2 decimal places for display in plots.
- **Non-Independence**: The pipeline will log a warning if multiple tracts from the same study are included without explicit RVE logic, as this may inflate Type I error rates.