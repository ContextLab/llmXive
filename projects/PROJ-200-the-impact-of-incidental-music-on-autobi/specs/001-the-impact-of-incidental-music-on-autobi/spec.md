# Feature Specification: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Feature Branch**: `001-impact-of-incidental-music`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Research question validation: Does exposure to music during adolescence produce uniquely vivid and emotionally salient autobiographical memories compared to music exposure during other developmental periods?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Cohort Exposure Scoring (Priority: P1)

The system must ingest the Million Song Dataset (MSD) listening logs and the Autobiographical Memory Test (AMT) dataset, then compute a normalized "Adolescent Exposure Score" for every track based on listening events occurring between ages 12-18 for users with known birth years.

**Why this priority**: This is the foundational data engineering step. Without accurate exposure scores derived from the correct developmental window, no statistical analysis of the "adolescent advantage" hypothesis can occur. It is the primary input for all downstream modeling.

**Independent Test**: Can be fully tested by running the ingestion pipeline on a small, synthetic subset of MSD and AMT data and verifying that the output CSV contains a `adolescent_exposure_score` column where values are strictly between 0 and 1, and that tracks with no adolescent listens have a score of 0.

**Acceptance Scenarios**:

1. **Given** a user record in MSD with a birth year and listening logs, **When** the system calculates the adolescent window (birth year + 12 to birth year + 18), **Then** only listening events within that window contribute to the track's numerator for the score.
2. **Given** a track with 100 total listens but 0 listens during any user's adolescent window, **When** the score is computed, **Then** the `adolescent_exposure_score` is exactly 0.00.
3. **Given** a user record missing the `birth_year` field, **When** the pipeline processes the record, **Then** the record is excluded from the primary cohort calculation to prevent data leakage.

### User Story 2 - Cue Matching and Memory Attribute Aggregation (Priority: P2)

The system must parse the free-text memory cues from the AMT dataset, normalize the text (lowercase, remove punctuation), and match them to MSD track titles using fuzzy string matching (Levenshtein distance ≤ 4). It then aggregates the associated vividness and valence ratings per matched track.

**Why this priority**: This links the behavioral outcome (memory retrieval) to the specific stimuli (tracks). It transforms raw text responses into the quantitative dependent variables required for the regression model.

**Independent Test**: Can be fully tested by providing a small set of AMT text cues with known MSD track titles and verifying that the matching engine correctly identifies the tracks and aggregates the correct mean vividness/valence values.

**Acceptance Scenarios**:

1. **Given** an AMT cue text "Imagine Dragons - Radioactive", **When** the system normalizes the text (lowercase, remove punctuation) and runs the fuzzy matcher against the MSD title list, **Then** the track "Radioactive" by "Imagine Dragons" is matched (Levenshtein distance ≤ 4).
2. **Given** a matched track that appears in the AMT dataset 5 times with vividness scores [80, 90, 75, 85, 95], **When** aggregation occurs, **Then** the resulting `mean_vividness` is 85.0.
3. **Given** an AMT cue text that does not match any MSD track within the Levenshtein threshold, **When** the pipeline runs, **Then** that cue is excluded from the final analysis dataset, and a count of unmatched cues is logged.

### User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

The system must fit a linear mixed-effects model to test the significance of the `adolescent_exposure_score` on `vividness` and `valence`, controlling for `overall_popularity`, and perform a sensitivity analysis on the matching threshold. The unit of analysis is the individual memory instance.

**Why this priority**: This directly answers the research question. It validates the "adolescent advantage" hypothesis and ensures the results are robust to the specific fuzzy-matching parameters used.

**Independent Test**: Can be fully tested by running the analysis script on the aggregated dataset and verifying that the output includes a regression summary table with a p-value for the adolescent exposure coefficient, and a sensitivity table showing results for threshold variations.

**Acceptance Scenarios**:

1. **Given** the memory instance dataset (where each row is a single memory), **When** the mixed-effects model `vividness ~ adolescent_exposure + overall_popularity + (1|User)` is fitted, **Then** the output includes the coefficient, standard error, and p-value for `adolescent_exposure`.
2. **Given** the primary analysis results (threshold 4), **When** the sensitivity analysis runs, **Then** the system reports regression coefficients for Levenshtein thresholds of 2 and 6 to demonstrate stability.
3. **Given** a null result (p ≥ 0.05), **When** the permutation test runs (shuffling memory outcomes relative to track labels [deferred] times), **Then** the observed statistic is compared against the null distribution to confirm the result is not due to chance structure in the data.

### Edge Cases

- **Missing Birth Years**: If >50% of MSD users lack birth year metadata, the primary cohort definition becomes statistically invalid. The system MUST trigger a fallback to a "global exposure" metric (adolescent listens / total listens from ALL users) and log a warning.
- **Ambiguous Track Titles**: If multiple tracks share the same title and artist (e.g., different versions/remixes) and the AMT cue is ambiguous, the fuzzy matcher may map to the wrong track; the system must log these collisions for manual review if the match count is low.
- **Zero-Variance Tracks**: If a track has a high exposure score but zero memory cues in AMT, it cannot contribute to the regression for vividness/valence; these rows must be filtered out prior to modeling.
- **Correlated Predictors**: If `overall_popularity` and `adolescent_exposure` are highly correlated (VIF > 5), the model may suffer from multicollinearity; the system must detect this and report the Variance Inflation Factor.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the `adolescent_exposure_score` for each track by dividing the count of listens from users aged 12-18 (with valid `birth_year`) by the total listens for that track from users with valid `birth_year` (See US-1).
- **FR-002**: System MUST filter MSD listening logs to include only records where the user's `birth_year` is present and valid for the primary cohort calculation (See US-1).
- **FR-003**: System MUST parse the AMT free-text cues, normalize them (lowercase, remove non-alphanumeric characters), and perform fuzzy string matching against MSD track titles with a maximum Levenshtein distance of 4 (See US-2).
- **FR-004**: System MUST aggregate AMT vividness and valence ratings per matched track to produce mean values (See US-2).
- **FR-005**: System MUST fit a linear mixed-effects model with `adolescent_exposure_score` as the primary predictor and `overall_popularity_score` as a covariate, using `User` as the random intercept `(1|User)`, where the unit of analysis is the individual memory instance (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis by re-running the matching and modeling pipeline with Levenshtein thresholds of 2 and 6 (See US-3).
- **FR-007**: System MUST output a permutation test result where memory outcomes (vividness/valence) are shuffled relative to track labels [deferred] times to establish a null distribution (See US-3).
- **FR-008**: System MUST switch to a "global exposure" fallback metric (adolescent listens / total listens from ALL users) if >50% of MSD users lack `birth_year` metadata, and log a warning (See Edge Cases).

### Key Entities

- **Track**: Represents a unique music track in the MSD, identified by `track_id`, `title`, and `artist`.
- **CohortListen**: Represents a listening event associated with a user's adolescent window (ages 12-18).
- **MemoryCue**: Represents a specific autobiographical memory instance from the AMT dataset, containing the cue text, vividness score, valence score, and `user_id`.
- **AggregatedMetric**: A derived entity per track containing `adolescent_exposure_score`, `overall_popularity_score`, `mean_vividness`, and `mean_valence`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The statistical significance of the `adolescent_exposure_score` coefficient is measured against the null hypothesis (p < 0.05) to determine if the adolescent advantage exists (See FR-005, US-3).
- **SC-002**: The stability of the primary result is measured against the sensitivity analysis by comparing the sign and magnitude of the coefficient across a range of Levenshtein thresholds. (See FR-006, US-3).
- **SC-003**: The robustness of the finding against chance is measured against the permutation test distribution (shuffled [deferred] times) to ensure the observed effect exceeds a standard significance threshold of the null (See FR-007, US-3).
- **SC-004**: The data quality is measured against the requirement that ≥ 80% of AMT cues must be successfully matched to MSD tracks to ensure sufficient statistical power (See FR-003, US-2).
- **SC-005**: The computational feasibility is measured against the constraint that the entire pipeline (ingestion, matching, modeling) completes within 6 hours on a GitHub Actions ubuntu-latest runner with ≤ 7 GB RAM (See FR-001, US-1).

## Assumptions

- The **Million Song Dataset** subset available via the official mirror contains the `birth_year` metadata field required to define the adolescent cohort (12-18 years).
- The **Autobiographical Memory Test** dataset includes free-text cues that are sufficiently similar to official track titles to allow matching with a Levenshtein distance of ≤ 4 after normalization.
- The relationship between adolescent exposure and memory vividness is **associational**, not causal, as the data is observational (no random assignment of music exposure).
- The **Million Song Dataset** listening logs are representative of the general population's music consumption during the relevant historical periods.
- The **OpenPsych** AMT dataset is licensed for reuse in this research context without additional fees.
- The `statsmodels` library in Python is sufficient for fitting the linear mixed-effects models without requiring the `lme4` R package or GPU acceleration.
- A large-scale subset of the MSD is representative enough of the full dataset to detect the hypothesized effect size.