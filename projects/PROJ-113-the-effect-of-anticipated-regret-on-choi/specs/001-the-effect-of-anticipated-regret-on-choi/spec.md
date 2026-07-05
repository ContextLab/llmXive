# Feature Specification: The Effect of Anticipated Regret on Choice Deferral

**Feature Branch**: `001-the-effect-of-anticipated-regret-on-choice-deferral`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Does higher anticipated regret increase the likelihood that individuals defer making a choice, after controlling for option set size, perceived risk, time pressure, and individual decision‑making style?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Regret Proxy Calculation (Priority: P1)

The research pipeline must successfully ingest raw decision-making logs from public datasets (OpenML/Kaggle), filter for valid choice trials, and compute a quantitative "anticipated regret proxy" for each trial based on the variance of expected utilities across available options.

**Why this priority**: This is the foundational data preparation step. Without a valid, computed regret proxy and a clean dataset of deferral events, no statistical modeling can occur. It represents the core transformation of raw data into the specific predictor variable required by the research question.

**Independent Test**: The pipeline can be tested by running the preprocessing script on a static, small sample of the "DecisionMaking" dataset and verifying that the output CSV contains a `regret_proxy` column with non-null, positive variance values derived strictly from option attributes, and that rows with missing deferral flags are correctly excluded.

**Acceptance Scenarios**:

1. **Given** a raw dataset file with option attributes and choice outcomes, **When** the preprocessing script runs, **Then** it outputs a cleaned CSV where every row has a calculated `regret_proxy` (standard deviation of expected utilities) and a binary `deferral` flag.
2. **Given** a trial where no choice was made within the specified time window (e.g., 24h), **When** the script processes the row, **Then** the `deferral` flag is set to 1 (true).
3. **Given** a trial with only one option available, **When** the script calculates the proxy, **Then** the `regret_proxy` is 0 (no variance), correctly reflecting zero anticipated regret due to lack of choice.

---

### User Story 2 - Mixed-Effects Logistic Regression Modeling (Priority: P2)

The system must fit a mixed-effects logistic regression model to quantify the association between the anticipated regret proxy and the probability of choice deferral, while controlling for option set size, perceived risk, time pressure, and decision-making style, and including a random intercept for participants.

**Why this priority**: This is the primary analysis engine that directly answers the research question. It must correctly implement the statistical model specified in the methodology to produce the coefficients and p-values necessary for hypothesis testing.

**Independent Test**: The model fitting process can be tested by running the analysis script on the preprocessed data and verifying that the output includes a regression table with the main effect of `regret_proxy`, the interaction term with `option_count`, and the random effect variance for `participant`.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset with computed predictors, **When** the modeling script executes, **Then** it outputs a `coefficients.csv` file containing the beta coefficient, standard error, and p-value for the `regret_proxy` term.
2. **Given** the fitted model, **When** the script checks for multicollinearity, **Then** it calculates and reports the Variance Inflation Factor (VIF) for all fixed effects, flagging any VIF > 5.
3. **Given** the model results, **When** the script performs 5-fold cross-validation, **Then** it outputs the mean Area Under the Curve (AUC) score for out-of-sample prediction.

---

### User Story 3 - Robustness Checks and Sensitivity Analysis (Priority: P3)

The pipeline must execute robustness checks by replicating the analysis on a secondary dataset (e.g., Online Shopping) and performing a sensitivity analysis on the decision cutoffs or proxy definitions to ensure findings are not artifacts of specific parameter choices.

**Why this priority**: This ensures the scientific validity and generalizability of the results. It addresses the "multiplicity & power" and "threshold justification" requirements by verifying that the observed effect holds across different data contexts and parameter variations.

**Independent Test**: The robustness module can be tested by pointing it at the secondary dataset and a modified proxy definition (e.g., using price variance instead of utility variance) and verifying that it produces a separate set of regression coefficients and a sensitivity report.

**Acceptance Scenarios**:

1. **Given** the secondary dataset (Online Shopping), **When** the robustness script runs, **Then** it produces a separate regression table and reports whether the direction of the `regret_proxy` coefficient matches the primary analysis.
2. **Given** a set of sensitivity thresholds (e.g., varying the utility dispersion calculation method), **When** the script sweeps these thresholds, **Then** it generates a report showing how the headline odds ratio and p-value change across the swept values.
3. **Given** the final results, **When** the report is compiled, **Then** it explicitly states whether the effect remains significant after correcting for multiple comparisons (e.g., Bonferroni or FDR) if >1 hypothesis was tested.

### Edge Cases

- **What happens when** a participant has only one trial in the dataset? The mixed-effects model must handle this by either excluding the participant from the random effect estimation or using a fixed-effects only fallback for that specific participant, ensuring the model does not crash due to singular fit.
- **How does the system handle** missing values in covariates (e.g., missing "perceived risk" scores)? The system must implement a specific imputation strategy (e.g., mean imputation or exclusion) and explicitly log the number of rows affected, ensuring the final sample size is reported.
- **What happens when** the variance of expected utilities is exactly zero for all options in a trial? The `regret_proxy` must be recorded as 0, and the model must be able to converge without division-by-zero errors or singular matrix exceptions.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest raw decision-making logs from the OpenML "DecisionMaking" collection and the Kaggle "Online Shopping Behavior" dataset, filtering for trials with definitive deferral flags. (See US-1)
- **FR-002**: System MUST calculate an anticipated regret proxy for each trial as the standard deviation of expected utilities across available options, handling cases with single options by assigning a value of zero. (See US-1)
- **FR-003**: System MUST fit a mixed-effects logistic regression model with `deferral` as the outcome, `regret_proxy` and `option_count` (and their interaction) as fixed effects, and `participant` as a random intercept. (See US-2)
- **FR-004**: System MUST perform 5-fold cross-validation on the fitted model to assess out-of-sample predictive performance and report the mean AUC. (See US-2)
- **FR-005**: System MUST execute a robustness check by replicating the primary analysis on the secondary dataset and performing a sensitivity analysis sweeping the regret proxy definition over at least three variations (e.g., utility variance, price variance, attribute range). (See US-3)
- **FR-006**: System MUST calculate and report Variance Inflation Factors (VIF) for all fixed effects to detect predictor collinearity, flagging any VIF > 5. (See US-2)
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to p-values if more than one primary hypothesis is tested. (See US-3)

### Key Entities

- **Trial**: A single decision event containing option attributes, choice outcome (deferral vs. selection), and contextual covariates.
- **Participant**: An individual decision-maker identified by a unique ID, whose repeated trials are grouped for random effects modeling.
- **Regret Proxy**: A computed numeric feature representing the anticipated regret for a trial, derived from the variance of expected utilities.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The association between anticipated regret and choice deferral is measured by the magnitude and significance (p-value) of the `regret_proxy` coefficient in the mixed-effects model, referenced against the null hypothesis of no effect. (See US-2)
- **SC-002**: Model predictive validity is measured by the mean Area Under the Curve (AUC) from 5-fold cross-validation, referenced against a baseline logistic regression without the regret proxy. (See US-2)
- **SC-003**: Robustness of findings is measured by the consistency of the direction and significance of the `regret_proxy` coefficient across the primary and secondary datasets, referenced against the primary analysis result. (See US-3)
- **SC-004**: Sensitivity of results to parameter choice is measured by the variation in the odds ratio of the `regret_proxy` when the proxy definition is swept across three distinct variations, referenced against the stability of the effect size. (See US-3)
- **SC-005**: Data integrity is measured by the Variance Inflation Factor (VIF) for all predictors, referenced against the threshold of 5.0 to ensure no severe collinearity exists. (See US-2)

## Assumptions

- **Dataset Variable Fit**: It is assumed that the selected OpenML and Kaggle datasets contain the necessary variables to compute the regret proxy (option attributes/expected utilities) and the outcome (deferral flag). If a specific dataset lacks a required variable (e.g., explicit "perceived risk" scores), the analysis will proceed using available proxies or exclude that covariate, with the limitation noted in the final report.
- **Computational Feasibility**: The analysis assumes that the selected datasets can be processed entirely within the GitHub Actions free-tier limits (2 CPU cores, ~7 GB RAM, 6-hour time limit) using Python's `statsmodels` or `scikit-learn` without GPU acceleration or large-model inference.
- **Observational Nature**: The study assumes an observational design where random assignment is not present; therefore, findings will be framed strictly as associational, not causal, unless a specific identification strategy is explicitly implemented in the data.
- **Proxy Validity**: It is assumed that the standard deviation of expected utilities across options serves as a valid and sufficient proxy for "anticipated regret" in the absence of direct self-report measures in the public datasets.
- **Deferral Definition**: It is assumed that the "deferral" flag in the source datasets correctly identifies instances where a choice was postponed or not made within the relevant timeframe (e.g., 24 hours), and that this definition is consistent across both datasets.
