# Specification: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Introduction

This document outlines the requirements for a research pipeline investigating the **association** between incidental music exposure during adolescence and the vividness/valence of autobiographical memories later in life. The observational design does not permit causal inference; results will be interpreted as correlational findings.

## 2. User Scenarios & Testing

### User Story 1 - Define and Calculate Exposure Metrics (Priority: P1)

As a researcher, I need the system to calculate the `adolescent_exposure_ratio` for each user‑track pair so that I can quantify the proportion of music exposure occurring during the user's adolescence.

**Why this priority**: This is the core predictor variable for the entire study. Without this metric, the primary research question cannot be answered.

**Independent Test**: Can be fully tested by running the exposure calculation script on a mock dataset with known birth years and track release years, verifying the ratio matches manual calculations.

**Acceptance Scenarios**:

1. **Given** a user with birth year 1990 and a set of tracks whose release years are known, **When** the system calculates the adolescent exposure ratio, **Then** the ratio is  
   `(# tracks with release year between 2000 and 2009) / (total # tracks listened by the user)`.  
   *(Adolescence defined as ages 10‑19, i.e., for birth year 1990 the adolescent years are 2000‑2009.)*
2. **Given** a user whose listened tracks all have release years outside the adolescent window, **When** the system calculates the ratio, **Then** the ratio is 0.0.

(See US-001)

### User Story 2 - Verify Data Quality and Handling (Priority: P2)

As a data analyst, I need the system to verify the track matching rate and handle cases with low match rates so that I can ensure the analysis is robust against noisy cue data.

**Why this priority**: Data quality is a prerequisite for valid statistical inference. If the matching rate is too low, the results may be unreliable.

**Independent Test**: Can be fully tested by providing a dataset with a known match rate and verifying the system logs a warning but proceeds.

**Acceptance Scenarios**:

1. **Given** a dataset with a match rate **≥ 80 %**, **When** the pipeline runs, **Then** no warning is logged.
2. **Given** a dataset with a match rate **< 80 %**, **When** the pipeline runs, **Then** a warning is logged and the analysis proceeds.

(See US-002)

### User Story 3 - Handle Edge Cases and Robustness (Priority: P3)

As a system operator, I need the pipeline to handle missing birth years, zero‑variance tracks, and multicollinearity so that the analysis does not crash and results are interpretable.

**Why this priority**: Real‑world data is messy. The system must fail gracefully or apply fallbacks to ensure the pipeline completes.

**Independent Test**: Can be fully tested by injecting missing birth years, zero‑variance tracks, and highly correlated predictors into a test dataset and verifying the fallbacks and warnings trigger correctly.

**Acceptance Scenarios**:

1. **Given** a dataset with >50 % missing birth years, **When** the pipeline runs, **Then** the ‘Global Exposure’ fallback is triggered.
2. **Given** a track with no memory cues, **When** the pipeline runs, **Then** the track is filtered out.
3. **Given** a model with VIF > 5, **When** the pipeline runs, **Then** a warning is logged.

(See US-003)

## 3. Functional Requirements

### FR-001: Primary Predictor Definition (See US-001)
The primary predictor variable is the `adolescent_exposure_ratio`. It is defined as the proportion of a user's listened tracks whose **release year falls within the user’s adolescence (ages 10‑19, inclusive)** to the total number of tracks the user has listened to.

Formula:  

```
adolescent_exposure_ratio = 
    (# tracks where release_year ∈ [birth_year+10, birth_year+19]) 
    / (total_tracks_listened)
```

*Justification*: The Million Song Dataset provides track release year metadata but not per‑user listening timestamps. Using release year as a proxy for exposure during adolescence is a standard practice when individual listening histories are unavailable (see e.g., prior work on cohort‑level exposure proxies). This preserves the original research question while remaining computable from the cited data source.

### FR-002: Track Matching Quality Check (See US-002)
The system MUST compute the overall track‑matching rate (fraction of cue‑track pairs successfully matched). If the rate is **< 80 %**, the pipeline MUST LOG A WARNING (including the actual rate) and continue execution.

### FR-003: Edge‑Case Handling (See US-003)
The pipeline MUST:

* Trigger the Global Exposure fallback (FR-008) when **> 50 %** of birth years are missing **before** applying the Minimum Listen Threshold filter.
* Filter out any user‑track pair where `total_listens` = 0 (zero‑variance track) prior to modeling.
* Compute Variance Inflation Factors for `adolescent_exposure_ratio` and `popularity`; if any VIF **> 5** (source 2605.22529), log a warning and flag results as requiring caution.

### FR-004: Aggregation Unit (See US-001)
All data aggregation (mean vividness, mean valence, exposure scores) must be performed at the **User‑Track Pair** level. A single row in the analysis dataset represents one user's memory association with one specific track.

### FR-005: Unit of Analysis and Model Formula (See US-001)
The unit of analysis is the **User‑Track Pair**.  
The primary statistical model is a Linear Mixed‑Effects Model (LMM) defined as:  

```
mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)
```

* `mean_vividness`: Average vividness rating for the specific User‑Track pair.  
* `adolescent_exposure_ratio`: Ratio defined in FR‑001.  
* `popularity`: Overall popularity score of the track (control covariate).  
* `(1|user_id)`: Random intercept for each user to account for individual response biases.

### FR-006: Sensitivity Analysis (See US-001)
The pipeline must perform a sensitivity analysis by re‑running the entire matching and aggregation process with different Levenshtein distance thresholds `[1, 2, 3, 4, 5]`. For each threshold, the data must be re‑aggregated to User‑Track pairs and the model re‑fitted. Results across thresholds must be corrected for multiple comparisons using a Bonferroni adjustment (α_adj = 0.05 / 5) and reported with adjusted p‑values.

### FR-007: Permutation Test Methodology (See US-001)
Significance testing must be performed via a **block‑permutation** test on the **User‑Track Pair** dataset.

* **Procedure**: Shuffle the `mean_vividness` values **within each user block** (i.e., permute outcomes for a specific user across their tracks) while keeping `user_id` and predictor values (`adolescent_exposure_ratio`, `popularity`, `total_listens`) fixed for each row.  
* **Iterations**: Perform **10,000** permutations.  
* **Null Distribution**: Collect the coefficient for `adolescent_exposure_ratio` from each permuted model.  
* **Two‑sided p‑value**: Compute the proportion of absolute null coefficients ≥ the absolute observed coefficient.  
* **Constraint**: Do not shuffle predictor variables directly; shuffle the outcome within user blocks to preserve the user‑level correlation structure.

### FR-008: Fallback Mechanism (See US-001)
If the proportion of missing birth years is notably high—exceeding a majority‑level threshold (> 50 %)—the pipeline must trigger a fallback mechanism to calculate a “Global Exposure” metric. The "Global Exposure" metric is defined as the mean `adolescent_exposure_ratio` across all available tracks in the Million Song Dataset for the user's birth decade (e.g., if birth year is 1990, use tracks released between 1980‑1999). This serves as a population‑level proxy for the missing individual data.

### FR-009: Minimum Listen Threshold (See US-003)
The pipeline must filter out user‑track pairs where the `total_listens` count is **< 5**. This ensures that the exposure ratio is based on a sufficient number of listening events to be meaningful.

### FR-010: Dataset Schema Alignment (See US-003)
The dataset schema (`contracts/dataset.schema.yaml`) must enforce `total_listens ≥ 5` to be consistent with FR‑009. Any records violating this minimum must be rejected during validation.

### FR-011: Power Analysis Requirement (See US-001)
Prior to final analysis, the pipeline MUST perform an a priori power analysis targeting **≥ 80 %** power to detect a small‑to‑medium effect (Cohen’s f² = 0.15) at α = 0.05 for the mixed‑effects model. The required sample size must be met or exceeded, and a post‑hoc power calculation must be reported.

### FR-013: Logit Transformation with Continuity Correction (See US-001)
When applying a logit transformation to `adolescent_exposure_ratio`, the pipeline MUST first adjust extreme values using a continuity correction:  

```
adjusted_ratio = (ratio * (N - 1) + 0.5) / N
logit_ratio = log(adjusted_ratio / (1 - adjusted_ratio))
```  

where `N` is the number of observations for the given user‑track pair. This prevents undefined logit(0) or logit(1) cases.

## 4. Success Criteria

### SC-001: Exposure Ratio Calculation Accuracy (See US-001)
On a synthetic validation dataset with known adolescent and total listen counts, the computed `adolescent_exposure_ratio` must equal the expected value within an absolute tolerance of 1 × 10⁻⁶.

### SC-002: Match Rate Verification (See US-002)
The pipeline must emit a warning when the track‑matching rate is **< 80 %** and must proceed without aborting. The warning must include the exact match‑rate percentage.

### SC-003: Edge‑Case Handling (See US-003)
* Fallback is triggered when missing birth years > 50 % (verified by log entry).  
* Zero‑variance tracks are removed before modeling (verified by absence in the final dataset).  
* If any VIF > 5, a warning is logged (verified by log entry).  

### SC-004: Match Rate Threshold (See US-002)
The pipeline must verify that the track matching rate is **≥ 80 %**. If the rate is below 80 %, the pipeline must LOG A WARNING and continue execution.

### SC-005: Power Analysis Confirmation (See FR-011)
The documented required sample size from FR‑011 must be met or exceeded in the final dataset, and a post‑hoc power calculation must report **≥ 80 %** power.

### SC-006: Sensitivity Analysis Reporting (See FR-006)
For each Levenshtein threshold, the model coefficients and Bonferroni‑adjusted p‑values must be reported in `data/final/sensitivity_analysis.csv`. At least one threshold must show a statistically significant effect after adjustment, or the result must be reported as non‑significant.

### SC-007: Permutation Test Reporting (See FR-007)
`data/final/permutation_results.csv` must contain the observed coefficient, the null distribution summary (mean, SD), and the two‑sided p‑value computed from 10,000 permutations.

### SC-008: Output Contract Conformance (See US-001)
All CSV artifacts (`regression_summary.csv`, `sensitivity_analysis.csv`, `permutation_results.csv`) conform to the schema defined in `contracts/output.schema.yaml`. No reference is made to `contracts/model_output.schema.yaml`, which is not required for this project.

## 5. Edge Cases and Error Handling

### EC-001: Missing Birth Years (See US-003)
The fallback check for missing birth years (>50 %) MUST be performed BEFORE applying the Minimum Listen Threshold filter (FR‑009) to prevent empty datasets. If the fallback check is performed after filtering by listen count, the dataset may be reduced to a size where the missing birth year proportion artificially exceeds the threshold, causing a false fallback trigger or an empty result set.

### EC-002: Zero Variance Tracks (See US-003)
Tracks with high exposure but zero memory cues (no matches) must be filtered out prior to modeling to avoid singularities in the design matrix.

### EC-003: Multicollinearity (See US-003)
If the Variance Inflation Factor (VIF) for `adolescent_exposure_ratio` or `popularity` indicates substantial multicollinearity (VIF > 5, see source 2605.22529), a warning must be logged, and the results should be interpreted with caution.

## 6. Data Sources

- **Million Song Dataset (MSD)**: Provides track metadata including release year and popularity. We use the release year to approximate adolescent exposure (see FR‑001). No per‑user listening timestamps are required.
- **Autobiographical Memory Test (AMT)**: For free‑text cues and memory ratings (vividness/valence).

## 7. Output Artifacts

- `data/processed/ingested_cohort.parquet`: Cohort data with exposure scores.  
- `data/processed/user_track_pairs.parquet`: Aggregated data at the User‑Track Pair level.  
- `data/final/regression_summary.csv`: Model coefficients and statistics (conforms to `contracts/output.schema.yaml`).  
- `data/final/sensitivity_analysis.csv`: Results across different matching thresholds with Bonferroni‑adjusted p‑values.  
- `data/final/permutation_results.csv`: Null distribution summary and two‑sided p‑value from the block‑permutation test.  
- `data/final/plots/`: Diagnostic plots (residuals, QQ plots).
