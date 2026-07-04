# Feature Specification: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

**Feature Branch**: `001-evaluating-the-impact-of-variable-select`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Pipeline & Simulation Loop (Priority: P1)

The system MUST download a set of regression datasets from OpenML., extract predictor covariance structures, and simulate multiple synthetic outcome vectors per dataset for each combination of 4 Signal-to-Noise Ratio (SNR) levels and 3 Sparsity levels.

**Why this priority**: This is the foundational data generation step; without simulated ground truth, no power analysis can occur. It delivers the raw material for all subsequent analysis.

**Independent Test**: Can be fully tested by verifying that A large set of synthetic datasets (multiple datasets × [deferred] sims × 4 SNR levels × 3 Sparsity levels) is generated and stored in memory/disk without error, and that true coefficients are recorded for each.

**Acceptance Scenarios**:

1. **Given** OpenML API is accessible, **When** the script requests 10 datasets, **Then** exactly 10 datasets with ≥ 100 rows and ≥ 3 predictors are loaded.
2. **Given** a dataset with known covariance, **When** the simulation runs for SNR levels {0.5, 1.0, 2.0, 5.0} and Sparsity levels {0.1, 0.2, 0.4}, **Then** [deferred] outcome vectors are generated per tuple with known ground-truth coefficients.
3. **Given** the simulation completes, **When** checking memory usage, **Then** peak RAM usage remains ≤ 7 GB on the CI runner.

---

### User Story 2 - Power Metric Computation (Priority: P2)

The system MUST apply three selection methods (Forward Stepwise, Backward Elimination, LASSO) to each simulated dataset and calculate empirical power as the proportion of true non-zero coefficients correctly retained AND found to be statistically significant (p < 0.05).

**Why this priority**: This delivers the core metric (power) required to answer the research question. It is independent of the statistical comparison step.

**Independent Test**: Can be fully tested by running the selection methods on a small subset of 10 simulations and verifying that power = (True Positives / Total True Non-Zero Coefficients) matches expected values within a tolerance of ±0.01.

**Acceptance Scenarios**:

1. **Given** a simulated dataset with 5 true non-zero coefficients, **When** LASSO selects 3 variables and OLS refitting yields p < 0.05 for 2 of them, **Then** the power metric is recorded as a moderate value (2/5).
2. **Given** all 120,000 simulations are processed, **When** aggregating results, **Then** a power rate is calculated for each method-SNR-Sparsity combination.
3. **Given** collinear predictors exist, **When** the selection method runs, **Then** a collinearity diagnostic (VIF or condition number) is recorded for the original dataset.

---

### User Story 3 - Statistical Comparison & Visualization (Priority: P3)

The system MUST compare power rates across methods using Kruskal-Wallis tests on simulation-level mean power, followed by Dunn's post-hoc analysis with Holm correction for multiplicity, and generate power curves with sensitivity analysis on significance thresholds.

**Why this priority**: This delivers the final research output and ensures methodological rigor (multiplicity control, sensitivity, and correct unit of analysis). It depends on US-2 data but can be tested independently on static results.

**Independent Test**: Can be fully tested by providing a CSV of simulation-level mean power indicators and verifying that p-values are corrected and plots are generated for SNR ∈ {0.5, 1.0, 2.0, 5.0}, Sparsity ∈ {0.1, 0.2, 0.4}, and Alpha ∈ {0.01, 0.05, 0.10}.

**Acceptance Scenarios**:

1. **Given** simulation-level mean power for 3 methods across 4 SNR levels and 3 Sparsity levels, **When** the Kruskal-Wallis test runs, **Then** a significant result triggers Dunn's post-hoc tests with Holm correction.
2. **Given** the primary alpha threshold is 0.05, **When** sensitivity analysis runs, **Then** power rates are also reported for alpha ∈ {0.01, 0.10}.
3. **Given** the analysis completes, **When** checking the output directory, **Then** plots (Power vs. SNR) are generated for each selection method and sparsity level.

---

### Edge Cases

- What happens when an OpenML dataset contains perfect multicollinearity (condition number > 10^10)? (System must skip the dataset and log a warning).
- How does system handle a simulation where the true coefficient is exactly zero? (System must count this as a true negative and exclude from power denominator).
- How does system handle API timeout during dataset download? (System must retry a limited number of times with a time-based backoff before failing the job).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download exactly 10 regression datasets from OpenML with ≥ 100 rows and ≥ 3 predictors (See US-1)
- **FR-002**: System MUST simulate a sufficient number of outcome vectors per dataset, per SNR level, AND per Sparsity level to ensure statistical robustness. (See US-1)
- **FR-003**: System MUST apply Forward Stepwise, Backward Elimination, and LASSO selection methods using CPU-only execution (See US-2)
- **FR-004**: System MUST calculate empirical power as the proportion of true non-zero coefficients that are selected AND have a p-value < 0.05 (See US-2)
- **FR-005**: System MUST apply Kruskal-Wallis tests followed by Dunn's post-hoc analysis with Holm correction for multiple comparisons (See US-3)
- **FR-006**: System MUST run sensitivity analysis on significance thresholds Alpha ∈ {0.01, 0.05, 0.10} (See US-3)
- **FR-007**: System MUST record collinearity diagnostics (VIF or condition number) for all datasets (See US-2)
- **FR-008**: System MUST complete execution within 6 hours on 2 CPU cores (See US-1)
- **FR-009**: System MUST refit OLS on variables selected by LASSO to calculate p-values for power determination (See US-2)

### Key Entities *(include if feature involves data)*

- **SimulatedDataset**: Represents one instance of X (real covariance) and Y (simulated outcome) with metadata for SNR, Sparsity, true coefficients, and selection results.
- **PowerMetric**: Aggregated record containing method name, SNR level, Sparsity level, alpha threshold, empirical power rate, and confidence interval.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Empirical power rates are measured against ground-truth coefficients embedded in SimulatedDataset (See US-2)
- **SC-002**: Statistical comparisons are measured against Holm-corrected p-values from Dunn's post-hoc tests (See US-3)
- **SC-003**: Total job runtime is measured against the 6-hour CI limit (See US-1)
- **SC-004**: Peak memory usage is measured against the 7 GB RAM limit (See US-1)

## Assumptions

- OpenML API remains accessible and rate-limits are respected during 10 dataset downloads.
- Selected OpenML datasets contain ≤ 50,000 rows to ensure covariance matrices fit within 7 GB RAM.
- Python `scikit-learn` and `statsmodels` libraries are available for LASSO and OLS refitting on CPU without CUDA dependencies.
- The CI runner environment provides at least vCPUs with a base clock frequency and 7 GB RAM as specified.
- Sparsity levels are explicitly varied across a range of low-to-moderate values. to evaluate the impact of variable selection across different signal densities.
- SNR levels are fixed at a range of low to moderate values. to provide a standard range for power curve generation.
- Simulation count is fixed at a constant number per tuple to ensure statistical stability of the power estimates.