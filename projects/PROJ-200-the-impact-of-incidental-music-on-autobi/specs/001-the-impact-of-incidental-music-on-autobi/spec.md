# Specification: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Introduction

This document defines the requirements for analyzing the relationship between
adolescent music exposure and the vividness/valence of autobiographical memories
cued by those tracks.

## 2. Functional Requirements

### FR-001: Exposure Score Calculation
The system must calculate a `residualized_exposure_score` for each track.
This is derived from the `adolescent_exposure_score` (ratio of listens during
the user's adolescent window to total valid listens) adjusted for the track's
overall popularity.
Formula: `residualized_exposure_score = residuals from OLS(adolescent_exposure_score ~ overall_popularity_score)`.

### FR-002: Data Sources
The system must ingest data from the Million Song Dataset (MSD) and the
Autobiographical Memory Test (AMT) corpus.

### FR-003: Cohort Filtering
The system must filter out users with missing or invalid `birth_year` data.
The adolescent window is defined as `birth_year + 10` to `birth_year + 19`.

### FR-004: Aggregation Unit
All metrics must be aggregated at the **User-Track Pair** level.
Aggregation includes mean vividness, mean valence, and the associated exposure score.

### FR-005: Statistical Model
The primary analysis must use a Linear Mixed-Effects Model with the following formula:
`mean_vividness ~ residualized_exposure + popularity + (1|user_id)`
The unit of analysis is the **User-Track Pair**.

### FR-006: Sensitivity Analysis
The system must re-run the matching and aggregation pipeline using different
Levenshtein distance thresholds (2, 4, 6) to verify result stability.
Crucially, this requires **re-aggregation** of data to User-Track pairs for each threshold.

### FR-007: Permutation Test
The system must perform a **block-permutation** test.
Procedure: Shuffle `residualized_exposure_score` values among tracks while preserving
the User-Track grouping structure (keeping `mean_vividness` and `user_id` intact for each pair).
This generates a null distribution to test the significance of the observed effect.

### FR-008: Fallback Mechanism
If >50% of the cohort lacks birth year data, the system must trigger a fallback
to calculate a "Global Exposure" metric instead of individual adolescent scores.

## 3. Success Criteria

### SC-001: Match Rate
The system must achieve a track-to-cue match rate of at least 80% using
Levenshtein distance ≤ 4.

### SC-002: Model Convergence
The mixed-effects model must converge successfully. If not, a diagnostic report
must be generated.

### SC-003: Significance
The permutation test p-value must be < 0.05 to claim statistical significance.

### SC-004: Warning on Low Match Rate
If the match rate drops below 80%, the system must **log a warning** and proceed
with the analysis rather than halting the pipeline.

## 4. Edge Cases and Error Handling

### EC-001: Missing Birth Years
The system must handle missing `birth_year` values by excluding those records
from the adolescent window calculation.

### EC-002: Zero Listens
Tracks with zero listens in the adolescent window must receive an `adolescent_exposure_score` of 0.0.

### EC-003: Empty Cohort After Filtering
If filtering results in an empty dataset, the pipeline must fail loudly with a clear error message.

### EC-004: Ordering of Filters (Critical)
**The fallback check for missing birth years (>50%) MUST be performed BEFORE applying the Minimum Listen Threshold filter to prevent empty datasets.**
If the Minimum Listen Threshold were applied first, a sparse dataset might be reduced to zero rows before the fallback logic could trigger the global exposure metric, leading to a premature pipeline failure instead of a valid fallback execution.

## 5. Data Outputs

- `data/processed/ingested_cohort.parquet`: Raw cohort data with exposure scores.
- `data/processed/user_track_pairs.parquet`: Aggregated data at User-Track level.
- `data/final/regression_summary.csv`: Model coefficients and p-values.
- `data/final/sensitivity_analysis.csv`: Results across different thresholds.
- `data/final/permutation_results.csv`: Null distribution statistics.