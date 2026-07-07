# Feature Specification: The Impact of Perceived Social Support on Resilience to Online Harassment

**Feature Branch**: `001-social-support-resilience`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Research on whether higher perceived social support buffers anxiety, depression, and PTSD symptoms in victims of online harassment, using GSS and Cyberbullying Survey data with propensity-score matching and interaction analysis."

## User Scenarios & Testing

### User Story 1 - Data Harmonization and Merging (Priority: P1)

The system MUST ingest two independent datasets (GSS 2022 and Cyberbullying Survey 2021), harmonize variable names, handle missing values, and generate a merged pseudo-panel dataset via propensity-score matching on demographic covariates.

**Why this priority**: Without a valid, merged dataset where harassment exposure and support levels are aligned for the same (matched) respondents, no statistical analysis can proceed. This is the foundational step for the entire research question.

**Independent Test**: The system can be tested by running the data ingestion and matching pipeline alone and verifying that the output CSV contains matched pairs with no `NaN` values in critical predictor/outcome columns and that the distribution of covariates (age, gender, education) is balanced between matched groups (p > 0.05 in t-tests).

**Acceptance Scenarios**:

1. **Given** raw GSS and Cyberbullying Survey CSV files exist, **When** the ingestion script is executed, **Then** a merged dataset is produced with exactly one row per matched pair and all demographic covariates filled.
2. **Given** the merged dataset, **When** a balance check is run on covariates, **Then** the standardized mean difference for every covariate is ≤ 0.1.
3. **Given** missing values in non-critical fields, **When** the script processes them, **Then** missing values are imputed or rows are dropped according to the defined rule (e.g., listwise deletion) without crashing.

### User Story 2 - Interaction Analysis and Hypothesis Testing (Priority: P2)

The system MUST fit hierarchical linear models for three outcomes (Depression, Anxiety, PTSD) testing the interaction between Social Support and Harassment Exposure, and output regression coefficients with 95% bias-corrected bootstrapped confidence intervals.

**Why this priority**: This directly answers the core research question: "Do individuals with higher support show lower distress?" The interaction term is the specific metric of the buffering effect.

**Independent Test**: The system can be tested by running the regression module on the merged dataset and verifying that the output table contains the interaction coefficient, standard error, p-value, and bootstrapped confidence intervals for all three models, and that the script completes within the 6-hour limit.

**Acceptance Scenarios**:

1. **Given** the merged dataset, **When** the regression model is fit for Depression, **Then** the output includes the interaction term `SocialSupport:HarassmentExposure` with a 95% bootstrap CI.
2. **Given** the model results, **When** the significance test is performed, **Then** the p-value for the interaction term is calculated using a Wald test.
3. **Given** the analysis completes, **When** the results are saved, **Then** a CSV file is generated containing coefficients, p-values, and CIs for all three mental health outcomes.

### User Story 3 - Sensitivity Analysis and Robustness Checks (Priority: P3)

The system MUST execute sensitivity analyses by varying the harassment exposure definition (binary vs. continuous severity) and stratifying by platform type, reporting how the interaction effect size changes across these variations.

**Why this priority**: This addresses the robustness of the findings and the "threshold justification" requirement. It ensures the results are not artifacts of a specific operationalization of "harassment" or "platform."

**Independent Test**: The system can be tested by running the sensitivity analysis script which re-runs the models with modified inputs and produces a comparison table showing the variation in the interaction coefficient across the defined scenarios.

**Acceptance Scenarios**:

1. **Given** the baseline model results, **When** the sensitivity analysis runs with continuous severity instead of binary exposure, **Then** the new interaction coefficient is calculated and compared to the baseline.
2. **Given** the baseline model, **When** the analysis is stratified by platform (e.g., Twitter vs. Reddit), **Then** separate interaction coefficients are output for each platform group.
3. **Given** all sensitivity runs, **When** the summary report is generated, **Then** it includes a table showing the range of interaction coefficients across all tested scenarios.

### Edge Cases

- What happens when the propensity score matching fails to find sufficient matches for a specific demographic subgroup (e.g., < 10 matches)? The system must flag this in the output log and exclude that subgroup from the final analysis rather than crashing or imputing invalid data.
- How does the system handle a dataset where the "Harassment Severity" variable has a high proportion of zeros (no harassment)? The system must verify that the interaction term is estimable (i.e., sufficient variance in the exposure variable) and report a warning if the effective sample size for the interaction is too low (< 30 observations).
- How does the system handle non-convergence of the hierarchical linear model? The system must catch the convergence error, log the specific model parameters that failed, and attempt a fallback with a simpler OLS model, reporting the fallback status in the results.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and harmonize variables from the GSS 2022 and Cyberbullying Survey 2021 datasets, mapping raw survey items to standardized constructs (Social Support, Harassment Severity, Mental Health Outcomes) (See US-1).
- **FR-002**: System MUST perform propensity-score matching on demographic covariates (age, gender, education, income) to create a balanced pseudo-panel dataset linking the two independent surveys (See US-1).
- **FR-003**: System MUST fit three separate hierarchical linear regression models for Depression (CES-D), Anxiety (GAD-7), and PTSD symptoms, each including an interaction term between Social Support and Harassment Exposure (See US-2).
- **FR-004**: System MUST compute 95% bias-corrected bootstrapped confidence intervals (1,000 resamples) for all interaction coefficients using CPU-tractable methods (See US-2).
- **FR-005**: System MUST execute sensitivity analyses by re-running models with (a) continuous harassment severity instead of binary exposure, and (b) stratification by platform type, reporting coefficient shifts (See US-3).
- **FR-006**: System MUST validate that all predictor variables used in the regression are present in the source datasets; if a required variable is missing, the system MUST output a `[NEEDS CLARIFICATION]` marker for that specific variable (See US-2).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to the family of three hypothesis tests (one per outcome) to control the family-wise error rate (See US-2).

### Key Entities

- **Matched Respondent**: A synthetic record representing a pair of individuals (one from GSS, one from Cyberbullying Survey) matched on demographics, containing derived scores for support, exposure, and mental health.
- **Interaction Effect**: The statistical coefficient representing the moderation of harassment impact by social support, stored with its standard error and confidence interval.
- **Platform Type**: A categorical variable derived from the survey data (e.g., Twitter, Reddit, Mastodon) used for stratification in sensitivity analysis.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The balance of covariates in the matched dataset is measured against the standardized mean difference threshold of ≤ 0.1 (See FR-002, US-1).
- **SC-002**: The statistical significance of the buffering effect is measured by whether the 95% bias-corrected bootstrapped confidence interval for the interaction term excludes zero (See FR-004, US-2).
- **SC-003**: The robustness of the findings is measured by the magnitude of change in the interaction coefficient across the sensitivity analysis scenarios (continuous vs. binary exposure) (See FR-005, US-3).
- **SC-004**: The control of Type I error is measured by the application of a multiple-comparison correction method to the set of three outcome tests (See FR-007, US-2).
- **SC-005**: The computational feasibility is measured by the total execution time of the analysis pipeline, which must complete within 6 hours on a 2-core CPU-only runner (See FR-004, US-2).
- **SC-006**: The validity of the measurement instruments is measured by the use of established, validated scales (CES-D, GAD-7, PCL-5) as defined in the source datasets (See FR-001, US-1).

## Assumptions

- **Assumption about data availability**: The 2022 GSS dataset contains valid items for the PCL-5 (PTSD) scale or a sufficiently proximal measure that can be constructed; if the PCL-5 items are missing, the analysis will proceed with CES-D and GAD-7 only, and the scope will be reduced to anxiety and depression.
- **Assumption about matching quality**: Propensity score matching on the available demographic variables (age, gender, education, income) will yield a sufficient number of matched pairs (N > 300) to provide adequate statistical power for detecting an interaction effect, given the effect sizes typical in social science literature.
- **Assumption about computational constraints**: The bootstrapping procedure (1,000 resamples) for three models will complete within the 6-hour GitHub Actions free-tier limit using standard Python `scipy`/`statsmodels` libraries on a 2-core CPU.
- **Assumption about platform classification**: The "Platform Type" variable in the Cyberbullying Survey is coded consistently enough to allow for meaningful stratification (e.g., distinct categories for Twitter, Reddit, etc.) rather than a single "Social Media" bucket.
- **Assumption about causality**: The analysis is observational; therefore, findings will be framed strictly as associational (buffering effect) rather than causal, acknowledging that unobserved confounders may exist despite propensity matching.
- **Assumption about threshold sensitivity**: A sensitivity analysis sweeping the harassment severity cutoff (if a binary threshold is used in alternative models) over a range of {0.01, 0.05, 0.1} will be sufficient to demonstrate robustness without requiring exhaustive grid searches.
