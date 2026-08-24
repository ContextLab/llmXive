# Feature Specification: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

**Feature Branch**: `001-assessing-the-validity-of-significance`  
**Created**: 2026-07-20  
**Status**: Draft  
**Input**: User description: "Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data"

## User Scenarios & Testing

### User Story 1 - Simulate Missing Data Mechanisms and Calculate Empirical Type I Error (Priority: P1)

The researcher needs to generate synthetic missing data patterns (MCAR, MAR, MNAR) on real RCT datasets with known ground truth (null hypothesis) to calculate the empirical Type I error rate of complete-case analysis.

**Why this priority**: This is the core scientific engine. Without the ability to simulate missingness and calculate the resulting error rates, the study cannot identify "tipping points" or validate the robustness of complete-case methods.

**Independent Test**: The system can be tested by running a single simulation loop (e.g., 500 iterations) with a fixed seed, a specific dataset, and a defined missingness rate (e.g., [deferred] MAR), and verifying that the output includes a calculated p-value distribution and an empirical error rate metric.

**Acceptance Scenarios**:

1. **Given** a public RCT dataset with treatment and outcome columns, **When** the system simulates 20% missingness under MAR (dependent on age) and sets the treatment effect to zero, **Then** the system outputs a list of 500 p-values and calculates the proportion of p-values < 0.05.
2. **Given** the same dataset and missingness rate, **When** the system switches the mechanism to MNAR (dependent on unobserved outcome values), **Then** the system outputs a distinct set of 500 p-values and a new empirical error rate that differs from the MCAR/MAR result.

### User Story 2 - Identify Tipping Points via Sensitivity Analysis (Priority: P2)

The researcher needs to systematically vary missingness rates from [deferred] to [deferred] and analyze the deviation of the Complete-Case (CC) method from the nominal [deferred] Type I error rate to identify specific thresholds where the method fails.

**Why this priority**: This transforms raw simulation data into actionable "tipping points" (e.g., ">15% missingness"). This directly addresses the research question regarding when imputation becomes mandatory.

**Independent Test**: The system can be tested by executing a batch simulation across multiple missingness rates (e.g., [deferred], [deferred], [deferred], [deferred], [deferred]) and verifying that the output contains a curve or table showing the error rate trend and flags the specific rate where the error exceeds the nominal 5% by a defined margin (e.g., >10% relative increase).

**Acceptance Scenarios**:

1. **Given** a fixed missingness mechanism (e.g., MNAR), **When** the system runs simulations for missingness rates of [deferred], [deferred], [deferred], [deferred], and [deferred], **Then** the system generates a data series showing the empirical Type I error rate for each step.
2. **Given** the data series from the previous step, **When** the system compares the error rate at [deferred] missingness against the nominal [deferred] level, **Then** the system identifies and reports a "tipping point" if the error rate exceeds 5.5% (a [deferred] relative increase [deferred]).

### User Story 3 - Compare Complete-Case vs. Imputation Methods (Priority: P3)

The researcher needs to compare the performance of Complete-Case (CC) analysis against Multiple Imputation (MI) and Inverse Probability Weighting (IPW) to demonstrate the relative validity of the correction methods.

**Why this priority**: This provides the necessary context and validation. It proves that the identified "tipping points" for CC are indeed resolved by standard correction methods, reinforcing the recommendation to use imputation.

**Independent Test**: The system can be tested by running a single condition (e.g., [deferred] MAR) with three analysis methods (CC, MI, IPW) and verifying that the output includes three distinct empirical Type I error rates, showing CC is inflated while MI/IPW remain near nominal.

**Acceptance Scenarios**:

1. **Given** a dataset with [deferred] MAR missingness and a null treatment effect, **When** the system applies CC, MI (5 imputations), and IPW, **Then** the output table lists the empirical Type I error rate for each method (e.g., CC=12%, MI=5.1%, IPW=5.0%).
2. **Given** the comparison results, **When** the system generates a visualization, **Then** the plot clearly distinguishes the CC error curve (inflated) from the MI/IPW curves (stable near [deferred]).

### Edge Cases

- What happens when the dataset has < 100 rows? (Simulation may lack power; system should flag or skip).
- How does the system handle a dataset where the outcome is binary but the CC method defaults to a t-test? (System must enforce Wilcoxon or logistic regression for binary outcomes).
- What if the MNAR mechanism cannot be simulated because the outcome variable is fully observed in the source data? (System must generate synthetic outcome values first).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and load 3-5 public RCT datasets (binary or continuous outcomes) from OpenML or UCI, ensuring the data contains treatment, outcome, and at least two covariates. (See US-1)
- **FR-002**: System MUST simulate missing data patterns under three distinct mechanisms: MCAR (random), MAR (dependent on observed covariates), and MNAR (dependent on unobserved outcome values). For MNAR, the system MUST first artificially corrupt the outcome variable to create a "true" unobserved state, verify that the corrupted data maintains a zero treatment effect, and then apply the missingness mechanism. (See US-1)
- **FR-003**: System MUST calculate empirical Type I error rates by permuting treatment labels to establish a true null hypothesis (Randomization Inference) and counting the proportion of p-values < 0.05 across 500 Monte Carlo iterations per condition. (See US-1)
- **FR-004**: System MUST execute a sensitivity analysis sweeping missingness rates from [deferred] to [deferred] in [deferred] increments and identify the specific rate where the CC error rate exceeds the nominal [deferred] level by >10% relative increase. (See US-2)
- **FR-005**: System MUST implement and compare three analysis methods: Complete-Case (t-test/Wilcoxon), Multiple Imputation (5 imputations via chained equations), and Inverse Probability Weighting. (See US-3)
- **FR-006**: System MUST perform a Binomial test on the count of p-values < 0.05 to determine if the empirical Type I error rate significantly deviates from the nominal [deferred] level. (See US-2)
- **FR-007**: System MUST handle binary outcomes by using non-parametric or logistic-based tests instead of t-tests to maintain measurement validity. (See US-1)

### Key Entities

- **SimulationConfig**: Defines the dataset source, missingness mechanism (MCAR/MAR/MNAR), missingness rate (5-40%), and outcome type.
- **ErrorMetric**: Stores the empirical Type I error rate, power, and p-value distribution for a specific simulation run.
- **ComparisonResult**: Aggregates error metrics across CC, MI, and IPW methods for a given condition.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Empirical Type I error rate for CC under MCAR conditions is measured against the nominal 5% level, with a pass threshold of ≤ 6% (a 20% relative increase over the nominal [deferred] level). (See US-1)
- **SC-002**: The "tipping point" missingness rate is measured against the condition where CC error rate exceeds 5.5% (a [deferred] relative increase [deferred]). (See US-2)
- **SC-003**: The deviation of p-value distribution is measured against the theoretical uniform distribution expected under the null using a Binomial test at the 0.05 threshold. (See US-2)
- **SC-004**: Statistical power under the alternative hypothesis is measured against the expected power of the CC method at 80% (to ensure the simulation is not underpowered). (See US-1)
- **SC-005**: The relative error inflation of CC vs. MI is measured at the identified tipping point, confirming CC error > 2 * MI error. (See US-3)

## Assumptions

- **Assumption about data availability**: Public RCT datasets from OpenML/UCI contain sufficient covariates (e.g., age, sex) to construct valid MAR mechanisms. If a dataset lacks these, a `[NEEDS CLARIFICATION]` marker is used, or a synthetic dataset generator is triggered.
- **Assumption about computational limits**: The simulation (500 iterations x 6 rates x 3 mechanisms x 3 methods) will complete within the 6-hour GitHub Actions free-tier limit (2 CPU, 7GB RAM) by processing datasets in batches and using vectorized operations (numpy/pandas) rather than iterative loops where possible.
- **Assumption about statistical validity**: The "ground truth" treatment effect of zero is established via treatment label permutation (Randomization Inference) to ensure exchangeability, rather than assuming the original dataset's structure supports a null hypothesis test without bias.
- **Assumption about missingness simulation**: For MNAR simulation, the system can generate unobserved outcome values based on the observed distribution to create a dependency, even if the original data is fully observed, provided the corruption process preserves the zero treatment effect.
- **Assumption about method selection**: The system defaults to Wilcoxon rank-sum tests for binary outcomes and t-tests for continuous outcomes to ensure robustness across data types without requiring complex GLM fitting that might exceed CPU limits.
- **Assumption about power**: The sample sizes of public datasets are assumed to be large enough (N > 100) to provide stable Type I error estimates; if a dataset is too small, the simulation for that specific dataset is skipped and logged.