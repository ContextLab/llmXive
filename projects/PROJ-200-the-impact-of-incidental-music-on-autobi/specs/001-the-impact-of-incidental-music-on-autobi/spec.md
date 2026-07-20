# Specification: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Introduction

This document outlines the requirements for a research pipeline investigating the relationship between incidental music exposure during adolescence and the vividness/valence of autobiographical memories later in life.

## 2. Functional Requirements

### FR-001: Primary Predictor Definition
The primary predictor variable is the `residualized_exposure_score`. This is derived by first calculating the `adolescent_exposure_score` (ratio of adolescent listens to total listens) and then regressing it against the track's `overall_popularity_score` to remove the confounding effect of general popularity.
Formula: `adolescent_exposure ~ overall_popularity`
The `residualized_exposure_score` is the residual from this regression: `residuals = observed - predicted`.

### FR-004: Aggregation Unit
All data aggregation (mean vividness, mean valence, exposure scores) must be performed at the **User-Track Pair** level. A single row in the analysis dataset represents one user's memory association with one specific track.

### FR-005: Unit of Analysis and Model Formula
The unit of analysis is the **User-Track Pair**.
The primary statistical model is a Linear Mixed-Effects Model (LMM) defined as:
`mean_vividness ~ residualized_exposure + popularity + (1|user_id)`
Where:
- `mean_vividness`: Average vividness rating for the specific User-Track pair.
- `residualized_exposure`: The residualized exposure score for the track.
- `popularity`: The overall popularity score of the track.
- `(1|user_id)`: Random intercept for each user to account for individual response biases.

### FR-006: Sensitivity Analysis
The pipeline must perform a sensitivity analysis by re-running the entire matching and aggregation process with different Levenshtein distance thresholds across a range of small integer values. For each threshold, the data must be **re-aggregated** to User-Track pairs and the model re-fitted to ensure stability of results.

### FR-007: Permutation Test Methodology
Significance testing must be performed via a **block-permutation** test on the **User-Track Pair** dataset.
- **Procedure**: Shuffle the `residualized_exposure_score` values among tracks while preserving the User-Track grouping structure. Specifically, keep the `mean_vividness` and `user_id` intact for each pair, but randomly reassign the exposure score assigned to that pair from the pool of available track scores.
- **Null Distribution**: Run a sufficient number of iterations (e.g., 1000) to establish a null distribution of the test statistic.
- **Comparison**: Compare the observed statistic from the original model against this null distribution to calculate a p-value.
- **Constraint**: Do not shuffle memory outcomes directly; shuffle the predictor variable while maintaining the structural integrity of the User-Track pairs.

### FR-008: Fallback Mechanism
If the proportion of missing birth years exceeds 50%, the pipeline must trigger a fallback mechanism to calculate a "Global Exposure" metric using aggregate population data instead of individual birth-year windows.

## 3. Success Criteria

### SC-004: Match Rate Threshold
The pipeline must verify that the track matching rate is ≥ 80%. If the rate is below [deferred], the pipeline must **LOG A WARNING** and proceed with the analysis rather than halting execution. This ensures robustness against noisy cue data.

## 4. Edge Cases and Error Handling

### EC-001: Missing Birth Years
**The fallback check for missing birth years (>50%) MUST be performed BEFORE applying the Minimum Listen Threshold filter to prevent empty datasets.** If the fallback check is performed after filtering by listen count, the dataset may be reduced to a size where the missing birth year proportion artificially exceeds the threshold, causing a false fallback trigger or an empty result set.

### EC-002: Zero Variance Tracks
Tracks with high exposure but zero memory cues (no matches) must be filtered out prior to modeling to avoid singularities in the design matrix.

### EC-003: Multicollinearity
If the Variance Inflation Factor (VIF) for `residualized_exposure` or `popularity` exceeds 5, a warning must be logged, and the results should be interpreted with caution.

## 5. Data Sources

- **Million Song Dataset (MSD)**: For track metadata and listen counts.
- **Autobiographical Memory Test (AMT)**: For free-text cues and memory ratings (vividness/valence).

## 6. Output Artifacts

- `data/processed/ingested_cohort.parquet`: Cohort data with exposure scores.
- `data/processed/user_track_pairs.parquet`: Aggregated data at the User-Track Pair level.
- `data/final/regression_summary.csv`: Model coefficients and statistics.
- `data/final/sensitivity_analysis.csv`: Results across different matching thresholds.
- `data/final/permutation_results.csv`: Null distribution and p-value from permutation test.
- `data/final/plots/`: Diagnostic plots (residuals, QQ plots).