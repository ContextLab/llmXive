# Feature Specification: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

**Feature Branch**: `001-evaluating-variable-selection-power`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Pipeline & Simulation Loop (Priority: P1)

The system MUST download 10 regression datasets from OpenML, extract predictor covariance structures, and simulate 1,000 synthetic outcome vectors per dataset across 4 Signal-to-Noise Ratio (SNR) levels.

**Why this priority**: This is the foundational data generation step; without simulated ground truth, no power analysis can occur. It delivers the raw material for all subsequent analysis.

**Independent Test**: Can be fully tested by verifying that 40,000 synthetic datasets (10 datasets × [deferred] sims × 4 SNR levels) are generated and stored in memory/disk without error, and that true coefficients are recorded for each.

**Acceptance Scenarios**:

1. **Given** OpenML API is accessible, **When** the script requests 10 regression datasets, **Then** exactly 10 datasets with ≥ 100 rows and ≥ 3 predictors are loaded.
2. **Given** a dataset with known covariance, **When** the simulation runs for SNR levels {0.5, 1.0, 2.0, 5.0}, **Then** [deferred] outcome vectors are generated per SNR level with known ground-truth coefficients.
3. **Given** the simulation completes, **When** checking memory usage, **Then** peak RAM usage remains ≤ 7 GB on the CI runner.

---

### User Story 2 - Power Metric Computation (Priority: P2)

The system MUST apply three selection methods (Forward Stepwise, Backward Elimination, LASSO) to each simulated dataset and calculate empirical power as the proportion of true non-zero coefficients correctly retained.

**Why this priority**: This delivers the core metric (power) required to answer the research question. It is independent of the statistical comparison step.

**Independent Test**: Can be fully tested by running the selection methods on a small subset of 10 simulations and verifying that power = (True Positives / Total True Non-Zero Coefficients) matches expected values.

**Acceptance Scenarios**:

1. **Given** a simulated dataset with 5 true non-zero coefficients, **When** LASSO selects 3 variables, **Then** the power metric is recorded as 0.6 (3/5).
2. **Given** all 40,000 simulations are processed, **When** aggregating results, **Then** a power rate is calculated for each method-SNR combination.
3. **Given** collinear predictors exist, **When** the selection method runs, **Then** a collinearity diagnostic (VIF or condition number) is recorded for the original dataset.

---

### User Story 3 - Statistical Comparison & Visualization (Priority: P3)

The system MUST compare power rates across methods using Kruskal-Wallis tests with Holm correction for multiplicity and generate power curves with sensitivity analysis on significance thresholds.

**Why this priority**: This delivers the final research output and ensures methodological rigor (multiplicity control, sensitivity). It depends on US-2 data but can be tested independently on static results.

**Independent Test**: Can be fully tested by providing a CSV of power rates and verifying that p-values are corrected and plots are generated for SNR ∈ {0.5, 1.0, 2.0, 5.0} and Alpha ∈ {0.01, 0.05, 0.10}.

**Acceptance Scenarios**:

1. **Given** power rates for 3 methods across 4 SNR levels, **When** the Kruskal-Wallis test runs, **Then** p-values are adjusted using Holm's method for family-wise error control.
2. **Given** the primary alpha threshold is 0.05, **When** sensitivity analysis runs, **Then** power rates are also reported for alpha ∈ {0.01, 0.10}.
3. **Given** the analysis completes, **When** checking the output directory, **Then** plots (Power vs. SNR) are generated for each selection method.

---

### Edge Cases

- What happens when an OpenML dataset contains perfect multicollinearity (condition number > 10^10)? (System must skip the dataset and log a warning).
- How does system handle a simulation where the true coefficient is exactly zero? (System must count this as a true negative and exclude from power denominator).
- How does system handle API timeout during dataset download? (System must retry 3 times with 10-second backoff before failing the job).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download exactly 10 regression datasets from OpenML with ≥ 100 rows and ≥ 3 predictors (See US-1)
- **FR-002**: System MUST simulate 1,000 outcome vectors per dataset across SNR levels {0.5, 1.0, 2.0, 5.0} (See US-1)
- **FR-003**: System MUST apply Forward Stepwise, Backward Elimination, and LASSO selection methods using CPU-only execution (See US-2)
- **FR-004**: System MUST calculate empirical power as True Positives / Total True Non-Zero Coefficients (See US-2)
- **FR-005**: System MUST apply Holm's correction for multiple comparisons across SNR levels (See US-3)
- **FR-006**: System MUST run sensitivity analysis on significance thresholds Alpha ∈ {0.01, 0.05, 0.10} (See US-3)
- **FR-007**: System MUST record collinearity diagnostics (VIF or condition number) for all datasets (See US-2)
- **FR-008**: System MUST complete execution within 6 hours on 2 CPU cores (See US-1)

### Key Entities *(include if feature involves data)*

- **SimulatedDataset**: Represents one instance of X (real covariance) and Y (simulated outcome) with metadata for SNR, true coefficients, and selection results.
- **PowerMetric**: Aggregated record containing method name, SNR level, alpha threshold, empirical power rate, and confidence interval.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Empirical power rates are measured against ground-truth coefficients embedded in SimulatedDataset (See US-2)
- **SC-002**: Statistical comparisons are measured against Holm-corrected p-values for family-wise error control (See US-3)
- **SC-003**: Total job runtime is measured against the 6-hour CI limit (See US-1)
- **SC-004**: Peak memory usage is measured against the 7 GB RAM limit (See US-1)

## Assumptions

- OpenML API remains accessible and rate-limits are respected during 10 dataset downloads.
- Selected OpenML datasets contain ≤ 50,000 rows to ensure covariance matrices fit within 7 GB RAM.
- Python `scikit-learn` library is available for LASSO implementation on CPU without CUDA dependencies.
- The CI runner environment provides at least 2 CPU cores and 7 GB RAM as specified.
- True coefficients are set to non-zero values for 20% of predictors in the simulation design.
