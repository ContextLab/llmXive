# Feature Specification: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Feature Branch**: `001-the-influence-of-algorithmic-recommendations`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "How does the content diversity of algorithmic recommendations predict subsequent learner course topic diversity, controlling for baseline interests?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Diversity Metric Calculation (Priority: P1)

The system must ingest public course enrollment datasets containing distinct columns for "recommended items" and "enrolled items," then compute a Shannon entropy-based "Recommendation Diversity Score" for each user session and a corresponding "Learner Diversity Score" for subsequent enrollments.

**Why this priority**: This is the foundational data engineering step. Without accurate, temporally distinct metrics for the predictor (recommendations) and outcome (enrollments), no statistical analysis can be performed. It delivers the primary dataset required for the research.

**Independent Test**: Can be fully tested by running the preprocessing script on a known sample dataset (e.g., a 100-row mock CSV) and verifying the output JSON contains calculated entropy scores for both recommendation and enrollment lists that match manual calculations within a tolerance of 0.001.

**Acceptance Scenarios**:

1. **Given** a CSV file with columns `user_id`, `session_id`, `recommended_categories`, and `enrolled_categories`, **When** the preprocessing script is executed, **Then** the output JSON must contain a `recommendation_diversity_score` and `learner_diversity_score` for each row, calculated as the Shannon entropy (using log base 2) of the category distribution.
2. **Given** a session where the `recommended_categories` list contains only one unique category (e.g., "Math"), **When** the diversity score is calculated, **Then** the score must be exactly 0.0.
3. **Given** a dataset where `enrolled_categories` is empty for a user, **When** the script processes the row, **Then** the `learner_diversity_score` must be recorded as `null` or excluded from the analysis dataframe, and a warning must be logged.

---

### User Story 2 - Baseline Control and Propensity Score Weighting (Priority: P2)

The system must derive a "Baseline_Interest_Vector" from pre-study enrollment history for each user and use Propensity Score Weighting (PSW) to adjust for the confounding effect of intrinsic preferences, then fit a weighted linear regression to isolate the effect of recommendations.

**Why this priority**: This addresses the core research hypothesis while mitigating the identification problem where recommendations are mechanistically linked to baseline interests. PSW creates a pseudo-population where the association between baseline interests and recommendations is balanced, allowing for a more valid estimation of the algorithmic influence.

**Independent Test**: Can be fully tested by executing the modeling script on the processed dataset and verifying that the output includes the estimated propensity scores, the distribution of weights, and the weighted regression coefficient for `Recommendation_Diversity` with a p-value.

**Acceptance Scenarios**:

1. **Given** the processed dataset with calculated diversity scores and baseline vectors, **When** the PSW model is fitted, **Then** the output must report the stabilized weights and the weighted regression estimate, standard error, and p-value for the `Recommendation_Diversity` predictor.
2. **Given** a dataset where the `Baseline_Interest_Vector` is highly correlated with `Recommendation_Diversity` (r > 0.7), **When** the weights are calculated, **Then** the system must report the effective sample size reduction and flag if extreme weights (> 10x median) are present.
3. **Given** a scenario where the propensity model fails to converge or produces unstable weights, **When** the script detects this, **Then** it must automatically fall back to a standard linear regression with robust standard errors and log the methodological change.

---

### User Story 3 - Robustness Verification and Sensitivity Analysis (Priority: P3)

The system must perform a residual permutation test to validate that the observed effect is not due to unmeasured confounders and conduct a sensitivity analysis on the semantic similarity threshold (used for merging categories) by sweeping the threshold (e.g., absolute difference ∈ {0.01, 0.05, 0.1}) to ensure result stability.

**Why this priority**: This ensures methodological soundness. The residual permutation test addresses the "observational vs. causal" framing by testing the null hypothesis on the residuals after controlling for known confounders. The sensitivity analysis justifies the robustness of the category merging step.

**Independent Test**: Can be fully tested by running the robustness suite on a subset of data and verifying that the residual permutation test p-value distribution is uniform under the null hypothesis and that the sensitivity analysis produces a table of effect sizes across the tested thresholds.

**Acceptance Scenarios**:

1. **Given** the fitted weighted regression results, **When** the residual permutation test is executed (shuffling residuals [deferred] times), **Then** the observed effect size must fall outside the 95% confidence interval of the permuted distribution if the null hypothesis is rejected.
2. **Given** a sensitivity analysis request with thresholds {0.01, 0.05, 0.1} for the semantic similarity metric, **When** the analysis runs, **Then** the output must be a table showing the `Recommendation_Diversity` coefficient and p-value for each threshold, demonstrating that the significance (p < 0.05) is stable across the sweep.
3. **Given** a scenario where the sensitivity analysis shows the p-value flips from significant to non-significant across the sweep (e.g., p=0.04 at 0.01 vs p=0.06 at 0.05), **When** the report is generated, **Then** a "Sensitivity Warning" must be appended to the results, explicitly stating the result is threshold-dependent.

### Edge Cases

- **What happens when** the recommendation log is missing for a user session? The system must exclude that row from the analysis and log a count of excluded sessions to ensure the sample size is reported accurately.
- **How does system handle** users with no prior enrollment history (no baseline)? The system must impute a neutral baseline vector (e.g., uniform distribution) or exclude the user, but must document this choice in the `## Assumptions` section and flag the imputation in the data dictionary.
- **What happens when** the dataset contains fewer than 30 unique users? The system must detect this and fall back to a fixed-effects model (GLS) with robust standard errors, logging the methodological change.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the Shannon entropy (log base 2) of the category distribution for both the `recommended_categories` list and the `enrolled_categories` list for every user session. (See US-1)
- **FR-002**: System MUST derive a `Baseline_Interest_Vector` for each user based on their enrollment history prior to the observation window. (See US-2)
- **FR-003**: System MUST fit a weighted linear regression model (using Propensity Score Weights) to estimate the fixed effect of `Recommendation_Diversity` on `Learner_Diversity`, unless N < 30. (See US-2)
- **FR-004**: System MUST execute a residual permutation test with at least 1,000 iterations to generate a null distribution for the observed effect size. (See US-3)
- **FR-005**: System MUST perform a sensitivity analysis sweeping the semantic similarity threshold over the set {0.01, 0.05, 0.1} and report the resulting coefficient stability. (See US-3)
- **FR-006**: System MUST frame all statistical conclusions as ASSOCIATIONAL, explicitly avoiding causal language (e.g., "causes," "leads to") in the final report unless randomization is present in the data source. (See US-2)
- **FR-007**: System MUST validate that the dataset source contains distinct columns for `recommended_categories` and `enrolled_categories` before processing; if missing, it must raise a `DataSchemaError` with the message: "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design." (See US-1)
- **FR-008**: System MUST detect if the number of unique users is less than 30 and, if so, execute a Generalized Least Squares (GLS) model with robust standard errors instead of the weighted regression or mixed-effects model. (See Edge Cases)
- **FR-009**: System MUST merge categories where the semantic similarity distance is below a configurable threshold as a preprocessing step before entropy calculation, to reduce noise from granular category labels. (See US-3, FR-005)

### Key Entities

- **UserSession**: Represents a single observation window for a specific user, containing the input (recommendations) and output (enrollments) lists.
- **DiversityScore**: A scalar value representing the Shannon entropy (log base 2) of a list of categories, used as both predictor and outcome.
- **Baseline_Interest_Vector**: A vector representing the user's historical topic preferences, used as a covariate for propensity score estimation.
- **ModelResult**: The output object containing fixed effects, weights, p-values, and diagnostic metrics (VIF, convergence status).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between `Recommendation_Diversity` and `Learner_Diversity` is measured against the null hypothesis of zero correlation (p < 0.05). (See US-2)
- **SC-002**: The stability of the model coefficient for `Recommendation_Diversity` is measured against the sensitivity analysis sweep (thresholds {0.01, 0.05, 0.1}), requiring the p-value to remain < 0.05 across at least 2/3 of the sweep points. (See US-3)
- **SC-003**: The false-positive rate of the residual permutation test is measured against the theoretical alpha level of 0.05 (i.e., the observed effect should not exceed the 95th percentile of the null distribution if the null is true). (See US-3)
- **SC-004**: The collinearity diagnostic (VIF) for `Baseline_Interest` is measured against the threshold of 5.0; if exceeded, the model must flag the limitation. (See US-2)
- **SC-005**: The total compute time for the entire pipeline (ingestion, modeling, robustness) is measured against the GitHub Actions free-tier limit of 6 hours. (See Assumptions)

## Assumptions

- **Assumption about data availability**: The public dataset (e.g., from OpenML or Zenodo) contains distinct, non-overlapping columns for "recommended items" and "enrolled items" for the same user sessions, and the category labels are consistent across both lists. If this is not true, the project cannot proceed without a clarification request.
- **Assumption about methodological framing**: Since the study uses observational data without random assignment, all findings will be framed as associational. The study does not claim to prove causality, but rather to identify a predictive relationship controlling for baseline interests.
- **Assumption about compute constraints**: The analysis is designed to run entirely on a CPU-only environment (GitHub Actions free tier: 2 cores, ~7 GB RAM). No GPU-accelerated libraries (e.g., CUDA, bitsandbytes) or large model training will be used; the linear mixed-effects model and permutation tests are assumed to be computationally tractable on this hardware for the expected dataset size (< 100k rows).
- **Assumption about metric justification**: The use of Shannon entropy for diversity is based on standard information theory practices in recommendation systems literature. The sensitivity analysis sweep (0.01, 0.05, 0.1) is a standard, CPU-trivial method to justify threshold robustness.
- **Assumption about baseline control**: The "Baseline_Interest_Vector" derived from pre-study history is a sufficient proxy for intrinsic user preferences. The study acknowledges that recommendations are highly correlated with baseline interests by design; therefore, Propensity Score Weighting is used to balance this confounding factor rather than assuming conditional independence.