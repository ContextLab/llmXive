# Specification: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Introduction

This document outlines the requirements for a research pipeline investigating the relationship between incidental music exposure during adolescence and the vividness/valence of autobiographical memories later in life.

## 2. User Scenarios & Testing

### User Story 1 - Define and Calculate Exposure Metrics (Priority: P1)

As a researcher, I need the system to calculate the 'adolescent_exposure_ratio' for each user-track pair so that I can quantify the proportion of music exposure occurring during the user's adolescence.

**Why this priority**: This is the core predictor variable for the entire study. Without this metric, the primary research question cannot be answered.

**Independent Test**: Can be fully tested by running the exposure calculation script on a mock dataset with known birth years and listen timestamps, verifying the ratio matches manual calculations.

**Acceptance Scenarios**:

1. **Given** a user with birth year 1990 and listen history, **When** the system calculates the adolescent exposure ratio, **Then** the ratio is (listens between 1990-2005) / (total listens).
2. **Given** a track with no listens during the user's adolescence, **When** the system calculates the ratio, **Then** the ratio is 0.0.

(See US-001)

### User Story 2 - Verify Data Quality and Handling (Priority: P2)

As a data analyst, I need the system to verify the track matching rate and handle cases with low match rates so that I can ensure the analysis is robust against noisy cue data.

**Why this priority**: Data quality is a prerequisite for valid statistical inference. If the matching rate is too low, the results may be unreliable.

**Independent Test**: Can be fully tested by providing a dataset with a known match rate (e.g., [deferred]) and verifying the system logs a warning but proceeds.

**Acceptance Scenarios**:

1. **Given** a dataset with a match rate of [deferred], **When** the pipeline runs, **Then** no warning is logged.
2. **Given** a dataset with a match rate of [deferred], **When** the pipeline runs, **Then** a warning is logged and the analysis proceeds.

(See US-002)

### User Story 3 - Handle Edge Cases and Robustness (Priority: P3)

As a system operator, I need the pipeline to handle missing birth years, zero-variance tracks, and multicollinearity so that the analysis does not crash and results are interpretable.

**Why this priority**: Real-world data is messy. The system must fail gracefully or apply fallbacks to ensure the pipeline completes.

**Independent Test**: Can be fully tested by injecting missing birth years, zero-variance tracks, and highly correlated predictors into a test dataset and verifying the fallbacks and warnings trigger correctly.

**Acceptance Scenarios**:

1. **Given** a dataset with >50% missing birth years, **When** the pipeline runs, **Then** the 'Global Exposure' fallback is triggered.
2. **Given** a track with no memory cues, **When** the pipeline runs, **Then** the track is filtered out.
3. **Given** a model with VIF > 5, **When** the pipeline runs, **Then** a warning is logged.

(See US-003)

## 3. Functional Requirements

### FR-001: Primary Predictor Definition (See US-001)
The primary predictor variable is the `adolescent_exposure_ratio`. This is defined as the ratio of the number of listens to a specific track during the user's adolescence (defined as birth year to birth year + 15) to the total number of listens to that track by the user.
Formula: `adolescent_exposure_ratio = listens_adolescence / total_listens`
*Note: This raw ratio is used to directly test the 'incidental exposure' hypothesis, controlling for popularity in the model (FR-005) rather than pre-residualizing, to avoid statistical tautology.*

### FR-004: Aggregation Unit (See US-001)
All data aggregation (mean vividness, mean valence, exposure scores) must be performed at the **User-Track Pair** level. A single row in the analysis dataset represents one user's memory association with one specific track.

### FR-005: Unit of Analysis and Model Formula (See US-001)
The unit of analysis is the **User-Track Pair**.
The primary statistical model is a Linear Mixed-Effects Model (LMM) defined as:
`mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)`
Where:
- `mean_vividness`: Average vividness rating for the specific User-Track pair.
- `adolescent_exposure_ratio`: The raw ratio of adolescent listens to total listens for the track.
- `popularity`: The overall popularity score of the track (used as a control covariate).
- `(1|user_id)`: Random intercept for each user to account for individual response biases.

### FR-006: Sensitivity Analysis (See US-001)
The pipeline must perform a sensitivity analysis by re-running the entire matching and aggregation process with different Levenshtein distance thresholds across a range of values.
For each threshold in the list `[1, 2, 3, 4, 5]`, the data must be **re-aggregated** to User-Track pairs and the model re-fitted to ensure stability of results.

### FR-007: Permutation Test Methodology (See US-001)
Significance testing must be performed via a **block-permutation** test on the **User-Track Pair** dataset.
- **Procedure**: Shuffle the `mean_vividness` values **within each user block** (i.e., permute the outcomes for a specific user across their tracks) while keeping the `user_id` and predictor values (`adolescent_exposure_ratio`, `popularity`) fixed for each row.
- **Null Distribution**: Run 1000 iterations to establish a null distribution of the test statistic (the coefficient for `adolescent_exposure_ratio`).
- **Comparison**: Compare the observed statistic from the original model against this null distribution to calculate a p-value.
- **Constraint**: Do not shuffle the predictor variable directly; shuffle the outcome within user blocks to preserve the user-level correlation structure.

### FR-008: Fallback Mechanism (See US-001)
If the proportion of missing birth years exceeds 50%, the pipeline must trigger a fallback mechanism to calculate a "Global Exposure" metric.
The "Global Exposure" metric is defined as the mean `adolescent_exposure_ratio` across all available tracks in the Million Song Dataset for the user's birth decade (e.g., if birth year is 1990, use tracks released between 1980-1999). This serves as a population-level proxy for the missing individual data.

### FR-009: Minimum Listen Threshold (See US-003)
The pipeline must filter out user-track pairs where the `total_listens` is less than 3. This ensures that the exposure ratio is based on a sufficient number of listening events to be meaningful.

## 4. Success Criteria

### SC-004: Match Rate Threshold (See US-002)
The pipeline must verify that the track matching rate is ≥ 80%. If the rate is below [deferred], the pipeline must **LOG A WARNING** and proceed with the analysis rather than halting execution. This ensures robustness against noisy cue data.

## 5. Edge Cases and Error Handling

### EC-001: Missing Birth Years (See US-003)
The fallback check for missing birth years (>50%) MUST be performed BEFORE applying the Minimum Listen Threshold filter (FR-009) to prevent empty datasets. If the fallback check is performed after filtering by listen count, the dataset may be reduced to a size where the missing birth year proportion artificially exceeds the threshold, causing a false fallback trigger or an empty result set.

### EC-002: Zero Variance Tracks (See US-003)
Tracks with high exposure but zero memory cues (no matches) must be filtered out prior to modeling to avoid singularities in the design matrix.

### EC-003: Multicollinearity (See US-003)
If the Variance Inflation Factor (VIF) for `adolescent_exposure_ratio` or `popularity` exceeds 5, a warning must be logged, and the results should be interpreted with caution.

## 6. Data Sources

- **Million Song Dataset (MSD)**: For track metadata and listen counts.
- **Autobiographical Memory Test (AMT)**: For free-text cues and memory ratings (vividness/valence).

## 7. Output Artifacts

- `data/processed/ingested_cohort.parquet`: Cohort data with exposure scores.
- `data/processed/user_track_pairs.parquet`: Aggregated data at the User-Track Pair level.
- `data/final/regression_summary.csv`: Model coefficients and statistics.
- `data/final/sensitivity_analysis.csv`: Results across different matching thresholds.
- `data/final/permutation_results.csv`: Null distribution and p-value from permutation test.
- `data/final/plots/`: Diagnostic plots (residuals, QQ plots).