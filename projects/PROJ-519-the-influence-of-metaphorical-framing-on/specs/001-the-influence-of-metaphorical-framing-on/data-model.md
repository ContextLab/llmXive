# Data Model: The Influence of Metaphorical Framing on Attitudes Towards Mental Health Treatment

## Overview

This document defines the data structures for the experimental and discourse analysis components. All data is stored in CSV or Parquet formats, with raw data remaining immutable and derived data versioned.

## Entities

### 1. Participant (Experimental)
Represents a single simulated participant in the vignette study.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | String | Unique identifier (e.g., "P-0001") | PK, Non-null |
| `condition` | String | Assigned vignette type | Enum: ["Battle", "Journey", "Medical"] |
| `vignette_text` | String | The exact text shown (immutable) | Non-null |
| `cami_score` | Float | Total CAMI score (continuous) | Range: 0-100 (or scale max) |
| `help_intent` | Integer | Help-seeking intent (Likert) | Range: 1-5 |
| `attention_check` | Boolean | Passed attention check | Non-null |
| `timestamp` | ISO8601 | Simulation timestamp | Non-null |

### 2. DiscoursePost (Observational)
Represents a unit of public text (or synthetic equivalent) for discourse analysis.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `post_id` | String | Unique identifier | PK, Non-null |
| `source` | String | Source label (e.g., "synthetic-fallback") | Non-null |
| `text` | String | Raw text content | Non-null |
| `metaphor_keywords` | String | Comma-separated list of found keywords | Nullable |
| `metaphor_count` | Integer | Count of metaphor keywords | ≥ 0 |
| `vader_compound` | Float | VADER compound sentiment score (raw) | Range: -1 to 1 |
| `vader_positive` | Float | VADER positive score | Range: 0 to 1 |
| `vader_negative` | Float | VADER negative score | Range: 0 to 1 |
| `vader_neutral` | Float | VADER neutral score | Range: 0 to 1 |
| `post_length` | Integer | Character count of text | ≥ 0 |
| `engagement_score` | Float | Simulated engagement metric | ≥ 0 |
| `is_stress_test` | Boolean | Flag indicating if this row is part of the stress test (known correlation) | Default: False |

### 3. StatisticalResult
Represents the output of an analysis run.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `result_id` | String | Unique identifier | PK |
| `analysis_type` | String | "ANOVA", "Regression", "VIF" | Enum |
| `test_statistic` | Float | F-value, t-value, etc. | Non-null |
| `p_value` | Float | P-value | Range: 0-1 |
| `effect_size` | Float | Cohen's f, R², etc. | Nullable |
| `adjusted_alpha` | Float | Adjusted significance threshold | Nullable |
| `significant` | Boolean | Result significance flag | Non-null |
| `model_params` | JSON | Full model coefficients/SEs | Nullable |
| `vif_values` | JSON | VIF for each predictor | Nullable |
| `timestamp` | ISO8601 | Run timestamp | Non-null |

**Separation Note**: The `StatisticalResult` entity is a container for *distinct* results. The `analysis_type` field explicitly separates ANOVA (experimental) from Regression (observational). The two streams are never merged into a single statistical inference, ensuring Principle VII (Psychometric Measurement Separation) is maintained. The `is_stress_test` flag in `DiscoursePost` allows for separate validation of the regression engine without conflating the null and signal results.

## File Layout

```text
data/
├── raw/
│   ├── vignette_templates.json       # Immutable vignette texts
│   └── synthetic_discourse.csv       # Fallback discourse data
├── processed/
│   ├── experimental_data.csv         # Participant data (cleaned)
│   └── discourse_data.csv            # Processed discourse (with VADER)
└── derived/
    ├── anova_results.json
    ├── regression_results.json
    └── figures/
        ├── anova_bar_chart.png
        └── regression_scatter.png
```

## Data Hygiene Rules

1. **Checksums**: Every file in `data/` must have a corresponding SHA-256 hash recorded in `state/projects/...yaml`.
2. **Immutability**: Files in `raw/` are never modified. Derivations in `processed/` and `derived/` are written as new files with version suffixes if the source changes.
3. **PII**: No personal identifiers are stored. `participant_id` is a synthetic UUID.
4. **Separation**: `vignette_text` (stimulus) is stored separately from `cami_score` (outcome) to prevent circularity.
5. **Versioning**: Synthetic data generation parameters are stored in `config/simulation_config.yaml` to ensure reproducibility.