# Feature Specification: Evaluating the Impact of Data Imputation on Variance Estimation in Public Surveys

**Feature Branch**: `001-evaluating-imputation-impact`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Data Imputation on Variance Estimation in Public Surveys"

## User Scenarios & Testing

### User Story 1 - Core Data Pipeline & Baseline Variance Calculation (Priority: P1)

A researcher needs to ingest a complex survey dataset (e.g., ACS or GSS), apply a complete-case analysis, and calculate the baseline variance estimates for key population parameters (means/proportions) using design weights.

**Why this priority**: This establishes the "ground truth" reference point (complete-case) and validates the data ingestion pipeline, which is a prerequisite for any comparative analysis. Without a working pipeline that correctly handles survey weights and calculates design-based variances, subsequent imputation comparisons are invalid.

**Independent Test**: Can be fully tested by running the pipeline on a small, known subset of the GSS dataset and verifying that the calculated mean and variance match the values published in the GSS documentation or a manual calculation using `survey` package logic.

**Acceptance Scenarios**:

1. **Given** a CSV export of the GSS 2018 dataset with missing values in variable `hrs1`, **When** the system loads the data and applies survey weights, **Then** the system calculates the mean and variance for `hrs1` using complete-case analysis and outputs a JSON summary with a status of "success".
2. **Given** a dataset where the sampling design includes clustering (PSU), **When** the system calculates variance, **Then** the variance estimate must be computed using a design-based method (e.g., Taylor series linearization) that accounts for the clustering, not a simple i.i.d. assumption.

---

### User Story 2 - Synthetic Validation & Imputation Method Implementation (Priority: P2)

A researcher needs to validate imputation methods using a synthetic data generator where the true population parameters are known by construction, and then apply these methods to real-world datasets to compare relative efficiency.

**Why this priority**: This is the core experimental manipulation. It directly addresses the research question by quantifying the bias introduced by different imputation strategies in a controlled setting (synthetic) and measuring relative performance in real settings.

**Independent Test**: Can be fully tested by running the synthetic data generator to create a dataset with known ground-truth variance, applying MICE and Single Mean Imputation, and verifying that the MICE variance estimates are closer to the known true variance than the Single Imputation estimates.

**Acceptance Scenarios**:

1. **Given** a synthetic dataset generated with a known super-population variance and Missing At Random (MAR) missingness mechanism, **When** the system applies MICE (m=5) and Single Mean Imputation, **Then** the system outputs a comparison table showing the percentage bias of the variance estimate for each method relative to the known true variance.
2. **Given** a real-world dataset (e.g., GSS) with missing values, **When** the system applies MICE and Single Mean Imputation, **Then** the system outputs a comparison of variance estimates relative to a robust design-based estimator (e.g., Jackknife or BRR) to measure relative efficiency, without claiming absolute bias against an unknown true value.
3. **Given** a dataset with a binary outcome variable, **When** the system runs MICE with appropriate predictive mean matching, **Then** the system must successfully converge the imputation chains (R-hat < 1.05) and report the pooled variance estimate.

---

### User Story 3 - Sensitivity Analysis & Methodological Reporting (Priority: P3)

A researcher needs to perform a sensitivity analysis on the imputation thresholds (if applicable) and generate a report that explicitly frames findings as associational (due to observational nature) and includes multiplicity corrections.

**Why this priority**: This ensures the study meets the methodological soundness requirements (inference framing, multiplicity, sensitivity) mandated by the downstream panel, preventing the project from being rejected for statistical rigor issues.

**Independent Test**: Can be fully tested by checking the generated report for the presence of a "Multiplicity Correction" section and a "Sensitivity Analysis" table that varies a specific parameter (e.g., number of imputations `m` or convergence tolerance) and reports the impact on the headline bias rate.

**Acceptance Scenarios**:

1. **Given** that 5 different population parameters are tested, **When** the system compares imputation methods, **Then** the system applies a Bonferroni correction (or similar) to the p-values of the paired t-tests and reports the adjusted significance levels in the final output.
2. **Given** a specific imputation parameter (e.g., number of iterations), **When** the sensitivity analysis is triggered, **Then** the system must sweep the parameter over a concrete set (e.g., iterations ∈ {10, 20, 50}) and report the variation in the variance bias rate for the primary outcome.

### Edge Cases

- What happens when the dataset has a missingness rate > 30% in a specific variable? (System should skip that variable and log a warning, not crash).
- How does the system handle survey designs with extremely small cluster sizes (PSU=1)? (System should detect this and flag that variance estimation may be unstable, potentially falling back to a simplified estimator with a warning).
- How does the system handle convergence failure in MICE? (System should retry with a different seed or increased iterations up to a limit of 3 attempts, then abort that specific variable and report the failure).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse public survey datasets (ACS/GSS) preserving design variables (weights, strata, PSU) to enable design-based variance estimation (See US-1).
- **FR-002**: System MUST implement Complete-Case analysis, Single Mean Imputation, and MICE (m≥5) as distinct, reproducible processing pipelines. For MICE, the system MUST use 4 chains, 1000 iterations each, with 500 burn-in iterations to ensure reproducible convergence diagnostics (See US-2).
- **FR-002b**: System MUST include a synthetic data generator that creates datasets with known super-population parameters (mean, variance) and controllable missingness mechanisms (MCAR, MAR) to enable absolute bias calculation (See US-2).
- **FR-003**: System MUST calculate the bias of variance estimates as `(estimated_variance - true_variance) / true_variance` for synthetic datasets where ground truth is known. For real-world datasets, the system MUST calculate relative efficiency against a robust design-based estimator (e.g., Jackknife) (See US-2).
- **FR-004**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) when conducting >1 hypothesis test comparing imputation methods (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis sweeping at least one key parameter (e.g., `m` for MICE or convergence tolerance) over a concrete set (e.g., {5, 10, 20}) and report the impact on bias rates (See US-3).
- **FR-006**: System MUST explicitly label all findings regarding imputation impact as "associational" in the final report, avoiding causal language unless randomization was part of the design (See US-3).

### Key Entities

- **SurveyDataset**: Represents the raw data with attributes for weights, strata, PSU, and missingness patterns.
- **SyntheticData**: Represents a generated dataset with known ground-truth parameters and controlled missingness mechanisms.
- **ImputationResult**: Represents the output of a specific imputation method, containing the pooled variance estimate, standard error, and convergence diagnostics.
- **BiasMetric**: A derived entity calculating the relative difference between the estimated variance and the known benchmark variance (synthetic) or design-based estimator (real).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage bias of variance estimates for Complete-Case analysis is measured against the known true variance from the synthetic data generator (See US-2).
- **SC-002**: The difference in bias magnitude between MICE and Single Imputation is measured against the target that MICE bias magnitude must be ≤ 80% of Single Imputation bias magnitude (i.e., a [deferred] reduction target) in synthetic MAR scenarios (See US-2).
- **SC-003**: The stability of the variance estimates is measured against the results of the sensitivity analysis sweep (e.g., variation in bias < 5% across the tested parameter range), consistent with standard conventions for stability in simulation studies (See US-3).
- **SC-004**: The computational runtime of the full pipeline is measured against the standard time limit of the GitHub Actions free-tier runner (See Assumption 4).

## Assumptions

- **Assumption about data availability**: The selected public datasets (ACS/GSS) contain sufficient sample sizes and documented design variables (weights, strata, PSU) to support design-based variance estimation.
- **Assumption about missingness mechanism**: The missingness in the target variables is assumed to be Missing At Random (MAR) or Missing Completely At Random (MCAR) for the purpose of the MICE simulation. If the data is Missing Not At Random (MNAR), the results are interpreted as a sensitivity check, noting that MNAR mechanisms can cause bias in any direction (over- or under-estimation) depending on the correlation between the missingness mechanism and the unobserved values.
- **Assumption about computational feasibility**: The chosen datasets can be subsetted to fit within the available RAM limit of the CI runner without requiring chunking or out-of-core processing, as the primary analysis involves standard statistical models (linear/logistic) rather than deep learning.
- **Assumption about methodological rigor**: Since the study is observational (no random assignment of imputation methods to populations), all conclusions regarding the "impact" of imputation will be framed strictly as associations between method choice and variance accuracy, not causal effects on the population itself.
- **Assumption about threshold justification**: The number of imputations `m=5` is used as the default based on standard practice (Rubin's rules), but the sensitivity analysis (FR-005) will verify if this threshold is sufficient for the observed missingness rates.
- **Assumption about variable fit**: The GSS/ACS datasets contain the specific variables required for the analysis (e.g., `hrs1` or similar continuous/binary variables with documented missingness); if a specific variable lacks missingness, the system will automatically select the next available variable with >5% missingness.