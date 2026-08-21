# Feature Specification: Detecting Statistical Power Drift in Replicated Studies

**Feature Branch**: `001-detect-power-drift`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Do reported statistical power estimates in published replication studies exhibit a systematic temporal decline, indicating a drift toward lower-powered replications over time?"

## User Scenarios & Testing

### User Story 1 - Core Power Drift Analysis (Priority: P1)

As a research methodologist, I want to compute post-hoc statistical power estimates for a dataset of replication studies and test for a temporal decline over calendar years *after adjusting for temporal trends in effect sizes and sample sizes*, so that I can determine if the replication enterprise is drifting toward underpowered studies independent of changes in the underlying data characteristics.

**Why this priority**: This is the primary research question. Without the ability to isolate the temporal trend in power from the trends in its constituent inputs (effect size, N), the analysis risks being tautological. This ensures the hypothesis tests for a genuine methodological drift rather than a mathematical artifact.

**Independent Test**: The system can be fully tested by running the power re-estimation and linear mixed-effects modeling scripts on a static subset of the OSF/Replication Project data, verifying that a slope coefficient and p-value are generated for the `year` predictor *in the residual model*.

**Acceptance Scenarios**:

1. **Given** a CSV file containing replication study metadata (year, effect size, sample size), **When** the analysis script is executed, **Then** a post-hoc power estimate is calculated for every row using α=0.05 two-tailed, and a linear mixed-effects model `power_est ~ year + effect_size + sample_size + (1|field)` is fitted to isolate the residual drift.
2. **Given** the fitted model, **When** the fixed effect of `year` is tested via likelihood-ratio test, **Then** the output includes the slope estimate, standard error, p-value, and a clear statement of whether the *residual* trend is statistically significant (p < 0.05).
3. **Given** the analysis results, **When** the user requests a visualization, **Then** a scatter plot of *residual* power vs. year with the fitted regression line and 95% confidence intervals is generated.

---

### User Story 2 - Robustness via Permutation & Sensitivity (Priority: P2)

As a skeptical peer reviewer, I want to see the power drift results validated against a non-parametric permutation test and a sensitivity analysis on the alpha threshold, so that I can trust the findings are not artifacts of model assumptions or arbitrary cutoff choices.

**Why this priority**: The methodology sketch explicitly requires guarding against model misspecification and justifying thresholds. This ensures the scientific validity of the drift claim.

**Independent Test**: The system can be tested by running the permutation test (sufficient iterations) and the sensitivity sweep on the same dataset, verifying that the p-value distribution from permutations and the trend stability across alpha thresholds are reported.

**Acceptance Scenarios**:

1. **Given** the original linear model results, **When** the permutation test is run (shuffling `year` labels [deferred] times), **Then** the empirical p-value is calculated and compared to the parametric p-value to confirm consistency.
2. **Given** a decision threshold (e.g., alpha = 0.05), **When** the sensitivity analysis sweeps the alpha value across a range of small magnitudes, **Then** the output reports how the significance of the drift slope changes across these values, confirming the result is robust or identifying the boundary of significance.
3. **Given** the sensitivity results, **When** the report is generated, **Then** it explicitly states whether the observed drift is driven by a specific alpha choice or holds across the tested range.

---

### User Story 3 - Cross-Field Aggregation & Drift Validation (Priority: P3)

As a domain expert, I want to combine evidence across heterogeneous fields using an adaptively weighted statistic and validate the drift using an input permutation framework, so that I can generalize findings beyond a single discipline.

**Why this priority**: This addresses the "heterogeneous effect-size metrics" and "validation" components of the methodology, adding depth to the primary finding but relying on the core analysis being complete first.

**Independent Test**: The system can be tested by executing the adaptively weighted statistic aggregation and the input permutation validation on the full dataset, verifying that a combined drift statistic is produced and compared to the mixed-model slope.

**Acceptance Scenarios**:

1. **Given** residual power drift estimates stratified by field, **When** the adaptively weighted statistic (inverse-variance weighting with heterogeneity adjustment) is applied, **Then** a single aggregated evidence metric is produced that accounts for field heterogeneity.
2. **Given** the time-series of residual power estimates, **When** the input permutation framework is applied (shuffling effect sizes and sample sizes while holding year constant), **Then** a null distribution of drift slopes is generated and the observed slope is compared against it to check for significance.
3. **Given** the results of both aggregation and permutation methods, **When** the final report is generated, **Then** it includes a section comparing the primary mixed-model slope with the aggregated drift estimate and the permutation-based p-value.

### Edge Cases

- **Missing Data**: What happens when a replication study lacks the sample size or effect size required for power calculation? (System must skip the row and log a warning, not crash).
- **Zero Variance**: What happens if a specific field has only one replication study in the dataset? (System must handle the `(1|field)` random effect gracefully, potentially collapsing that field or excluding it from the mixed model).
- **Extreme Outliers**: How does the system handle effect sizes or sample sizes that are statistical outliers (e.g., infinite or negative variance)? (System must cap or filter extreme values based on domain logic before modeling).
- **Permutation Convergence**: What if the permutation test fails to converge or runs out of memory on the free-tier runner? (System must implement a fallback to a smaller iteration count of [deferred] and flag the result as "approximate").

## Requirements

### Functional Requirements

- **FR-001**: System MUST calculate post-hoc statistical power for each replication study using reported effect size (Cohen's *d* or odds ratio), sample size, and α = 0.05 two-tailed, as defined by the 1999 power-of-association formulas (See US-1).
- **FR-002**: System MUST fit a linear mixed-effects model with `power_est` as the outcome, `year` as the fixed effect, `effect_size` and `sample_size` as covariates to control for input drift, and random intercepts for `field` and `original_study_id` (See US-1).
- **FR-003**: System MUST perform a likelihood-ratio test to determine the statistical significance of the `year` fixed effect, reporting the slope, SE, and p-value (See US-1).
- **FR-004**: System MUST execute a non-parametric permutation test with a sufficient number of permutations of the `year` variable to generate an empirical p-value for the drift slope, with a fallback to a minimum of 1,000 permutations if memory or time limits are exceeded (See US-2).
- **FR-005**: System MUST conduct a sensitivity analysis sweeping the alpha threshold across a range of statistically conventional significance levels, as established in prior methodological literature (e.g., Cohen, 1988). and report the resulting drift significance rates (See US-2).
- **FR-006**: System MUST apply an inverse-variance weighting with heterogeneity adjustment (DerSimonian-Laird) to combine residual power drift estimates across fields with heterogeneous effect-size metrics (See US-3).
- **FR-007**: System MUST compute a null distribution for the drift slope by permuting the input variables (effect size and sample size) [deferred] times while holding year constant, and compare the observed slope against this distribution (See US-3).
- **FR-008**: System MUST handle missing data (missing sample size or effect size) by excluding the specific record and logging a warning, without terminating the pipeline (See Edge Cases).
- **FR-009**: System MUST visualize the *residual* power vs. year trajectory with the fitted regression line and 95% confidence intervals (See US-1).
- **FR-010**: System MUST run entirely on a CPU-only environment (no GPU/CUDA) within a reasonable runtime limit on a standard CI runner (See Compute Feasibility).

### Key Entities

- **ReplicationStudy**: Represents a single replication event. Key attributes: `study_id`, `year`, `field`, `original_study_id`, `effect_size`, `sample_size`, `power_estimate`.
- **DriftModel**: Represents the statistical model output. Key attributes: `slope_year`, `se_slope`, `p_value_parametric`, `p_value_permutation`, `random_effects_variance`.
- **SensitivityResult**: Represents the outcome of threshold sweeps. Key attributes: `alpha_value`, `drift_significant`, `false_positive_rate`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The slope of *residual* power estimates over calendar year (adjusted for effect size and sample size) is measured against the null hypothesis of zero slope (See US-1).
- **SC-002**: The empirical p-value from the permutation test is measured against the parametric p-value to assess model robustness (See US-2).
- **SC-003**: The stability of the drift detection is measured against the alpha threshold sweep {0.01, 0.05, 0.1} to ensure the finding is not threshold-dependent (See US-2).
- **SC-004**: The aggregated evidence across fields is measured against the primary mixed-model slope to validate generalizability (See US-3).
- **SC-005**: The observed drift slope is measured against the null distribution generated by permuting input variables to confirm the drift is not an artifact of input distribution changes (See US-3).

## Assumptions

- **Dataset Availability**: The OSF replication project metadata and the OpenML Reproducibility Project dataset are accessible and contain the necessary columns (year, effect size, sample size) for the majority of studies. If specific variables (e.g., exact alpha level used in original studies) are missing, the analysis assumes α = 0.05 for all.
- **Compute Constraints**: The total dataset size (after download and filtering) will fit within a manageable amount of RAM., and the permutation test (a sufficient number of iterations) will complete within the CI job limit on a 2-core CPU runner.
- **Statistical Formulas**: The power calculation formulas from the 1999 paper are applicable to the effect size metrics (Cohen's *d*, odds ratio) found in the dataset without requiring complex conversion factors not provided in the source.
- **Observational Nature**: The study design is purely observational; therefore, the analysis assumes no causal claims can be made about *why* the drift occurs, only that a temporal association exists.
- **Independence of Random Effects**: The assumption is made that `field` and `original_study_id` random effects are sufficient to account for clustering, and that no additional hierarchical levels (e.g., specific lab) are required for the model to converge.
- **Threshold Justification**: The choice of alpha thresholds {0.01, 0.05, 0.1} for sensitivity analysis is based on standard community practices in statistical reporting; this specific set is sufficient to demonstrate robustness.