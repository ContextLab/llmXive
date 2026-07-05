# Feature Specification: Assessing the Impact of Sample Size on Meta-Analytic Reliability

**Feature Branch**: `001-meta-analytic-sample-size`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Assessing the Impact of Sample Size on the Reliability of Meta-Analytic Effect Sizes"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Subsampling Pipeline (Priority: P1)

The system MUST acquire a corpus of at least 50 real-world meta-analyses from public repositories and generate up to 100 bootstrap subsamples ranging from 3 studies up to the full study count for each meta-analysis, reducing the subsample count if necessary to meet computational time limits.

**Why this priority**: This is the foundational data layer. Without a robust, representative dataset and the ability to systematically subsample it, no stability analysis or coverage calculation can occur. It delivers the raw material for all subsequent metrics.

**Independent Test**: The pipeline can be tested by running a script that downloads a fixed set of meta-analyses., generates up to 100 subsamples per meta-analysis at specific study counts (e.g., k=3, 5, 10), and outputs a CSV of subsampled effect sizes and standard errors without performing any statistical modeling.

**Acceptance Scenarios**:

1. **Given** a list of 50 meta-analysis identifiers from Cochrane/Campbell, **When** the download script executes, **Then** the system retrieves effect sizes and standard errors for all component studies, handling missing data by excluding that specific study from the current meta-analysis pool while logging the exclusion.
2. **Given** a meta-analysis with N component studies, **When** the subsampling procedure runs, **Then** the system generates up to 100 distinct bootstrap samples for each study count k ∈ {3, ..., N}, ensuring no sample exceeds the original N. If computational constraints are detected, the system reduces the number of subsamples per k to maintain the runtime limit.
3. **Given** a downloaded dataset exceeding 50 meta-analyses, **When** memory constraints are simulated (e.g., a constrained limit), **Then** the system processes data in chunks to prevent out-of-memory errors, retaining only necessary columns (effect size, SE, study ID).

---

### User Story 2 - Stability and Coverage Metric Computation (Priority: P2)

The system MUST compute pooled effect sizes using fixed and random effects models for every subsample, applying a robust estimator (REML) for small sample sizes (k < 10), then derive stability metrics (standard deviation of estimates) and confidence interval coverage rates against the full-sample estimate (treated as the reference value).

**Why this priority**: This transforms raw subsampled data into the core research metrics. It directly addresses the research question regarding "stability" and "confidence interval coverage."

**Independent Test**: The computation module can be tested by feeding it a pre-generated set of subsamples for a single meta-analysis and verifying that it outputs a table of pooled effects, their standard deviations, and a binary flag for whether the 95% CI of each subsample contains the full-sample estimate.

**Acceptance Scenarios**:

1. **Given** a set of 100 subsamples for a specific study count k, **When** the fixed-effects model is applied, **Then** the system calculates the pooled effect size and its standard error for each subsample, storing the results.
2. **Given** the same 100 subsamples, **When** the random-effects model is applied, **Then** the system calculates the pooled effect size and its standard error for each subsample, using the DerSimonian-Laird method if k ≥ 10, and the Restricted Maximum Likelihood (REML) method if k < 10.
3. **Given** the full-sample estimate and the 100 subsample estimates, **When** the coverage analysis runs, **Then** the system calculates the proportion of subsamples whose confidence interval includes the full-sample estimate, reporting this as the coverage rate for count k.

---

### User Story 3 - Threshold Detection and Visualization (Priority: P3)

The system MUST fit a Generalized Additive Model (GAM) to the stability metrics to identify the study count threshold where stability improvements diminish (defined as a derivative drop below 0.05 with p < 0.05 vs linear), then generate diagnostic plots. If GAM fails, the system MUST use segmented regression as a fallback.

**Why this priority**: This delivers the final research insight (the "threshold") and the visual evidence required for interpretation. It synthesizes the metrics from Story 2 into a actionable conclusion.

**Independent Test**: The analysis module can be tested by providing it with a CSV of study counts vs. stability/coverage metrics and verifying that it outputs a changepoint estimate and a set of PNG plots showing the stability curves with confidence bands.

**Acceptance Scenarios**:

1. **Given** the aggregated stability metrics across all meta-analyses, **When** the GAM fitting process runs, **Then** the system identifies an inflection point (changepoint) where the rate of stability improvement drops below a negligible threshold and the model significantly outperforms a linear fit (p < 0.05), marking this as the "diminishing returns" point.
2. **Given** the coverage rates by study count, **When** the stabilization analysis runs, **Then** the system identifies the minimum study count k where the coverage rate remains within ±2% of the nominal 95% target for all k' > k.
3. **Given** the computed metrics, **When** the visualization script executes, **Then** the system generates a stability curve plot with confidence bands and a coverage plot, saving them to the output directory.

### Edge Cases

- What happens when a meta-analysis has fewer than 3 component studies? (System must skip or flag as insufficient for subsampling).
- How does the system handle meta-analyses with zero-variance studies (SE = 0)? (System must apply a small epsilon or exclude to prevent division by zero in inverse-variance weighting).
- How does the system behave if the random-effects variance estimate is zero or negative? (System must clamp variance to zero and log a warning).
- What if the full-sample estimate is an outlier compared to the subsamples? (System must calculate bias relative to the median of subsamples if the mean is skewed, or flag the meta-analysis).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse at least 50 meta-analyses from public repositories (Cochrane/Campbell) containing effect sizes and standard errors (See US-1).
- **FR-002**: System MUST generate up to 100 bootstrap subsamples for each study count k ranging from 3 to N (total studies) for every meta-analysis, reducing the count if computational limits are exceeded (See US-1).
- **FR-003**: System MUST compute pooled effect sizes using both fixed-effects and random-effects models for every generated subsample; for random-effects, use DerSimonian-Laird if k ≥ 10, and REML if k < 10 (See US-2).
- **FR-004**: System MUST calculate the standard deviation of pooled effects across multiple subsamples for each study count k to quantify stability (See US-2).
- **FR-005**: System MUST calculate the confidence interval coverage rate for each study count k by determining the proportion of subsample CIs containing the full-sample estimate (treated as the reference value) (See US-2).
- **FR-006**: System MUST fit a Generalized Additive Model (GAM) to the stability metrics to detect inflection points; if GAM fails, use segmented regression with a minimum of 2 segments. The threshold is defined as the point where the derivative drops below 0.05 and the model fit is significantly better than linear (p < 0.05) (See US-3).
- **FR-007**: System MUST identify the minimum study count where CI coverage stabilizes within ±2% of the nominal 95% level (See US-3).
- **FR-008**: System MUST generate diagnostic plots including stability curves with confidence bands and coverage plots by study count (See US-3).
- **FR-009**: System MUST perform a sensitivity analysis on the reference value (full-sample estimate) by perturbing it by its standard error to verify the robustness of the coverage metric (See US-2).

### Key Entities

- **MetaAnalysis**: Represents a single meta-analysis study, containing a list of component studies, total study count (N), and the full-sample pooled estimate.
- **Subsample**: A specific bootstrap sample of a MetaAnalysis at a specific study count k, containing a subset of effect sizes and standard errors.
- **StabilityMetric**: A record linking a MetaAnalysis ID, study count k, model type (fixed/random), standard deviation of pooled effects, and coverage rate.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of meta-analyses successfully processed and subsampled is measured against the target of ≥50 valid meta-analyses (See US-1).
- **SC-002**: The standard deviation of pooled effects across subsamples is measured against the theoretical expectation of decreasing variance as k increases, with the inflection point identified (See US-2, FR-006).
- **SC-003**: The confidence interval coverage rate is measured against the nominal [deferred] target, specifically identifying the study count k where coverage stabilizes within ±2% (See US-2, FR-007).
- **SC-004**: The computational runtime for the full bootstrap analysis (multiple meta-analyses × up to 100 subsamples × varying k) is measured against the GitHub Actions free-tier limit (See US-2, FR-008).
- **SC-005**: The number of detected inflection points (diminishing returns) is measured against the distribution of study counts, confirming a non-linear relationship (See US-3, FR-006).
- **SC-006**: The robustness of the coverage metric is measured by the variation in results when the reference value is perturbed by its standard error (See FR-009).

## Assumptions

- The Cochrane Library and Campbell Collaboration repositories provide machine-readable data (e.g., CSV, JSON, or parseable HTML) for at least 50 meta-analyses with ≥10 component studies each.
- The DerSimonian-Laird random-effects method is sufficient for k ≥ 10; for k < 10, the REML method is used to ensure stability.
- The "full-sample estimate" is treated as the reference value for coverage calculations, acknowledging it is an estimate with uncertainty, not the absolute ground truth.
- The tolerance for CI coverage stabilization (±2% of [deferred]) is a community-standard default for this type of simulation study.
- The dataset fits within the available RAM limit of the free-tier runner when processed in chunks; no single meta-analysis will require loading the entire corpus into memory simultaneously.
- The Generalized Additive Model (GAM) implementation in Python (e.g., `pygam` or `statsmodels`) is computationally tractable on 2 CPU cores for the expected dataset size; if not, the system falls back to segmented regression.
- The analysis assumes observational data; findings will be framed as associational regarding stability, not causal regarding the "true" effect size.
- The study count threshold for diminishing returns is expected to fall within a low-to-moderate range based on prior literature, but the analysis will empirically determine the exact point.