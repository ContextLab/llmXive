# Data Model: Counterfactual Inspector Agent

## 1. Overview

This document defines the data structures used in the Counterfactual Inspector Agent. All data is stored as JSON/Parquet in `data/` (raw) and `output/` (derived). The model ensures traceability from raw data to final narrative.

## 2. Core Entities

### 2.1 Dataset
- **Source**: Raw CSV/Parquet from verified URLs.
- **Fields**:
  - `id`: Unique identifier (hash of filename + checksum).
  - `url`: Verified source URL.
  - `rows`: Number of rows.
  - `columns`: List of column names and types.
  - `numeric_columns`: List of numeric column names.
  - `checksum`: SHA-256 of the raw file.
  - `is_synthetic`: Boolean (True if synthetic, used to exclude from final evaluation).

### 2.2 Baseline Narrative
- **Source**: `narrative/baseline.py`.
- **Fields**:
  - `dataset_id`: Reference to Dataset.
  - `primary_pair`: Tuple `(var_x, var_y)`.
  - `correlation`: Pearson $r$ value.
  - `p_value`: Significance level.
  - `n_samples`: Sample size.
  - `narrative_text`: Generated text summary.
  - `query`: Python/Pandas code used to generate the result.
  - `baseline_type`: Enum ["standard", "random"].

### 2.3 Counterfactual Insight
- **Source**: `narrative/inspector.py`.
- **Fields**:
  - `baseline_id`: Reference to Baseline Narrative.
  - `counterfactual_pair`: Tuple `(var_x, var_y)`.
  - `partial_correlation`: Partial $r$ value (controlling for confounders).
  - `p_value`: Significance level.
  - `threshold_config`: Dict `{corr_threshold: 0.3, p_threshold: 0.05}`.
  - `robustness_score`: Float (0.0-1.0, based on stability across thresholds).
  - `effect_size_valid`: Boolean (True if |r| >= 0.2).
  - `n_samples`: Sample size.
  - `insight_text`: Generated text summary of the counterfactual.
  - `query`: Python/Pandas code used to generate the result.
  - `is_distinct`: Boolean (true if pair introduces a new variable not in top 3 baseline correlations).
  - `power_warning`: Boolean (true if $n < 30$).
  - `confounders_adjusted`: List of variable names used in partial correlation.
  - `sign_flip_validated`: Boolean (true if sign flip persists after confounder adjustment).

### 2.4 Integrated Story
- **Source**: `narrative/synthesizer.py`.
- **Fields**:
  - `story_id`: Unique identifier.
  - `baseline_narrative`: Embedded Baseline Narrative object.
  - `counterfactual_insights`: List of Counterfactual Insight objects.
  - `final_text`: Full synthesized narrative.
  - `citation_count`: Number of valid query citations.
  - `generated_at`: Timestamp.

### 2.5 Evaluation Metrics
- **Source**: `evaluation/rubric.py`, `evaluation/bias.py`.
- **Fields**:
  - `story_id`: Reference to Integrated Story.
  - `rubric_scores`: Dict `{novelty: 1-5, evidence: 1-5, nuance: 1-5, clarity: 1-5}`.
  - `bias_improvement_score`: Float (Delta between Inspector and Baseline diversity).
  - `traceability_score`: Percentage of claims with valid citations.
  - `runtime_seconds`: Execution time.
  - `max_memory_mb`: Peak memory usage.
  - `statistical_test_result`: Dict `{test_type: "ttest_rel", p_value: float, significant: boolean}`.

## 3. Data Flow

```mermaid
graph TD
    A[Raw Dataset] --> B[Data Loader]
    B --> C{Valid Numeric Columns?}
    C -- No --> D[Skip & Log]
    C -- Yes --> E[Processor: Impute/Filter]
    E --> F[Baseline Narrative Generator (Standard & Random)]
    E --> G[Counterfactual Inspector: Partial Correlation + Robustness]
    F --> H[Baseline Narrative Object]
    G --> I[Counterfactual Insight Objects]
    H --> J[Synthesizer]
    I --> J
    J --> K[Integrated Story]
    K --> L[Evaluation Module]
    L --> M[Evaluation Metrics + Statistical Test]
```

## 4. Constraints & Validation

- **Numeric Columns**: Must be ≥ 5 for baseline generation.
- **Sample Size**: If $n < 30$, `power_warning` must be set to `True`.
- **Causal Language**: `narrative_text` and `insight_text` must not contain "causes", "leads to", etc., unless randomization is present.
- **Query Execution**: All `query` fields must be executable Python code that reproduces the reported statistics.
- **Checksums**: All raw data files must have a recorded SHA-256 checksum.
- **Robustness**: Counterfactuals must have `robustness_score` > 0.5 to be included in the final story.
- **Effect Size**: Counterfactuals must have `effect_size_valid` = True to be considered distinct.
- **Distinctness**: Counterfactuals must be `is_distinct` = True (not in top 3 correlations).
- **Confounder Adjustment**: Counterfactuals must have `confounders_adjusted` list populated.
