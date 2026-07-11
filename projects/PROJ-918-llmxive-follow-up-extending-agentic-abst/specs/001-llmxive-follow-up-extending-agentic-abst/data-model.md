# Data Model: llmXive follow-up: extending "Agentic Abstention: Do Agents Know When to Stop Instead of Act?"

## Overview

This document defines the data models for the Meta-Critic system, including the feature-engineered dataset, model inputs/outputs, and analysis results. All data models are designed for CPU-optimized processing and strict schema validation.

## Feature-Engineered Dataset

### Schema: `feature_dataset.parquet`

| Column Name | Type | Description | Source/Constraint |
|-------------|------|-------------|-------------------|
| `task_id` | string | Unique identifier for the task | From raw dataset |
| `turn_number` | integer | Current turn number in the trajectory | Extracted from log |
| `cumulative_token_usage` | float | Total tokens used up to current turn | Extracted from log |
| `search_result_count` | integer | Number of search results retrieved | Extracted from log |
| `error_frequency` | integer | Count of unique error types encountered | Extracted from log |
| `query_context_embedding_distance` | float | Cosine similarity between initial query and current context | Computed via `all-MiniLM-L6-v2` |
| `abstention_label` | boolean | Ground truth: True if task is "impossible" (Semantic Exhaustion) | Derived from Independent Oracle (Semantic check, not token limit) |
| `is_impossible` | boolean | Boolean flag for task impossibility | From oracle |
| `time_to_event` | float | Turn number where abstention occurred or hard stop reached | Used for survival analysis |
| `event_observed` | boolean | True if abstention occurred, False if hard stop reached | Used for survival analysis |

### Constraints

- **No Full Context**: Full semantic context strings are excluded.
- **Missing Data**: Numeric variables imputed with mean; categorical variables assigned "unknown".
- **Validation**: Schema validated against `contracts/dataset.schema.yaml`.

## Model Inputs/Outputs

### Meta-Critic Input: `state_feature_vector`

- **Type**: 1D array of floats/ints
- **Features**: `[turn_number, cumulative_token_usage, search_result_count, error_frequency, query_context_embedding_distance]`
- **Constraint**: Excludes full semantic context.

### Meta-Critic Output: `abstention_decision`

- **Type**: Boolean (True = abstain, False = continue)
- **Confidence**: Probability score (0.0 to 1.0)
- **Metadata**: Turn number, feature vector, timestamp

## Analysis Results

### Statistical Test Output: `statistical_results.json`

| Field | Type | Description |
|-------|------|-------------|
| `test_type` | string | "Log-Rank Test" (Survival Analysis) |
| `p_value` | float | p-value for difference in time-to-event distributions |
| `hazard_ratio` | float | Hazard ratio comparing Meta-Critic to Baseline |
| `effect_size` | float | Cohen's d for token consumption |
| `significance` | boolean | True if p < 0.05 |
| `utility_metric` | float | Token Savings per Correct Abstention |

### Sensitivity Analysis Output: `sensitivity_analysis.csv`

| Threshold | False_Positive_Rate | False_Negative_Rate | Inconsistency_Rate |
|-----------|---------------------|---------------------|--------------------|
| 0.40 | float | float | float |
| 0.45 | float | float | float |
| ... | ... | ... | ... |

## Data Flow

1. **Raw Dataset** → **Feature Extraction** → **Feature-Engineered Dataset**
2. **Feature-Engineered Dataset** → **Meta-Critic Training** → **Model File**
3. **Model File** + **Feature-Engineered Dataset** → **Simulation** → **Performance Metrics**
4. **Performance Metrics** → **Statistical Tests (Survival Analysis)** → **Analysis Results**

## Versioning

- All data files are checksummed and versioned in `state/projects/PROJ-918-llmxive-follow-up-extending-agentic-abst.yaml`.
- Derived data files include derivation metadata (source, script, timestamp).