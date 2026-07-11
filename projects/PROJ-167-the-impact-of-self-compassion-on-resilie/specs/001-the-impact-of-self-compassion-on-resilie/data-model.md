# Data Model: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Overview

This document defines the data structures, transformations, and schemas used in the analysis pipeline. It ensures that the data flowing from raw download to final report is consistent, validated, and traceable.

## Raw Data Schema

The raw dataset is expected to be a CSV file with the following columns. The pipeline will abort if any of these are missing.

| Column Name | Type | Description | Required |
|-------------|------|-------------|----------|
| `participant_id` | string | Unique ID | Yes |
| `scf_total` | float | Self-Compassion Total | Yes |
| `scf_self_judgment` | float | Self-Judgment Subscale | No |
| `scf_self_kindness` | float | Self-Kindness Subscale | Yes (for robustness) |
| `stai_pre` | float | Anxiety Pre | Yes |
| `stai_post` | float | Anxiety Post | Yes |
| `rrs_pre` | float | Rumination Pre | Yes |
| `rrs_post` | float | Rumination Post | Yes |
| `gse_pre` | float | Self-Efficacy Pre | Yes |
| `gse_post` | float | Self-Efficacy Post | Yes |
| `feedback_cond` | string | Feedback Condition | Yes |
| `age` | int | Age | Yes |
| `gender` | string | Gender | Yes |
| `bigfive_openness` | float | Big Five (Optional) | No |
| `bigfive_conscientiousness` | float | Big Five (Optional) | No |
| `bigfive_extroversion` | float | Big Five (Optional) | No |
| `bigfive_agreeableness` | float | Big Five (Optional) | No |
| `bigfive_neuroticism` | float | Big Five (Optional) | No |

## Processed Data Schema

After cleaning and transformation, the data will be stored in a Parquet file with the following structure:

| Column Name | Type | Transformation Logic |
|-------------|------|----------------------|
| `participant_id` | string | Original |
| `feedback_cond` | category | Encoded: 0=Positive, 1=Neutral, 2=Negative |
| `scf_total_z` | float | Z-score of `scf_total` |
| `scf_self_kindness_z` | float | Z-score of `scf_self_kindness` |
| `stai_pre` | float | Original (Covariate) |
| `stai_post` | float | Original (Outcome) |
| `rrs_pre` | float | Original (Covariate) |
| `rrs_post` | float | Original (Outcome) |
| `gse_pre` | float | Original (Covariate) |
| `gse_post` | float | Original (Outcome) |
| `age` | int | Original |
| `gender` | category | Encoded (Binary/Missing handling) |

## Output Artifacts

### 1. Analysis Result (JSON/Dict)
- **Structure**: Nested dictionary per outcome.
- **Keys**: `interaction_coef`, `interaction_se`, `interaction_pval`, `interaction_ci_lower`, `interaction_ci_upper`, `partial_eta2`, `vif_values`, `bootstrap_ci`.
- **Schema**: Must conform to `contracts/analysis_result.schema.yaml`.

### 2. Report HTML
- **Content**: Aggregated statistics, tables, plots, and caveats.
- **Schema**: Must conform to `contracts/report.schema.yaml`.

## Data Flow Diagram

1. **Raw CSV** (OSF) -> `download.py` -> **Raw CSV (Checksummed)**
2. **Raw CSV** -> `preprocess.py` -> **Processed Parquet** (Validation: N >= 92, Columns present, Enum values valid)
3. **Processed Parquet** -> `models.py` -> **Regression Results** (HC3, Bootstrap, Homogeneity Test)
4. **Regression Results** + **Processed Parquet** -> `visualize.py` -> **PNG Plots**
5. **All Artifacts** -> `report.py` -> **report.html**