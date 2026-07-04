# Feature Specification: Residue Distribution of Euler's Totient Function Modulo Small Primes

**Feature Branch**: `001-residue-distribution-totient`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Do the residues of Euler's totient function φ(n) modulo a fixed small prime p (e.g., p ∈ {3, 5, 7, 11}) appear uniformly distributed among the residue classes as n ranges over the first several million positive integers?"

## User Scenarios & Testing

### User Story 1 - Compute Totient Residues for Large Range (Priority: P1)

The researcher MUST be able to generate the sequence of Euler's totient function values $\phi(n)$ for all integers $n$ from 1 to $N$ (where $N$ is a deferred upper bound) and compute their residues modulo a specified small prime $p \in \{3, 5, 7, 11\}$.

**Why this priority**: This is the foundational data generation step. Without accurate, high-volume computation of residues, no statistical analysis or hypothesis testing can occur. It is the minimum viable product for the empirical investigation.

**Independent Test**: This can be fully tested by running the sieve algorithm on a sample subset (e.g., $n \le [deferred]$), verifying the output against known $\phi(n)$ values from mathematical tables, and confirming the residue counts match the expected uniform distribution for small $N$ where theoretical bias is negligible.

**Acceptance Scenarios**:

1. **Given** the system is initialized with prime $p=3$ and $N=100$, **When** the computation runs, **Then** the system outputs a frequency table of residues $\{0, 1, 2\}$ with a total count of 100 entries.
2. **Given** the system processes $n=1$ to $100$, **When** the residues modulo 5 are calculated, **Then** the specific values for $n=1, 2, 3, 4, 5$ (residues 1, 2, 2, 1, 0) match the mathematically correct values of $\phi(n) \pmod 5$.
3. **Given** the memory constraint of 7 GB RAM, **When** the linear sieve processes $n=N$, **Then** the peak memory usage remains within the acceptable limit, ensuring the job does not fail on the free-tier runner.

---

### User Story 2 - Perform Statistical Goodness-of-Fit Tests (Priority: P2)

The researcher MUST be able to apply a Chi-squared ($\chi^2$) goodness-of-fit test with Monte Carlo p-value estimation to the residue frequency distributions to determine if they deviate significantly from a uniform distribution, replacing the invalid Kolmogorov–Smirnov test for discrete data.

**Why this priority**: Data generation alone is descriptive; statistical testing transforms the data into evidence. This step directly addresses the research question regarding uniformity versus bias, using a method sound for discrete distributions.

**Independent Test**: This can be tested by feeding the system a synthetic dataset of residues that is known to be perfectly uniform (or known to be biased) and verifying that the $\chi^2$ test statistic and p-value (computed via Monte Carlo simulation or exact method) align with theoretical expectations for those specific discrete distributions.

**Acceptance Scenarios**:

1. **Given** a dataset of $N$ residues modulo 3 that are perfectly uniform, **When** the $\chi^2$ test (with Monte Carlo estimation) is executed, **Then** the resulting p-value is $> 0.05$ (indicating no significant deviation from uniformity), acknowledging the discrete nature of the data.
2. **Given** a dataset of residues modulo 7 where class '' is artificially inflated by [deferred], **When** the $\chi^2$ test is executed, **Then** the resulting p-value is $< 0.05$ (indicating a significant deviation from the uniform distribution).
3. **Given** the results for prime $p=11$, **When** the tests are completed, **Then** the system outputs a structured report containing the test statistic, degrees of freedom, and p-value for the $\chi^2$ test.

---

### User Story 3 - Visualize and Compare Against Theoretical Bounds (Priority: P3)

The researcher MUST be able to generate bar plots comparing observed residue frequencies against the uniform expectation and overlay QQ-plots for the $\chi^2$ residuals, while contextualizing the results against the error bounds provided in the referenced literature (Lebowitz-Lockard et al.; Pollack & Roy, 2024).

**Why this priority**: Visualization is critical for human interpretation of the statistical output, and comparison with theoretical bounds validates the empirical findings against established analytic number theory results.

**Independent Test**: This can be tested by generating plots from a known dataset and verifying that the "Uniform Expectation" line matches the calculated $N/p$ value and that the error bounds from the cited papers are correctly annotated on the visualization.

**Acceptance Scenarios**:

1. **Given** the frequency counts for $p=5$, **When** the bar plot is generated, **Then** the plot displays a bar for each residue class and a horizontal reference line at height $N/5$.
2. **Given** the p-values from the statistical tests, **When** the report is generated, **Then** the system explicitly states whether the deviation falls within the theoretical error bounds described in the 2021 and 2024 papers.
3. **Given** the execution environment, **When** the visualization script runs, **Then** the output images are saved in a standard format (e.g., PNG) with a resolution sufficient for publication review (minimum 300 DPI or equivalent vector quality).

### Edge Cases

- **Boundary Condition**: What happens if the user requests a prime $p$ outside the set $\{3, 5, 7, 11\}$? The system must reject the request with a clear error message indicating only the specified primes are supported in this phase.
- **Error Scenario**: How does the system handle a scenario where the linear sieve fails to compute $\phi(n)$ for a specific $n$ due to an overflow or logic error? The system must halt execution and log the specific $n$ where the failure occurred, rather than silently producing incorrect data.
- **Statistical Edge**: What if the sample size $N$ is too small for the $\chi^2$ approximation to hold (e.g., expected count $< 5$)? The system must issue a warning or switch to an exact test (or Monte Carlo simulation) if the expected count in any bin drops below the standard threshold for statistical validity.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute $\phi(n)$ for all $n \in [1, N]$ using a linear sieve algorithm with arbitrary-precision integer arithmetic (BigInt) to ensure $O(N)$ arithmetic operations while maintaining bit-complexity integrity (See US-1).
- **FR-002**: System MUST calculate the residue $\phi(n) \pmod p$ for each $n$ and aggregate counts for every residue class $\{0, \dots, p-1\}$ for $p \in \{3, 5, 7, 11\}$ (See US-1).
- **FR-003**: System MUST perform a Chi-squared ($\chi^2$) goodness-of-fit test against the uniform distribution hypothesis for each prime $p$. If any expected bin count is $< 5$, the system MUST automatically switch to an exact test or Monte Carlo simulation (See US-2).
- **FR-004**: System MUST generate a visualization report containing the $\chi^2$ test statistic, p-value (computed via Monte Carlo or exact method), and degrees of freedom for each prime $p$ (See US-2).
- **FR-005**: System MUST generate visualization artifacts (bar plots and residual QQ-plots) that overlay observed frequencies with the theoretical uniform expectation $N/p$ (See US-3).
- **FR-006**: System MUST output a structured summary report containing the test statistics, p-values, and a binary pass/fail flag based on the $\alpha = 0.05$ significance threshold (See US-2).
- **FR-007**: System MUST enforce a memory limit check during execution to ensure peak usage remains within acceptable bounds, as defined by the resource constraints outlined in the study design., failing gracefully if usage reaches $\ge 90\%$ of the limit (See US-1).

### Key Entities

- **N**: The deferred upper bound integer defining the range of computation $[1, N]$. This is a configurable input parameter.
- **ResidueDataset**: Represents the collection of computed residues $\{\phi(n) \pmod p \mid 1 \le n \le N\}$ for a specific prime $p$. Attributes include `prime_modulus`, `total_count`, and `frequency_map`.
- **StatisticalResult**: Represents the output of a hypothesis test. Attributes include `test_type` ($\chi^2$), `test_statistic`, `p_value`, `degrees_of_freedom`, `method` (asymptotic/Monte Carlo/Exact), and `uniformity_hypothesis` (True/False).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The correctness of the computed $\phi(n)$ values is measured against known mathematical values for $n \le N$ (See US-1).
- **SC-002**: The validity of the statistical inference is measured by the consistency of p-values generated from synthetic uniform/biased datasets against theoretical expectations for discrete distributions (See US-2).
- **SC-003**: The computational feasibility is measured by the total wall-clock time required to process $N=5,000,000$ (for the test case), which must be $\le 1$ hour on a standard GitHub Actions runner (See US-1).
- **SC-004**: The methodological rigor is measured by the presence of $\chi^2$ test results (with appropriate Monte Carlo/Exact fallback) for every prime $p$, ensuring robustness against the limitations of a single test statistic (See US-2).
- **SC-005**: The interpretability of results is measured by the successful generation of visualization artifacts that clearly distinguish between observed frequencies and the uniform baseline (See US-3).

## Assumptions

- **Assumption about data source**: The linear sieve algorithm will use arbitrary-precision integers (BigInt) to compute $\phi(n)$ for all $n \le N$ to prevent overflow artifacts and comply with Constitution Principle VI, even if standard 64-bit integers are likely sufficient for the specific $N$ range.
- **Assumption about statistical validity**: The sample size $N$ is sufficiently large for the Chi-squared approximation to hold for all tested primes $p \in \{3, 5, 7, 11\}$, as the expected count per bin ($N/p$) will be $\ge 5$, far exceeding the standard rule of thumb. If $N/p < 5$, the system will use an exact/Monte Carlo method.
- **Assumption about compute environment**: The GitHub Actions free-tier runner provides sufficient CPU throughput (2 cores) to complete the $O(N)$ sieve (with BigInt overhead) and statistical tests within the 6-hour job limit, provided no heavy model training or GPU operations are attempted.
- **Assumption about theoretical comparison**: The error bounds and asymptotic formulas cited in Lebowitz-Lockard (2021) and Pollack & Roy (2024) are applicable to the finite range $n \le N$ and can be used as a reference for "expected" deviations.
- **Assumption about multiplicity**: Since multiple primes ($p=3, 5, 7, 11$) are tested, the analysis will treat the p-values independently for the purpose of this exploratory study, though a formal Bonferroni correction (dividing $\alpha$ by 4) is noted as a potential sensitivity analysis if the research question shifts to a strict family-wise error rate.