# Data Model: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Overview

This document defines the data structures for the meta-analysis pipeline. It includes the input schema for study records, the output schema for meta-analysis results, and the schema for the narrative fallback.

## Entities

### StudyRecord

Represents a single literature entry.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `author` | string | First author name. | Yes |
| `year` | integer | Publication year. | Yes |
| `tract_name` | string | Name of the brain tract (e.g., "arcuate fasciculus"). | Yes |
| `metric` | string | MRI metric (e.g., "FA", "MD"). | Yes |
| `r` | float | Correlation coefficient. | Conditional |
| `n` | integer | Sample size. | Conditional |
| `t_value` | float | T-statistic (if r not available). | Conditional |
| `qualitative_desc` | string | Extracted qualitative description (if no r/n). | Yes |
| `source` | string | Source of the record (e.g., "PubMed", "Synthetic"). | Yes |

**Constraints**:
- `r` must be in [-1, 1].
- `n` must be > 0.
- If `r` and `n` are missing, `qualitative_desc` must be populated.

### MetaAnalysisResult

Represents the aggregated output.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `pooled_r` | float | Weighted mean correlation. | Conditional |
| `ci_lower` | float | 95% CI lower bound. | Conditional |
| `ci_upper` | float | 95% CI upper bound. | Conditional |
| `i_squared` | float | Heterogeneity statistic (2 decimals). | Conditional |
| `egger_intercept` | float | Egger's test intercept. | Conditional |
| `egger_p` | float | Egger's test p-value. | Conditional |
| `egger_skipped_reason` | string | Reason for skipping Egger's test (if N<10). | Conditional |
| `synthesis_mode` | string | "quantitative" or "narrative". | Yes |
| `study_count` | integer | Number of eligible studies. | Yes |
| `tract_count` | integer | Number of distinct tracts. | Yes |
| `bonferroni_adjusted_alpha` | float | Adjusted alpha if applied. | Conditional |
| `qualitative_summary` | string | Narrative summary (if synthesis_mode="narrative"). | Conditional |

**Constraints**:
- If `synthesis_mode` == "quantitative", `pooled_r`, `i_squared`, and `egger_skipped_reason` (if applicable) must be present.
- If `synthesis_mode` == "narrative", `qualitative_summary` must be present.
- `i_squared` must have at least 2 decimal places.

### VisualizationOutput

Represents generated plots.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `forest_plot_path` | string | Path to PNG file. | Yes |
| `funnel_plot_path` | string | Path to PNG file. | Yes |
| `correlation_plot_path` | string | Path to PNG file. | Yes |
| `file_size_mb` | float | Size of each PNG in MB. | Yes |

**Constraints**:
- `file_size_mb` < 5.0 for all plots.

## Data Flow

1.  **Input**: `raw/studies.csv` (or JSONL from PubMed).
2.  **Extraction**: `extraction.py` parses input -> `processed/study_records.json`.
3.  **Analysis**: `meta_analysis.py` reads records -> `results/meta_analysis_result.json`.
4.  **Visualization**: `visualization.py` reads result -> `results/plots/` (PNGs).
5.  **Output**: Final JSON report and PNGs.

## Validation Rules

- **Study Count**: Must be >= 1 for any analysis.
- **Tract Count**: Must be >= 1.
- **Effect Size Range**: `r` must be [-1, 1].
- **Precision**: `i_squared` must be formatted to 2 decimal places.
- **Skip Logic**: If `study_count` < 10, `egger_p` must be null and `egger_skipped_reason` must be set.
