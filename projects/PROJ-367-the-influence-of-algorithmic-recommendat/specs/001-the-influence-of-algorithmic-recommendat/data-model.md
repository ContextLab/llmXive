# Data Model: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Overview

This document defines the data structures, transformations, and schemas used in the analysis pipeline. It ensures that all data flows are traceable and reproducible, adhering to the "Single Source of Truth" principle.

## Entities

### 1. UserSession
Represents a single observation window for a specific user.
- **user_id**: Unique identifier for the user.
- **session_id**: Unique identifier for the session.
- **recommended_categories**: List of category labels recommended by the algorithm. **Used directly for entropy calculation; no merging.**
- **enrolled_categories**: List of category labels enrolled in by the user. **Used directly for entropy calculation; no merging.**
- **baseline_interest_vector**: Vector representing historical preferences (pre-study). **Users with no baseline history are excluded from the dataset.**
- **recommendation_diversity_score**: Shannon entropy (log base 2) of `recommended_categories`.
- **learner_diversity_score**: Shannon entropy (log base 2) of `enrolled_categories`.
- **propensity_score**: Estimated probability of receiving a high-diversity recommendation.
- **weight**: Stabilized propensity score weight.
- **excluded**: Boolean flag indicating if the row was excluded (e.g., empty enrollments or no baseline history).

### 2. DiversityScore
A scalar value representing the Shannon entropy of a list of categories.
- **value**: Float (entropy value).
- **base**: Integer (log base, always 2).
- **null_handling**: If the input list is empty, the value is `null`.

### 3. ModelResult
The output object containing model diagnostics and estimates.
- **coefficient**: Float (fixed effect of `Recommendation_Diversity`).
- **standard_error**: Float.
- **p_value**: Float.
- **vif**: Float (Variance Inflation Factor for `Baseline_Interest`).
- **convergence_status**: Boolean.
- **effective_sample_size**: Integer.
- **extreme_weights_flag**: Boolean (true if any weight > 10x median).
- **overlap_weighting_applied**: Boolean (true if overlap weighting was used).
- **rows_trimmed**: Integer (number of rows trimmed for overlap weighting).
- **runtime_warning**: String (warning if runtime > 6 hours, or null).

## Data Flow

1. **Ingestion**: Raw data (CSV/Parquet) is loaded and validated for required columns (`recommended_categories`, `enrolled_categories`). **If missing, `DataSchemaError` is raised.** **A statistical test ensures the predictor is not mechanically derived from the outcome.**
2. **Preprocessing**:
   - **No category merging is performed.** Raw labels are used.
   - `baseline_interest_vector` is derived from pre-study history. **Users with no baseline history are excluded.**
   - `recommendation_diversity_score` and `learner_diversity_score` are calculated directly on raw labels.
   - Rows with empty `enrolled_categories` or no baseline history are excluded and logged.
3. **Modeling**:
   - Propensity scores are estimated.
   - Stabilized weights are calculated.
   - **If extreme weights are detected, Overlap Weighting is applied.**
   - Weighted linear regression is fitted (or GLS if N < 30).
4. **Robustness**:
 - **Residual Permutation Test** is executed ([deferred] iterations).
   - **No sensitivity analysis for semantic thresholds is performed.**
5. **Reporting**:
   - Final metrics are aggregated.
   - Results are framed as associational.
   - Runtime is recorded; if > 6h, a warning flag is set.

## Schema Definitions

### Raw Data Schema
```yaml
user_id: string
session_id: string
recommended_categories: list[string]
enrolled_categories: list[string]
# Optional: pre-study enrollment history for baseline calculation
```

### Processed Data Schema
```yaml
user_id: string
session_id: string
recommendation_diversity_score: float | null
learner_diversity_score: float | null
baseline_interest_vector: list[float]
propensity_score: float
weight: float
excluded: boolean
```

### Output Schema
```yaml
coefficient: float
standard_error: float
p_value: float
vif: float
convergence_status: boolean
effective_sample_size: integer
extreme_weights_flag: boolean
overlap_weighting_applied: boolean
rows_trimmed: integer
permutation_p_value: float
total_runtime_seconds: number
runtime_warning: string | null
warning: string
```

## Assumptions

- **Baseline Imputation**: **No imputation is performed.** Users with no prior enrollment history are excluded from the analysis to avoid systematic bias.
- **Category Merging**: **No category merging is performed.** Diversity is calculated directly on raw category labels.
- **Null Handling**: Empty `enrolled_categories` lists result in `null` for `learner_diversity_score` and exclusion from analysis.
- **Causal Independence**: **A verification step ensures the predictor is not mechanically derived from the outcome.**
- **Runtime**: The pipeline is designed to complete within 6 hours. If it exceeds this, a warning flag is set rather than a hard crash.