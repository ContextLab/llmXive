# Feature Specification: Assessing the Validity of p-Values in High-Dimensional Data

**Feature Branch**: `[001-assess-p-value-validity]`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How do standard p-values from common hypothesis tests deviate from their theoretical uniform distribution when applied to high-dimensional data with violated independence and normality assumptions?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Synthetic Data Generation with Controlled Correlation and Distribution Violations (Priority: P1)

As a researcher, I want to generate synthetic high-dimensional datasets with precisely controlled correlation structures, sample-to-dimension ratios, and distributional violations (heavy-tailed or skewed), so that I can systematically test p-value validity under known ground-truth null conditions.

**Why this priority**: Without controlled synthetic data generation that explicitly violates both independence and normality assumptions, no empirical analysis of p-value behavior is possible. This is the foundational capability that enables all subsequent testing.

**Independent Test**: Can be fully tested by verifying that generated data matrices have the exact correlation structure specified (within numerical tolerance) and that the null hypothesis is true by construction (no mean differences), while the distributional shape matches the target (e.g., t-distribution with df=3).

**Acceptance Scenarios**:

1. **Given** a correlation matrix with specified $\rho \in \{0, 0.1, 0.3, 0.5, 0.7, 0.9\}$ and a target distribution (e.g., Normal, t-distribution with df=3, or Skewed Normal), **When** data is generated for $n \in \{50, 100, 200, 500\}$ samples and $p \in \{500, 1000, 2000, 5000\}$ features, **Then** the empirical correlation matrix matches the target within numerical tolerance (absolute difference $\leq 0.01$ for all pairwise correlations) and the empirical distribution matches the target distribution.
2. **Given** a null scenario with no true effect, **When** synthetic data is generated, **Then** all features follow the same distribution (no systematic mean differences) to ensure ground-truth null validity.

---

### User Story 2 - Hypothesis Test Execution and p-Value Collection (Priority: P2)

As a researcher, I want to apply standard t-tests and F-tests to the synthetic null data and collect all resulting p-values, so that I can empirically observe their distribution under violated assumptions.

**Why this priority**: This is the core analysis step that produces the primary data for evaluating p-value validity. Without test execution, no deviation can be measured.

**Independent Test**: Can be fully tested by running hypothesis tests on a known null dataset and verifying that p-values are collected for every test without missing values.

**Acceptance Scenarios**:

1. **Given** a synthetic dataset with $p$ features and known null ground truth, **When** t-tests and F-tests are applied to each feature (comparing to theoretical mean), **Then** exactly $p$ p-values are collected for each test type with no missing values.
2. **Given** 1000 simulation iterations per setting, **When** hypothesis tests are executed, **Then** all iterations complete successfully without runtime errors on CPU-only infrastructure.

---

### User Story 3 - P-Value Distribution Analysis and Deviation Quantification (Priority: P3)

As a researcher, I want to analyze the collected p-values using Kolmogorov-Smirnov statistics and QQ-plots against a Gold Standard (permutation-based) reference, so that I can quantify the degree of anti-conservative bias across different correlation structures and $p/n$ ratios.

**Why this priority**: This delivers the primary research output—quantified evidence of p-value deviation—but depends on completed data generation and test execution.

**Independent Test**: Can be fully tested by running the analysis on a fixed dataset and verifying that KS statistics and QQ-plots are produced with correct statistical calculations comparing standard tests to the permutation reference.

**Acceptance Scenarios**:

1. **Given** a collection of p-values from null hypothesis tests, **When** Kolmogorov-Smirnov statistics are computed against the permutation-based reference distribution, **Then** the KS statistic is reported with the exact numerical value (not just "significant" or "non-significant").
2. **Given** multiple correlation thresholds tested, **When** sensitivity analysis is performed, **Then** the KS statistic is reported for each threshold in $\{\rho = 0.0, 0.1, 0.3, 0.5, 0.7, 0.9\}$ to show how deviation varies.

---

### Edge Cases

- What happens when $p/n > 10$ (extreme high-dimensional regime where $p=5000, n=50$)?
- How does the system handle numerical instability when correlation approaches perfect ($\rho = 0.99$)?
- What happens when the t-test encounters singular covariance matrices in high dimensions?
- How does the system handle missing values if the public dataset download fails?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate synthetic high-dimensional datasets with correlation structures specified by $\rho \in \{0, 0.1, 0.3, 0.5, 0.7, 0.9\}$, sample sizes $n \in \{50, 100, 200, 500\}$, dimensions $p \in \{500, 1000, 2000, 5000\}$, and distributional violations (heavy-tailed or skewed) (See US-1)
- **FR-002**: System MUST apply standard t-tests and F-tests to each feature under null scenarios where ground truth is known to be no effect (See US-2)
- **FR-003**: System MUST collect exactly $p$ p-values per simulation iteration with no missing values (See US-2)
- **FR-004**: System MUST compute p-values using a permutation test (respecting the correlation structure) to serve as a Gold Standard reference, and compute the Kolmogorov-Smirnov statistic comparing the standard test p-values against this permutation reference distribution (See US-3)
- **FR-005**: System MUST produce QQ-plots of standard test p-values against the permutation reference distribution for visual inspection of deviation (See US-3)
- **FR-007**: System MUST perform sensitivity analysis sweeping the correlation threshold over $\rho \in \{0, 0.1, 0.3, 0.5, 0.7, 0.9\}$ and report how the KS statistic varies across this range (See US-3)
- **FR-008**: System MUST run all computations using CPU-only methods (scipy, numpy, matplotlib) without requiring GPU/CUDA or 8-bit/4-bit quantization (See US-1)
- **FR-009**: System MUST detect when $p/n > 10$ or when the covariance matrix is near-singular (condition number > $10^{12}$) and apply regularization (adding diagonal term $\epsilon = 10^{-6}$) or raise a specific error code `ERR_HIGH_DIMENSIONAL_INSTABILITY` (See Edge Cases)

### Key Entities *(include if feature involves data)*

- **SyntheticDataset**: Represents generated high-dimensional data with attributes including correlation structure ($\rho$), sample size ($n$), feature count ($p$), distribution type, and null hypothesis status (true/false)
- **PValueCollection**: Represents the set of p-values collected from hypothesis tests, with attributes including KS statistic (vs permutation), test count, and correlation threshold

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Kolmogorov-Smirnov statistic for p-value distribution deviation is measured against the permutation-based reference distribution (See US-3)
- **SC-002**: P-value anti-conservative bias magnitude is measured against the deviation observed between standard tests and the permutation reference (See US-3)
- **SC-004**: Computational feasibility is measured against the GitHub Actions free-tier constraint of 2 CPU cores, ~7 GB RAM, and ≤6 hours runtime (See US-1)
- **SC-005**: Sample-size/power adequacy is measured against a simulation iteration count per setting that achieves statistical power ≥ 0.8 to detect a KS statistic deviation > 0.05 (See US-2)

## Assumptions

- The public high-dimensional dataset (e.g., UCI gene expression subsets) will be accessible via `wget` and will remain available throughout the project duration
- Synthetic data generation using numpy random number generation will produce sufficiently representative correlation structures and distributional violations for the research question
- The GitHub Actions free-tier runner will provide consistent CPU performance (2 cores, ~7 GB RAM) without significant variance between runs
- Standard t-tests and F-tests from scipy.stats will handle high-dimensional data without numerical overflow or underflow for the specified parameter ranges
- The permutation test implementation will correctly respect the correlation structure of the data to provide a valid Gold Standard
- All statistical findings will be framed as associational observations about p-value behavior under violated assumptions, not as causal claims about hypothesis test validity
- The power limitation of 1000 iterations per setting is acknowledged as a constraint; results should be interpreted with appropriate uncertainty bounds
- When correlation structures approach perfect ($\rho > 0.95$), numerical instability may occur in matrix operations; the system will use regularization (adding small diagonal term $\epsilon = 10^{-6}$) to ensure invertibility