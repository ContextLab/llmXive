# Feature Specification: Assessing the Validity of Frequentist Confidence Intervals with Small Sample Sizes

**Feature Branch**: `001-assess-ci-coverage`  
**Created**: 2024-01-01  
**Status**: Draft  
**Input**: User description: "Research question: Do standard frequentist confidence intervals (e.g., t-intervals, z-intervals) maintain their nominal coverage probabilities when applied to samples of size n < 30 drawn from real-world distributions?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Monte Carlo Simulation Engine (Priority: P1)

The system MUST execute a Monte Carlo simulation that draws repeated small samples (n < 30) from full UCI datasets, computes standard t-intervals and z-intervals, and checks empirical coverage against the known population mean.

**Why this priority**: This is the foundational capability; without the simulation engine, no coverage data can be generated to address the research question.

**Independent Test**: Can be fully tested by running the simulation on a single dataset (e.g., UCI Wine) and verifying that the output contains coverage rates for both t-intervals and z-intervals.

**Acceptance Scenarios**:

1. **Given** a UCI dataset with continuous variables, **When** the system draws [deferred] samples of size n=20, **Then** it outputs the percentage of intervals containing the true population mean.
2. **Given** a sample size of n=10, **When** the system computes a [deferred] t-interval, **Then** it uses the t-distribution critical value (t_{n-1,0.975}) and records coverage.
3. **Given** a skewed distribution, **When** the system runs the simulation, **Then** it completes within 6 hours on a CPU-only environment.

---

### User Story 2 - Aggregation and Statistical Reporting (Priority: P2)

The system MUST aggregate coverage rates across multiple datasets and sample sizes, apply multiple-comparison corrections where applicable, and frame findings as associational rather than causal.

**Why this priority**: Raw coverage rates from single datasets do not generalize; aggregation allows for statistical inference about the method's behavior across distributions.

**Independent Test**: Can be fully tested by feeding pre-computed coverage data from 5 datasets and verifying that the system outputs a summary table with corrected p-values.

**Acceptance Scenarios**:

1. **Given** coverage rates from 10 datasets, **When** the system aggregates results, **Then** it calculates the mean deviation from [deferred] nominal coverage.
2. **Given** multiple hypothesis tests (one per dataset), **When** the system reports significance, **Then** it applies a family-wise error correction (e.g., Bonferroni).
3. **Given** the results, **When** the system generates the final report, **Then** it explicitly states findings are associational regarding coverage properties.

---

### User Story 3 - Sensitivity Analysis on Confidence Thresholds (Priority: P3)

The system MUST perform a sensitivity analysis by sweeping the nominal confidence level across a small concrete set (e.g., [deferred], [deferred], [deferred]) to test robustness of coverage deviations.

**Why this priority**: A single threshold (95%) may hide instability; sensitivity analysis validates whether deviations are consistent across confidence levels.

**Independent Test**: Can be fully tested by running the simulation with fixed parameters but varying the confidence level argument and verifying output differences.

**Acceptance Scenarios**:

1. **Given** a fixed dataset and sample size, **When** the system sweeps confidence levels (90%, 95%, 99%), **Then** it reports coverage rates for each level.
2. **Given** the sweep results, **When** the system generates the sensitivity report, **Then** it shows how the false-positive rate (non-coverage) varies across the set.

---

### Edge Cases

- **What happens when** a selected UCI dataset contains fewer than 30 rows? The system MUST skip that dataset and log a warning.
- **How does system handle** datasets with missing values? The system MUST exclude rows with missing values for the selected variable before resampling.
- **What happens when** a variable is categorical? The system MUST filter for continuous numeric variables only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download numeric datasets from the UCI Machine Learning Repository via HTTP without GPU acceleration (See US-1).
- **FR-002**: System MUST select continuous variables with no missing values to ensure the full dataset represents the population (See US-1).
- **FR-003**: System MUST perform 10,000 Monte Carlo replications per dataset to ensure statistical power for coverage estimation (See US-1).
- **FR-004**: System MUST execute all computations on CPU only, forbidding CUDA, mixed-precision, or GPU-specific libraries (See US-1).
- **FR-005**: System MUST compute both [deferred] t-intervals and [deferred] z-intervals using sample statistics (See US-1).
- **FR-006**: System MUST apply Bonferroni correction when testing significance across multiple datasets to control family-wise error rate (See US-2).
- **FR-007**: System MUST frame all output findings as associational regarding coverage properties, avoiding causal claims (See US-2).
- **FR-008**: System MUST sweep the nominal confidence level over {90%, 95%, [deferred]} for sensitivity analysis (See US-3).

### Key Entities *(include if feature involves data)*

- **Simulation Run**: Represents one complete execution of the Monte Carlo process for a specific dataset, sample size, and confidence level.
- **Coverage Record**: Represents the outcome of a single replication (interval contains true mean: boolean).
- **Aggregate Report**: Represents the summarized statistics (mean coverage, deviation, p-values) across all replications.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Empirical coverage rate is measured against the nominal [deferred] level to quantify deviation (See US-1).
- **SC-002**: Total runtime is measured against the CI limit of ≤ 6 hours on a 2-core CPU runner (See US-1).
- **SC-003**: Memory usage is measured against the CI limit of ≤ 7 GB RAM during peak execution (See US-1).
- **SC-004**: Sensitivity analysis results are measured against the requirement to report coverage variation across {[deferred], [deferred], [deferred]} (See US-3).

## Assumptions

- UCI Machine Learning Repository datasets are accessible via direct HTTP requests without authentication during the CI job.
- The full dataset available in UCI serves as the "population" with a known true mean for coverage validation.
- The 95% confidence level is selected as the community standard baseline for statistical inference.
- The GitHub Actions free-tier runner provides sufficient CPU cycles to complete 10,000 replications across 15 datasets within 6 hours.
- All selected variables are continuous numeric types suitable for mean and standard deviation calculations.
- No GPU hardware or CUDA-enabled libraries are available or required for this statistical analysis.
- Missing values in selected variables are handled by row-wise exclusion rather than imputation.
