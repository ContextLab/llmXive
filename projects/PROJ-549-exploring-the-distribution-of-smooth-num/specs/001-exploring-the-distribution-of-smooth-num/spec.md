# Feature Specification: Exploring the Distribution of Smooth Numbers in Short Intervals

**Feature Branch**: `001-exploring-the-distribution-of-smooth-numbers`  
**Created**: 2026-05-28  
**Status**: Draft  
**Input**: User description: "Exploring the Distribution of Smooth Numbers in Short Intervals"

## User Scenarios & Testing

### User Story 1 - Generate and Validate Prime Sieve Data (Priority: P1)

The researcher needs a computationally efficient, memory-safe method to generate all prime numbers up to $10^9$ to serve as the basis for factorization, ensuring the pipeline runs within the available RAM and CPU time constraints of the CI environment. This stage is allocated a maximum of 120 minutes; the output is treated as a pre-computed artifact for subsequent stages.

**Why this priority**: Without a reliable prime list, the core factorization logic cannot execute. This is the foundational data layer; if the sieve fails or exceeds memory, the entire project halts.

**Independent Test**: Can be fully tested by executing the sieve generation script in isolation and verifying the count of primes against the known value of $\pi(10^9) = 50,847,534$ within a 1-second tolerance, while monitoring peak memory usage to ensure it remains within acceptable system limits.

**Acceptance Scenarios**:

1. **Given** a standard GitHub Actions runner with CPU cores and 7 GB RAM, **When** the segmented sieve script executes to generate primes up to $10^9$, **Then** the script completes within 120 minutes and outputs a file containing a large number of primes.
2. **Given** the generated prime list, **When** a random subset of primes is sampled, **Then** every sampled number is confirmed to be prime (no composites) and no duplicates exist in the list.

---

### User Story 2 - Compute Smooth Number Density Across Parameter Grid (Priority: P2)

The researcher needs to systematically enumerate integers in short intervals $[x, x+h]$ for a defined grid of $y$ (smoothness bound), $x$ (start point), and $h$ (interval length) to calculate the density of $y$-smooth numbers, enabling the empirical measurement of distribution variance. This stage is allocated a maximum of 240 minutes (4 hours), assuming the prime sieve is pre-generated.

**Why this priority**: This is the core research engine. It directly addresses the research question by generating the raw data (counts and densities) required for statistical analysis and comparison against theoretical bounds.

**Independent Test**: Can be fully tested by running the computation on a fixed, small subset of the parameter grid (e.g., $x=10^6, y=100$) and verifying that the calculated smooth number count matches a manually verified or brute-force calculated ground truth for that specific interval with [deferred] error.

**Acceptance Scenarios**:

1. **Given** a specific parameter set ($x=10^7, y=1000, h=x^{0.5}$), **When** the enumeration script processes the interval $[x, x+h]$, **Then** the script correctly identifies every integer in the range as $y$-smooth or not based on its prime factors, and outputs a count that matches the expected value with [deferred] error (accounting for potential edge-case definition differences).
2. **Given** the full parameter grid ($y \in \{100, 1000, 10000\}$, $x \in \{10^6, 10^7, 10^8, 10^9\}$, $h \in \{x^{0.1}, x^{0.3}, x^{0.5}, x^{0.7}, x^{0.9}\}$), **When** the script runs across multiple random starting positions per configuration, **Then** it generates a complete dataset of density measurements without crashing due to memory or time limits (completing within 240 minutes).

---

### User Story 3 - Statistical Analysis and Visualization of Density Trends (Priority: P3)

The researcher needs to fit a power-law model to the observed density data, perform goodness-of-fit tests against the Dickman function, and generate visualizations to interpret the relationship between interval length and smooth number density. This stage is allocated a maximum of 120 minutes.

**Why this priority**: This transforms raw data into scientific insight, allowing the researcher to validate or refute the hypothesis regarding finite-scale deviations from asymptotic predictions.

**Independent Test**: Can be fully tested by running the analysis script on a pre-generated synthetic dataset where the power-law exponent is known, verifying that the regression recovers the exponent within an acceptable margin of error and that the visualization renders correctly.

**Acceptance Scenarios**:

1. **Given** the complete density dataset from User Story 2, **When** the power-law regression ($\rho(h) = c \cdot h^\beta$) is executed, **Then** the model converges and outputs a coefficient $\beta$ with a standard error, and the $R^2$ value is calculated for each $y$-group.
2. **Given** the observed density distributions, **When** the Chi-Square Goodness-of-Fit test is applied against the theoretical prediction derived from the Dickman function for each $y$-group, **Then** the script outputs a p-value for each test, and a visualization plot is generated showing the observed density curves with confidence intervals overlaid on the theoretical expectation.

### Edge Cases

- **What happens when** an interval $[x, x+h]$ contains no $y$-smooth numbers? The system must record a non-zero density. and not crash during division or statistical aggregation.
- **How does the system handle** the boundary condition where $x+h$ exceeds $10^9$ (if the grid definition allows)? The system must clamp $x+h$ to the maximum supported limit ($10^9$) or skip the configuration if the prime sieve does not extend that far, logging a warning.
- **What happens when** the factorization of a number requires a prime larger than $y$ but smaller than the number itself? The system must correctly identify the number as *not* $y$-smooth and increment the non-smooth count.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement a segmented sieve of Eratosthenes to generate all primes up to $10^9$ using a memory footprint within reasonable system constraints (See US-1).
- **FR-002**: The system MUST factorize every integer in a defined interval $[x, x+h]$ using trial division against the subset of the prime list ≤ y to determine $y$-smoothness (See US-2).
- **FR-003**: The system MUST compute the density $\rho = \text{count} / h$ for each interval and aggregate results across multiple random starting positions per parameter configuration (See US-2).
- **FR-004**: The system MUST fit a power-law model $\rho(h) = c \cdot h^\beta$ to the aggregated density data using ordinary least squares regression (See US-3).
- **FR-005**: The system MUST perform a Chi-Square Goodness-of-Fit test comparing the observed counts of smooth numbers against the expected counts derived from the Dickman function for each $y$-group (See US-3).
- **FR-006**: The system MUST generate a visualization containing density vs. interval length curves with 95% confidence intervals for each $y$-value, saving the output as a PNG file (See US-3).

### Key Entities

- **PrimeList**: A sorted, immutable collection of prime numbers up to $10^9$, used as the reference for factorization.
- **IntervalConfig**: A tuple defining the parameters for a single measurement run: $(x, y, h, \text{start\_offset})$.
- **DensityMeasurement**: A record containing the interval parameters, the count of $y$-smooth numbers found, the calculated density, and the timestamp of the measurement.
- **ModelFit**: A structured result containing the regression coefficients ($c, \beta$), standard errors, $R^2$ value, and the p-value from the Chi-Square test.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The power-law exponent $\beta$ is measured against the theoretical prediction (constant density $\beta=1$ or Hildebrand-Tenenbaum scaling) to determine if local scaling exists; success is defined as the measured $\beta$ being within 10% of the theoretical prediction OR the deviation being statistically significant (p < 0.05) (See US-3).
- **SC-002**: The goodness-of-fit of the observed distribution is measured against the theoretical expectation using the p-value from the Chi-Square test, with a significance threshold of $\alpha = 0.05$; success is defined as p > 0.05 (data consistent with theory) or p < 0.05 with a quantified effect size indicating significant deviation (See US-3).
- **SC-003**: The computational feasibility is measured against the CI constraint of a bounded total runtime (sieve, compute, and analysis phases) and a fixed RAM allocation., ensuring the full parameter grid completes without resource exhaustion (See US-1, US-2).
- **SC-004**: The variance of density estimates is measured across multiple random starting positions per configuration to quantify the stability of the distribution in short intervals (See US-2).

## Assumptions

- **Assumption about data**: The pre-computed prime tables from PrimePages are available and trusted, or the segmented sieve implementation is sufficient to generate primes up to a large magnitude within the 2-hour window on a 2-core CPU.
- **Assumption about methodology**: The distribution of $y$-smooth numbers in short intervals follows a power-law relationship at the scales tested ($x \le 10^9$) as a hypothesis to be tested, not an assumed truth; the Dickman function provides a valid theoretical baseline for expected counts.
- **Assumption about compute**: The factorization of integers up to $10^9$ using trial division against primes up to $y$ (where $y \le [deferred]$) is computationally feasible within the 6-hour limit, even with the overhead of a moderate set of random samples per configuration.
- **Assumption about statistical framing**: Since the study is observational (no random assignment of numbers), all conclusions regarding the relationship between interval length and density will be framed as associational, not causal, to avoid inferential overreach.
- **Assumption about threshold**: The power-law regression will use a standard least-squares approach without additional regularization, assuming the data is sufficiently linear in the log-log space for the tested range.
- **Assumption about sensitivity**: The choice of $h$ values as powers of $x$ ($x^{0.1}$ to $x^{0.9}$) is sufficient to capture the transition from local to asymptotic behavior; a sensitivity analysis sweeping the exponent $\alpha$ by $\pm 0.05$ is deferred to future work if the initial results are inconclusive.
- **Assumption about scientific context**: The power-law hypothesis is proposed to investigate potential local scaling anomalies in the context of open problems in analytic number theory (e.g., Montgomery's pair correlation conjecture), acknowledging that the theoretical expectation for large $h$ is constant density.