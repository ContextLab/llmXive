# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

## Overview

This document defines the data models, schemas, and relationships for the gut microbiome and sleep quality analysis pipeline. It ensures data integrity and consistency throughout the pipeline.

**Note**: The data model is conditional on the availability of the source dataset. If the source dataset lacks required fields, the pipeline will halt.

## Entities

### MicrobiomeSample

Represents a single participant's gut flora data and associated metadata.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `sample_id` | string | Unique identifier for the sample | Primary Key, Not Null |
| `age` | integer | Participant age | >= 0, **Conditional on source** |
| `bmi` | float | Body Mass Index | >= 0, Not Null for multivariate analysis, **Conditional on source** |
| `antibiotic_use_last_3m` | boolean | Antibiotic use in last 3 months | Not Null, **Conditional on source** |
| `sleep_efficiency` | float | Sleep efficiency (%) | 0.0 - 100.0, Not Null, **Conditional on source** |
| `sleep_duration_hours` | float | Sleep duration (hours) | > 0.0, Not Null, **Conditional on source** |
| `shannon_diversity` | float | Shannon index | >= 0.0 |
| `simpson_diversity` | float | Simpson index | 0.0 - 1.0 |
| `observed_otus` | integer | Observed OTUs count | >= 0 |

**Validation Note**: If the source dataset does not contain `sleep_efficiency`, `sleep_duration_hours`, or `antibiotic_use_last_3m`, the pipeline must halt with a clear error message indicating the missing fields. These fields are not optional for the analysis as specified.

### CorrelationResult

Represents the statistical output of a single correlation test.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `diversity_metric` | string | Name of the diversity metric (e.g., "shannon") | Not Null |
| `sleep_metric` | string | Name of the sleep metric (e.g., "efficiency") | Not Null |
| `r_value` | float | Spearman correlation coefficient | -1.0 - 1.0 |
| `p_value` | float | Raw p-value | 0.0 - 1.0 |
| `q_value` | float | Benjamini-Hochberg adjusted p-value | 0.0 - 1.0 |
| `is_significant` | boolean | True if q_value < 0.05 | Not Null |
| `is_moderate` | boolean | True if |r_value| > 0.3 | Not Null |

## Data Flow

1.  **Raw Data**: Downloaded from AGP (OTU tables + metadata). **If not found, halt.**
2.  **Feasibility Check**: Verify presence of required columns (`sleep_efficiency`, `sleep_duration_hours`, `antibiotic_use_last_3m`). **If missing, halt.**
3.  **Filtered Data**: Samples with antibiotic use or missing sleep data are removed.
4.  **Enriched Data**: Alpha-diversity indices are computed (with rarefaction) and added to the filtered dataset.
5.  **Analysis Output**: Correlation results are generated and stored.
6.  **Visualization Output**: Plots are generated from significant results.

## Storage Format

- **Raw Data**: Parquet or CSV (preserved unchanged).
- **Filtered/Enriched Data**: CSV (analysis-ready).
- **Correlation Results**: JSON or CSV.
- **Plots**: PNG.

## Validation Rules

- All numeric fields must be within valid ranges.
- No missing values in critical fields (`sleep_efficiency`, `sleep_duration_hours`, `antibiotic_use_last_3m`) **if the source provides them**. If the source lacks these fields, the pipeline halts.
- Diversity indices must be non-negative.
- Correlation coefficients must be between -1 and 1.