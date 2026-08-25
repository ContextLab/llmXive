# Data Model: The Influence of Perceived Agency in AI Interactions on Trust

## Overview

This document defines the data structures for the experimental study, including the raw data schema, processed data schema, and analysis output schema. All data will be stored in CSV format for raw/processed data and JSON for configuration/results.

## Raw Data Schema

The raw data schema defines the structure of the CSV export from the data collection interface. This schema MUST conform to `contracts/participant.schema.yaml`.

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `participant_id` | String | Unique anonymous identifier | Not null, unique |
| `condition` | String | Experimental condition (High, Low, Control) | Enum: ["High", "Low", "Control"] |
| `adherence_rate` | Float | Percentage of AI recommendations followed | 0.0 to 100.0 |
| `trust_score` | Float | Sum/Average of Lee & See (2004) scale items | 1.0 to 7.0 (per item) or aggregated |
| `attention_check` | Boolean | Pass/Fail status | True/False |
| `completion_time` | Integer | Time in seconds | > 0 |
| `timestamp` | String | ISO 8601 timestamp of completion | Not null |
| `perceived_agency_score` | Float | Manipulation check (1-7 Likert) | 1.0 to 7.0 |
| `trust_item_1` ... `trust_item_12` | Integer | Individual scale items | 1 to 7 |

**Note on Adherence**: `adherence_rate` is treated as a secondary outcome. The primary power analysis is driven by `trust_score`.

## Processed Data Schema

The processed data schema defines the structure of the cleaned dataset used for analysis.

| Column | Type | Description | Derived From |
|--------|------|-------------|--------------|
| `participant_id` | String | Unique anonymous identifier | Raw |
| `condition` | Categorical | Experimental condition | Raw |
| `adherence_rate` | Float | Percentage of AI recommendations followed | Raw |
| `trust_score` | Float | Aggregated trust score (mean of items) | Raw (if raw items provided) or Raw (if aggregated) |
| `perceived_agency_score` | Float | Manipulation check score | Raw |
| `included` | Boolean | Whether the participant passed all filters | Computed (Attention Check + Completion Time) |

## Analysis Output Schema

The analysis output schema defines the structure of the statistical results.

| Key | Type | Description |
|-----|------|-------------|
| `planned_contrasts` | Object | Results of planned directional contrasts (High vs. Low) |
| `pairwise_comparisons` | Object | Results of post-hoc pairwise comparisons |
| `effect_sizes` | Object | Cohen's d for significant pairwise comparisons |
| `power_analysis` | Object | Pre-study power calculation results |
| `sensitivity_analysis` | Object | Results of threshold sensitivity sweep |

## Configuration Schema

The configuration schema defines the parameters for the analysis pipeline.

| Key | Type | Description |
|-----|------|-------------|
| `alpha` | Float | Significance level (default: 0.05) |
| `target_power` | Float | Target power (default: 0.80) |
| `effect_size` | Float | Expected effect size (default: 0.5 for contrast) |
| `exclusion_threshold` | Float | Minimum attention check pass rate (default: 0.8) |
| `random_seed` | Integer | Random seed for reproducibility |