# Feature Specification: The Influence of Simulated Social Status on Risk-Taking Behavior

**Feature Branch**: `001-simulated-status-risk`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does observing higher-status agents engaging in risky behavior increase an individual's subsequent risk-taking, and does observing lower-status agents engaging in risky behavior decrease it?"

## User Scenarios & Testing

### User Story 1 - Data Synthesis and Preprocessing (Priority: P1)

The system must either simulate a synthetic dataset based on meta-analytic effect sizes from social status and risk-taking literature OR aggregate data from separate randomized trials (meta-analysis) to prepare for analysis.

**Why this priority**: Finding a single public dataset with a fully crossed factorial design (status level × observed behavior) is infeasible (scientific soundness concern). Simulating data based on established effect sizes or meta-analyzing separate studies provides a rigorous basis for testing the causal hypothesis. This is the foundational step for the entire research pipeline.

**Independent Test**: The system can be tested by verifying that the output CSV contains the required columns (`status_level`, `observed_behavior`, `risk_taking_score`, `participant_id`), that the data structure (between vs. within subjects) is correctly tagged, and that missing values are handled according to defined rules, without needing to run the regression model.

**Acceptance Scenarios**:

1. **Given** a valid simulation seed or a list of valid study IDs from a meta-analysis registry, **When** the ingestion script executes, **Then** the system produces a cleaned CSV with at least [deferred] rows (based on power analysis) and no duplicate `participant_id` entries.
2. **Given** a dataset where a required column (e.g., `risk_taking_score`) is missing or named differently, **When** the ingestion script executes, **Then** the system attempts to map the column based on common aliases; if mapping fails, it logs an error and halts, preventing downstream analysis on invalid data.
3. **Given** a dataset with >10% missing values in the outcome variable, **When** the preprocessing step runs, **Then** the system applies the defined imputation strategy (or exclusion rule) and reports the final N used for analysis.

---

### User Story 2 - Adaptive Mixed-Effects Regression Analysis (Priority: P1)

The system must fit a mixed-effects regression model (logistic or linear) to test the interaction between observed agent status and observed behavior on participant risk-taking, adapting to the data structure (between-subjects vs. within-subjects).

**Why this priority**: This directly answers the primary research question. The model must account for the specific data structure (repeated measures or independent groups) and test the specific interaction term hypothesized in the literature gap.

**Independent Test**: The model can be tested by running it on a synthetic dataset with a known interaction effect and verifying that the coefficient for the interaction term is statistically significant (p < 0.05) and matches the expected direction.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with sufficient sample size (N ≥ [deferred]), **When** the regression script executes, **Then** the system detects the data structure (between/within), selects the appropriate random effects term, and outputs a model summary including fixed effects coefficients, standard errors, and p-values for the `status_level * observed_behavior` interaction term.
2. **Given** a dataset where the interaction term is not significant (p ≥ 0.05), **When** the analysis completes, **Then** the system correctly flags the null result and generates the required diagnostic plots without raising a "model failed" error.
3. **Given** a dataset with collinear predictors, **When** the model fitting begins, **Then** the system calculates Variance Inflation Factors (VIF) and reports them, ensuring they do not exceed the threshold of 5.0.

---

### User Story 3 - Sensitivity Analysis and Reporting (Priority: P2)

The system must conduct sensitivity analyses on decision thresholds and outliers, and generate reproducible reports including effect size plots and model diagnostics.

**Why this priority**: To ensure methodological robustness, the findings must be validated against changes in parameters (e.g., outlier definitions) and presented with effect sizes and confidence intervals, not just p-values, to address the literature gap regarding practical significance.

**Independent Test**: The system can be tested by manually altering the outlier threshold (e.g., from 3 SD to 2 SD) in the config and verifying that the report explicitly lists the change in the headline effect size and p-value.

**Acceptance Scenarios**:

1. **Given** the fitted model, **When** the sensitivity analysis runs, **Then** the system sweeps the outlier exclusion threshold (defined as absolute deviation from *cell mean*) over {2.5 SD, 3.0 SD, 3.5 SD} and outputs a table showing how the interaction coefficient and p-value vary across these thresholds.
2. **Given** a significant interaction (p < 0.05), **When** the post-hoc analysis runs, **Then** the system performs pairwise comparisons with Bonferroni correction and reports the adjusted p-values.
3. **Given** the final results, **When** the report generation script executes, **Then** it produces a PDF/HTML summary containing a forest plot of condition means with 95% Confidence Intervals and a table of all model coefficients.

### Edge Cases

- What happens when the generated/synthetic dataset contains no variance in the `status_level` variable (e.g., all entries are "high")? The system must detect this and halt with a clear error message.
- How does the system handle a dataset where the `risk_taking` measure is continuous rather than binary? The system must detect the data type and switch the regression family from `binomial` to `gaussian` (linear mixed model) automatically, or flag for manual review if the model specification is rigid.
- What happens if the free-tier runner runs out of memory during the bootstrap resampling for confidence intervals? The system must fallback to asymptotic standard errors and log a warning.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST either (a) simulate a synthetic dataset based on effect sizes from meta-analyses of status/risk studies, OR (b) aggregate data from separate randomized trials via meta-analysis. It MUST NOT rely on finding a single pre-existing public dataset with a fully crossed factorial design (See US-1).
- **FR-002**: The system MUST preprocess the data to map `status_level` and `observed_behavior` variables to categorical factors with exactly two levels each (high/low, risky/conservative). If the input data has more levels, the system MUST apply a binning strategy (e.g., High vs. Low/Medium) OR flag the ambiguity for manual review (See US-1).
- **FR-003**: The system MUST fit a mixed-effects regression model with the formula `risk_taking ~ status_level * observed_behavior + (1|participant_id)` IF the data structure is within-subjects (repeated measures). If the data structure is between-subjects, the system MUST omit the random effect term to avoid singular fit. The system MUST automatically detect the outcome variable type (binary vs. continuous) and select the `binomial` or `gaussian` family accordingly (See US-2).
- **FR-004**: The system MUST calculate and report the Variance Inflation Factor (VIF) for all fixed effect predictors to detect multicollinearity, flagging any VIF > 5.0 (See US-2).
- **FR-005**: The system MUST perform a sensitivity analysis by sweeping the outlier exclusion threshold (defined as absolute deviation from the *cell mean* within each of the 4 experimental conditions) over the set {2.5, 3.0, 3.5} standard deviations and report the resulting change in the interaction effect size (See US-3).
- **FR-006**: The system MUST apply Bonferroni correction to ALL post-hoc pairwise comparisons to control the family-wise error rate, regardless of whether the primary interaction term is significant (See US-3).
- **FR-007**: The system MUST generate a forest plot visualizing the mean risk-taking scores for all four condition combinations (High/Risky, High/Conservative, Low/Risky, Low/Conservative) with 95% Confidence Intervals (See US-3).

### Key Entities

- **Participant**: An individual unit of observation with a unique `participant_id`, associated with a specific experimental condition and a risk-taking score.
- **Condition**: A combination of `status_level` (High/Low) and `observed_behavior` (Risky/Conservative) defining the experimental group.
- **ModelResult**: The output object containing fixed effects coefficients, standard errors, p-values, and random effect variances from the mixed-effects regression.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The interaction term `status_level * observed_behavior` in the mixed-effects model is measured against the null hypothesis of zero effect (p-value < 0.05) (See US-2).
- **SC-002**: The stability of the interaction effect is measured against the sensitivity analysis results, specifically checking if the p-value remains < 0.05 across the outlier threshold sweep {2.5, 3.0, 3.5 SD} (See US-3).
- **SC-003**: The precision of the effect estimate is measured by the width of the 95% Confidence Interval for the interaction coefficient, reported for all model runs (See US-2).
- **SC-004**: The validity of the risk-taking measure is measured against the documentation of the source dataset (for meta-analysis) or the parameterization of the simulation (See US-1).

## Assumptions

- **Assumption about data availability**: A single public dataset with a fully crossed factorial design (status × behavior) is highly improbable to find. Therefore, the project assumes it is scientifically valid to either (a) simulate data based on meta-analytic parameters to test the causal mechanism, or (b) meta-analyze separate studies. This approach is justified as essential to answering the causal research question given data constraints.
- **Assumption about compute resources**: The entire analysis (data loading, model fitting, sensitivity sweeps) can complete within 6 hours on a GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) without GPU acceleration.
- **Assumption about measurement validity**: The risk-taking scores in the identified datasets (or simulated data) are derived from validated psychological instruments (e.g., Balloon Analog Risk Task) rather than ad-hoc self-reports, ensuring construct validity.
- **Assumption about causal inference**: The simulation/meta-analysis approach is designed to infer causality by controlling for confounders in the synthetic generation or by selecting only randomized trials for the meta-analysis. The findings will be framed as causal evidence derived from these rigorous methods.
- **Assumption about collinearity**: The predictors `status_level` and `observed_behavior` are orthogonal in the experimental design of the source datasets or simulation parameters, minimizing inherent multicollinearity before model fitting.
- **Assumption about threshold justification**: The outlier threshold of 3.0 SD is adopted as the community standard for initial exclusion, with the sensitivity analysis (FR-005) serving as the validation step for this choice.