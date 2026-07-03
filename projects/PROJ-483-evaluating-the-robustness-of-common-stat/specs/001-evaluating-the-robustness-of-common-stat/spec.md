# Feature Specification: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

**Feature Branch**: `001-evaluating-robustness-tests`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Type I Error Inflation Quantification (Priority: P1)

A researcher needs to know exactly how much the false-positive rate of a standard t-test or ANOVA inflates when applied to public datasets with varying degrees of temporal or hierarchical non-independence.

**Why this priority**: This addresses the core research gap: the lack of empirical evidence on Type I error inflation. Without this, the project cannot answer the primary research question. It is the foundation for all subsequent analysis.

**Independent Test**: The system must be able to run a complete Monte Carlo simulation for a single test type (e.g., t-test) and a single dependency structure (e.g., AR(1)) across defined dependency strengths, outputting a table of observed error rates vs. nominal alpha (0.05).

**Acceptance Scenarios**:

1. **Given** a public dataset with continuous variables and a configured null-hypothesis scenario, **When** the system injects AR(1) dependency with correlation $r=0.3$ and runs 10,000 Monte Carlo replications of a t-test, **Then** the output must report the observed Type I error rate with a [deferred] Clopper-Pearson exact confidence interval.
2. **Given** the same dataset and null scenario, **When** the system varies $r$ across $\{0, 0.1, 0.2, 0.3, 0.5\}$, **Then** the output must show a monotonic increase in error rates (verified by a trend test with p < 0.05) as $r$ increases.

---

### User Story 2 - Cross-Test and Structure Comparison (Priority: P2)

A researcher needs to compare the robustness of different statistical tests (t-test, ANOVA, chi-squared) across different dependency structures (temporal, spatial, hierarchical) to determine which tests are most vulnerable.

**Why this priority**: This extends the findings from US-1 to provide actionable comparative guidance. It allows the researcher to see if certain tests are more robust than others under specific real-world data conditions.

**Independent Test**: The system must run the simulation for all three test types and at least two dependency structures, producing a comparative plot or table showing error rate curves for each combination.

**Acceptance Scenarios**:

1. **Given** the results from US-1 for multiple test types, **When** the system aggregates the error rates by test type and dependency structure, **Then** it must generate a visualization (e.g., line plot) where the x-axis is dependency strength and the y-axis is observed Type I error rate, with separate lines for each test.
2. **Given** the comparative data, **When** the system identifies the point where error rate exceeds $\alpha=0.10$, **Then** it must report the specific dependency strength threshold for each test type.

---

### User Story 3 - Power Analysis under Dependency (Priority: P3)

A researcher needs to understand how statistical power is affected when non-independence is present, specifically whether dependency reduces the ability to detect true effects.

**Why this priority**: While Type I error is the primary concern for validity, power is critical for study design. This provides a complete picture of the inferential costs of violating independence. It is secondary because the primary risk to validity is false positives.

**Independent Test**: The system must inject true effects (e.g., mean shifts) into the dependency-injected data and measure the proportion of significant results, comparing it to the independent baseline.

**Acceptance Scenarios**:

1. **Given** a dataset with injected true effect (mean shift $\delta=1.0\sigma$) and AR(1) dependency ($r=0.3$), **When** the system runs 10,000 replications of a t-test, **Then** it must report the observed statistical power.
2. **Given** power results for $r=0$ and $r=0.3$, **When** the system compares them, **Then** it must quantify the percentage reduction in power due to the dependency.

---

### Edge Cases

- What happens when a dataset is too small to support the required Monte Carlo replications or dependency injection (e.g., $N < 20$)?
- How does the system handle datasets where the null hypothesis cannot be cleanly constructed (e.g., all variables are highly correlated)?
- What is the behavior when the injected dependency structure creates a distribution that violates the normality assumption of the t-test/ANOVA beyond just non-independence?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse a set of public datasets from UCI Machine Learning Repository or OpenML that contain continuous or categorical variables suitable for t-tests, ANOVA, or chi-squared tests (See US-1).
- **FR-002**: System MUST construct a null hypothesis by first injecting the controlled dependency structure into the original data, and THEN applying random permutation of labels or selection of independent variables to ensure a known ground truth of no effect while preserving the dependency structure (See US-1).
- **FR-003**: System MUST inject controlled dependency structures via block bootstrap (hierarchical), AR(1) resampling (temporal), and spatial kernel smoothing (spatial, restricted to datasets with explicit spatial coordinates or a validated feature-space clustering proxy) with tunable strength parameters (See US-1).
- **FR-004**: System MUST execute Monte Carlo simulations with at least 10,000 replications per test-configuration combination to ensure error rate precision within $\pm 0.5\%$ (See US-1, US-2).
- **FR-005**: System MUST calculate and report observed Type I error rates and statistical power for t-tests, one-way ANOVA, and chi-squared tests across all dependency configurations (See US-1, US-2, US-3).
- **FR-006**: System MUST generate comparative visualizations (e.g., error rate curves with 95% Clopper-Pearson CIs) plotting error rate/power against dependency strength for each test type (See US-2).
- **FR-007**: System MUST implement a sensitivity analysis that sweeps the dependency strength threshold over the concrete set $r \in \{0, 0.1, 0.2, 0.3, 0.5\}$ to report how error rates vary, ensuring threshold robustness (See US-1, US-2).
- **FR-008**: System MUST run the entire analysis pipeline on a CPU-only environment (specifically GitHub Actions ubuntu-latest, 2-core, 7GB RAM) ensuring execution of 10,000+ replications per configuration completes within 6 hours (See Assumptions).

### Key Entities

- **Dataset**: A public dataset containing variables suitable for statistical testing, with metadata on sample size and variable types.
- **DependencyConfiguration**: A definition of the dependency structure type (temporal, spatial, hierarchical) and its strength parameter (e.g., correlation coefficient $r$).
- **SimulationResult**: The outcome of a single Monte Carlo replication, including the p-value and whether it was significant.
- **AggregatedMetric**: The calculated Type I error rate or statistical power for a specific test, dataset, and dependency configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Observed Type I error rate is measured against the nominal alpha level (0.05) across dependency strengths to quantify inflation (See US-1).
- **SC-002**: Statistical power is measured against the theoretical power expected under independence to quantify power loss (See US-3).
- **SC-003**: Error rate estimates are measured against a precision target of $\pm 0.5\%$ (derived from 10,000+ replications) to ensure reliability (See US-1).
- **SC-004**: Computational feasibility is measured against the constraint of completing 10,000+ replications per configuration within 6 hours on a 2-core, 7GB RAM runner (See Assumptions).
- **SC-005**: Threshold sensitivity is measured by the variation in error rates across the swept dependency strength set $\{0, 0.1, 0.2, 0.3, 0.5\}$ to ensure robustness (See US-1, US-2).

## Assumptions

- The public datasets selected from UCI/OpenML contain sufficient sample sizes ($N \ge 50$) to support the injection of dependency structures and Monte Carlo replications without exhausting memory.
- The "null hypothesis" can be reliably constructed for the selected datasets via random permutation of labels or by identifying pairs of variables that are empirically uncorrelated in the original data, provided dependency is injected prior to permutation.
- The computational cost of injecting dependency structures (block bootstrap, AR(1) resampling) for a sufficiently large number of replications fits within the 7 GB RAM and 6-hour time limit of a free-tier GitHub Actions runner (ubuntu-latest, 2-core, 7GB RAM). IF implemented using vectorized numpy operations or parallel processing.
- The standard `scipy.stats` and `statsmodels` libraries in Python are sufficient for performing t-tests, ANOVA, and chi-squared tests without requiring GPU acceleration or specialized high-performance computing libraries, provided the simulation loop is optimized.
- The dependency injection methods (block bootstrap, AR(1), spatial kernel) are appropriate approximations for the types of non-independence found in general public datasets, even if the exact real-world structure is unknown.
- The nominal alpha level for significance testing is fixed at 0.05 for all experiments.