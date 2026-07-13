# Feature Specification: Assessing the Reliability of Statistical Power Calculations in Real-World Datasets

**Feature Branch**: `001-assessing-power-reliability`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Assessing the Reliability of Statistical Power Calculations in Real-World Datasets"

## User Scenarios & Testing

### User Story 1 - Baseline Power vs. Empirical Ground Truth (Priority: P1)

As a researcher, I want to compare standard theoretical power calculations against empirical power estimates derived from bootstrapping on real-world datasets, so that I can quantify the baseline bias introduced by assuming idealized data distributions (normality, equal variance) without any induced violations.

**Why this priority**: This is the foundational step. Without establishing the discrepancy between the theoretical formula and the empirical reality on "clean" (but non-ideal) real-world data, we cannot attribute any later errors to specific induced violations. It validates the core methodology of the project.

**Independent Test**: Can be fully tested by running the pipeline on a single dataset (e.g., `mtcars`) with no induced violations and verifying that the output file contains both the calculated power (using `statsmodels` or `scipy` closed-form) and the empirical power (from 1,000 bootstrap iterations), and that a difference metric is recorded.

**Acceptance Scenarios**:

1. **Given** a public dataset with continuous outcomes (e.g., `iris`), **When** the system computes the standard theoretical power for a two-sample t-test (Cohen's d = 0.5) and runs 1,000 bootstrap simulations, **Then** the system outputs a JSON record containing the theoretical power, the empirical power, and the absolute error between them.
2. **Given** the same dataset, **When** the system repeats the process with a different fixed effect size (e.g., Cohen's d = 0.8), **Then** the system updates the record with the new power estimates and error metrics without crashing.

---

### User Story 2 - Controlled Violation Induction and Bias Mapping (Priority: P2)

As a researcher, I want to systematically inject specific assumption violations (heavy-tailed noise, autocorrelation, effect size heterogeneity) into datasets and re-compare theoretical vs. empirical power, so that I can generate bias curves showing how each specific violation type distorts power estimates. The goal is to measure the sensitivity of theoretical formulas to specific distributional violations using real-world data as a base, not to claim the perturbed data represents a new "real-world" state.

**Why this priority**: This addresses the core research question regarding the *extent* of bias caused by specific violations. It moves from "is there a bias?" to "what causes the bias and how much?"

**Independent Test**: Can be fully tested by running the pipeline on a dataset where only one specific violation (e.g., AR(1) autocorrelation) is introduced at a defined magnitude, and verifying that the output shows a distinct shift in the bias metric compared to the baseline (US-1).

**Acceptance Scenarios**:

1. **Given** a dataset, **When** the system injects heavy-tailed noise (t-distribution with df=3) at a contamination rate of [deferred], **Then** the system recalculates theoretical power, re-runs the 1,000 bootstrap simulations, and records the new bias value in the results.
2. **Given** a dataset, **When** the system introduces autocorrelation (AR(1) with $\phi=0.5$) to a time-series subset, **Then** the system detects the violation, applies the perturbation, and outputs a bias metric that differs from the non-autocorrelated baseline.
3. **Given** a dataset, **When** the system simulates effect size heterogeneity by mixing two sub-populations with means separated by 1.5 standard deviations, **Then** the system records the resulting power estimation error.

---

### User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

As a researcher, I want the system to perform a sensitivity analysis on the decision thresholds used for classifying "significant" power bias, so that I can ensure the findings are robust to small changes in the definition of "bias" and not an artifact of arbitrary cutoffs.

**Why this priority**: This ensures methodological soundness. Any conclusion about "systematic over-estimation" relies on a threshold for what counts as a "significant" error. Sensitivity analysis prevents the results from being brittle.

**Independent Test**: Can be fully tested by running the analysis with three different bias thresholds (e.g., 0.01, 0.05, 0.10) and verifying that the system outputs a summary showing how the classification of "high bias" cases changes across these thresholds.

**Acceptance Scenarios**:

1. **Given** the set of bias results from US-2, **When** the system sweeps the "significant bias" threshold across values {0.01, 0.05, 0.10}, **Then** the system outputs a table showing the count and percentage of datasets classified as "high bias" for each threshold.
2. **Given** a specific violation type (e.g., heavy tails), **When** the system varies the severity of the injection (e.g., contamination rates of [deferred], [deferred], and [deferred]), **Then** the system records the trend in bias magnitude to support the regression analysis.

---

### Edge Cases

- What happens when a dataset is too small (N < 10) to perform a meaningful bootstrap simulation? (System should skip or flag as "insufficient sample size" rather than crashing).
- How does the system handle datasets with missing values? (System must impute or drop missing values consistently before power calculation to avoid bias in the bootstrap).
- What happens if the induced violation (e.g., autocorrelation) cannot be applied because the data is not time-ordered? (System should skip that specific violation type for that dataset and log a warning).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load at least 10 diverse public datasets (e.g., from UCI, OpenML, or R `datasets`) covering continuous, count, and binary outcomes, each with a sample size N ≥ 30, to ensure generalizability and bootstrap validity. (See US-1)
- **FR-002**: System MUST compute standard theoretical power estimates for a two-sample t-test (or equivalent) using a fixed effect size (Cohen's d = 0.5) and standard assumptions (normality, equal variance). (See US-1)
- **FR-003**: System MUST perform a Monte Carlo simulation (minimum 1,000 iterations) using bootstrapping to generate empirical power estimates that preserve the actual data distribution. (See US-1)
- **FR-004**: System MUST implement specific data perturbation modules to inject heavy-tailed noise, autocorrelation (AR(1)), and effect size heterogeneity with configurable magnitude parameters (e.g., contamination rate, AR coefficient). (See US-2)
- **FR-005**: System MUST calculate and record the absolute and relative error between the theoretical power estimate and the empirical power estimate for every dataset and violation condition. (See US-2)
- **FR-006**: System MUST perform a sensitivity analysis by sweeping the "significant bias" threshold across a range of low-to-moderate values and reporting the variation in classification rates. (See US-3)
- **FR-007**: System MUST execute all computations on a CPU-only environment without requiring GPU acceleration, ensuring the total runtime for 10 datasets and 1,000 bootstrap iterations per condition remains ≤ 6 hours. (See Methodological Soundness - Compute Feasibility)
- **FR-008**: System MUST validate the bootstrap methodology by running a "Synthetic Ground Truth" test on fully synthetic datasets with known parameters, verifying that the bootstrap recovery rate matches the true power within 5% before processing real-world data. (See Methodological Soundness - Validation)
- **FR-009**: System MUST verify the successful application of induced violations (e.g., checking if AR(1) coefficient was achieved) and log the actual achieved magnitude for every perturbation attempt. (See US-2)
- **FR-010**: System MUST perform a "Bootstrap Validity Check" comparing bootstrap variance to analytical variance for each dataset; if the discrepancy exceeds a predefined threshold, the empirical power estimate must be flagged as "unreliable" and excluded from the final bias calculation. (See Methodological Soundness - Bootstrap Reliability)

### Key Entities

- **Dataset**: A structured collection of observations (rows) and variables (columns) used for the analysis. Key attributes: `source`, `outcome_type`, `sample_size`, `missing_value_rate`.
- **PowerEstimate**: A record containing the theoretical power, empirical power, and the calculated error metrics for a specific dataset and condition. Key attributes: `theoretical_power`, `empirical_power`, `absolute_error`, `relative_error`, `violation_type`, `violation_magnitude`, `bootstrap_reliability_flag`.
- **ViolationConfig**: A configuration object defining the type and magnitude of the induced assumption violation. Key attributes: `type` (e.g., "heavy_tail", "autocorrelation"), `parameter` (e.g., degrees of freedom, AR coefficient), `achieved_magnitude`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of bias (absolute difference between theoretical and empirical power) is measured against the type and magnitude of the induced assumption violation to determine which violations cause the largest systematic errors. (See US-2)
- **SC-002**: The proportion of datasets classified as having "significant bias" is measured against the sensitivity thresholds {0.01, 0.05, 0.10} to verify the robustness of the findings to cutoff selection. (See US-3)
- **SC-003**: The total computational runtime for the full simulation suite (multiple datasets × 3 violation types × [deferred] iterations) is measured against the 6-hour GitHub Actions free-tier limit to ensure feasibility. (See FR-007)
- **SC-004**: The consistency of the bias direction (over-estimation vs. under-estimation) is measured across different dataset types (continuous, count, binary) to determine if the bias is universal or context-dependent. (See US-2)
- **SC-005**: The sensitivity of theoretical power to induced violations is measured using a mixed-effects regression model where the predictor is the *induced* violation magnitude and the outcome is the observed bias, explicitly acknowledging the experimental design rather than implying discovery of natural data properties. (See Methodology Sketch)
- **SC-006**: The accuracy of the bootstrap method is measured by comparing the recovered power on synthetic datasets with known true power, ensuring the recovery rate is within 5% of the true value. (See FR-008)

## Assumptions

- The 10 selected public datasets contain sufficient sample sizes (N ≥ 30) to perform meaningful bootstrap simulations and t-tests without excessive computational overhead or instability.
- The "theoretical power calculation" refers to the closed-form approximation for a two-sample t-test assuming normality and equal variance, as implemented in standard libraries like `statsmodels` or `scipy`.
- The bootstrapping method (sampling with replacement) provides a sufficiently accurate approximation of the true empirical power distribution for the purposes of this study, *provided* that the Bootstrap Validity Check (FR-010) confirms reliability.
- The induced violations (heavy tails, autocorrelation, heterogeneity) can be applied to the datasets without fundamentally altering the underlying research question or making the data synthetic in a way that invalidates the "real-world" context, *provided* that the perturbation validity (FR-009) is logged and the goal is sensitivity analysis.
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) is sufficient to handle the memory footprint of loading 10 datasets and performing a substantial number of bootstrap iterations (10 datasets × 3 violations × [deferred] iterations) within the 6-hour time limit.
- The datasets do not contain missing values that would require complex imputation strategies; any missing values will be handled via simple listwise deletion to maintain computational simplicity.
- Bootstrap validity may fail for N < 30 or heavy-tailed distributions; the system is designed to detect and flag these cases (FR-010) rather than produce misleading results.