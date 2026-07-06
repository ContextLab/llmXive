# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

## Overview

This document defines the data structures for the ingestion, processing, and output phases of the analysis pipeline. It ensures alignment with the functional requirements (FR-001 to FR-007) and the project constitution.

## Input Data Model (Raw)

The system ingests a single CSV/TSV file (wide-format) containing the following columns:

| Column Name | Type | Description | Required? |
| :--- | :--- | :--- | :--- |
| `subject_id` | String | Unique identifier for the subject. | Yes |
| `taxon_A_abundance` | Float/Int | Abundance count for Taxon A. | Yes (Dynamic, pattern: `^taxon_.*_abundance$`) |
| `taxon_B_abundance` | Float/Int | Abundance count for Taxon B. | Yes (Dynamic) |
| ... | ... | ... | ... |
| `rem_duration_min` | Float | REM sleep duration in minutes. | Yes |
| `sws_duration_min` | Float | Slow-Wave Sleep duration in minutes. | Yes |
| `total_sleep_time_min` | Float | Total sleep time in minutes. | Yes |
| `sleep_efficiency_pct` | Float | Sleep efficiency percentage. | Yes |

**Validation Rules**:
- All numeric columns must be non-negative (for counts) or within physiological bounds (for sleep).
- Missing values (`NaN`) in required outcome variables must trigger a halt (FR-001).
- Zero-inflation check is performed on all taxon columns.
- Outlier detection performed on sleep metrics.

## Intermediate Data Model (Processed)

After ingestion, cleaning, and transformation:
- **Index**: `subject_id`
- **Predictor Matrix (X)**: `DataFrame` of shape `(N, M)` where `M` is the number of taxa. **Values are CLR-transformed.**
- **Outcome Vector (y)**: `Series` or `DataFrame` of shape `(N, K)` where `K` is the number of sleep metrics. **Outliers removed.**
- **Metadata**: Dictionary containing distribution statistics (Shapiro-Wilk p-value, zero proportion) for each predictor.
- **Diagnostics**: Dictionary containing `outlier_count`, `vif_scores`, `power_status`.

## Output Data Model (Results)

The primary output is a structured JSON/Parquet file containing correlation results:

| Field | Type | Description |
| :--- | :--- | :--- |
| `taxon_name` | String | Name of the microbial taxon. |
| `sleep_metric` | String | Name of the sleep metric. |
| `method_used` | String | "Pearson", "Spearman", or "ZINB". |
| `correlation_coefficient` | Float | Estimated correlation coefficient. |
| `p_value_raw` | Float | Raw p-value from the test. |
| `p_value_adjusted` | Float | Benjamini-Hochberg adjusted p-value. |
| `is_significant` | Boolean | True if `p_value_adjusted <= 0.05`. |
| `interpretation` | String | "Associational relationship observed." |

## Diagnostics Data Model

Separate output for diagnostics:

- **Sensitivity**: JSON object mapping thresholds (`0.01`, `0.05`, `0.10`) to counts of significant findings.
- **Collinearity**: List of dictionaries with `taxon_pair`, `vif` (or "Perfect Multicollinearity"), and `status`.
- **Power**: JSON object with `observed_N`, `min_N_required` (for r=0.1), `power_estimate`, `status` ("Underpowered" or "Adequate").
- **Outliers**: JSON object with `metric_name`, `outlier_count`, `excluded_indices`.