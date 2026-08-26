# Feature Specification: Normalized Gaps Between Consecutive Squarefree Numbers

**Feature Branch**: `001-normalized-squarefree-gaps`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Do the gaps between consecutive squarefree integers, after normalizing by their empirical mean, follow an exponential distribution?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Squarefree Gaps and Compute Normalized Statistics (Priority: P1)

As a researcher, I want to generate the sequence of squarefree numbers up to a maximum limit $N$, compute the raw gaps between consecutive terms, and normalize these gaps by their empirical mean, so that I have the primary dataset required to test the exponential distribution hypothesis.

**Why this priority**: This is the foundational step. Without the correctly generated and normalized gap data, no statistical testing or visualization can occur. It represents the core data acquisition and transformation pipeline.

**Independent Test**: Can be fully tested by running the sieve algorithm for a small $N$ (e.g., $10^4$), verifying the count of squarefree numbers against known values, and confirming the mean of normalized gaps is exactly 1.0 within floating-point tolerance.

**Acceptance Scenarios**:

1. **Given** a maximum integer limit $N=10,000$, **When** the sieve algorithm runs, **Then** the system outputs a list of gaps $\Delta_i$ and a normalized list $g_i = \Delta_i / \bar{\Delta}$ where the mean of $g_i$ is $1.0 \pm 10^{-9}$.
2. **Given** the computed list of normalized gaps, **When** the system calculates the sum of all $g_i$, **Then** the result equals the count of gaps (proving normalization is correct).

---

### User Story 2 - Perform Statistical Goodness-of-Fit Testing (Priority: P2)

As a researcher, I want to perform a one-sample Kolmogorov–Smirnov (KS) test comparing the empirical distribution of normalized gaps against the standard exponential distribution (rate=1), so that I can quantitatively assess the hypothesis that the gaps are exponentially distributed.

**Why this priority**: This is the primary scientific inquiry. It directly answers the research question with a statistical metric (KS statistic and p-value) rather than just visual inspection.

**Independent Test**: Can be fully tested by running the KS test on a synthetic dataset known to be exponential (should yield high p-value) and a dataset known to be uniform (should yield low p-value), verifying the logic of the test implementation.

**Acceptance Scenarios**:

1. **Given** the normalized gap dataset for $N=10^6$, **When** the KS test is executed against the exponential CDF, **Then** the system outputs a KS statistic value and a p-value.
2. **Given** a dataset of size $M$ where $M > 100$, **When** the KS test is run, **Then** the system correctly handles the case where the p-value is exactly 0.0 or 1.0 (edge cases of the CDF) without crashing.

---

### User Story 3 - Generate Convergence Analysis and Visualizations (Priority: P3)

As a researcher, I want to generate comparative plots (Empirical CDF vs. Exponential CDF, QQ-plot) and a convergence analysis chart showing the KS statistic and p-value as a function of $\log N$ for multiple cutoffs ($10^6, 5\times10^6, 10^7$), so that I can visually and quantitatively verify the asymptotic behavior of the distribution.

**Why this priority**: While the statistical test provides a number, the visualizations and convergence analysis provide the necessary context to interpret the results and confirm the "random-like" heuristic across scales.

**Independent Test**: Can be fully tested by generating plots for a fixed $N$ and verifying that the plots are rendered as image files (PNG/SVG) and that the convergence chart correctly plots the trend line of KS statistics.

**Acceptance Scenarios**:

1. **Given** the results from three different $N$ values, **When** the convergence analysis script runs, **Then** it produces a single plot with the KS statistic on the y-axis and $\log N$ on the x-axis.
2. **Given** the normalized gaps for a specific $N$, **When** the QQ-plot is generated, **Then** the points lie approximately along the line $y=x$ if the hypothesis holds, or deviate systematically if it does not.

### Edge Cases

- What happens when $N$ is too small to generate a statistically significant sample (e.g., $N < 1000$)? The system should log a warning and skip the KS test or flag the p-value as unreliable.
- How does the system handle memory limits if $N$ is increased beyond the available RAM (e.g., $N > 10^8$ on a 7GB runner)? The sieve implementation must be optimized to stream or use bit-arrays to stay within ~2GB RAM.
- What if the empirical mean of gaps is exactly zero (impossible mathematically but possible via bug)? The normalization step must include a guard against division by zero.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a linear sieve (O(N log log N)) to identify squarefree numbers up to a user-defined limit $N$ without requiring external data sources. (See US-1)
- **FR-002**: System MUST calculate the raw gaps $\Delta_i = s_{i+1} - s_i$ and the normalized gaps $g_i = \Delta_i / \bar{\Delta}$ for the identified sequence. (See US-1)
- **FR-003**: System MUST perform a one-sample Kolmogorov–Smirnov test comparing the empirical CDF of $\{g_i\}$ against the standard exponential distribution (rate=1). (See US-2)
- **FR-004**: System MUST generate visualizations including an Empirical CDF vs. Exponential CDF plot and a QQ-plot for each tested $N$. (See US-3)
- **FR-005**: System MUST produce a convergence analysis plot showing the KS statistic and p-value as a function of $\log N$ for at least three distinct cutoff values ($10^6, 5\times10^6, 10^7$). (See US-3)

### Key Entities

- **SquarefreeSequence**: An ordered list of integers $s_i$ where each $s_i$ is squarefree.
- **GapDataset**: A collection of raw gaps $\Delta_i$ and normalized gaps $g_i$ associated with a specific cutoff $N$.
- **TestResult**: A record containing the KS statistic, p-value, and cutoff $N$ for a specific run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The mean of the normalized gap distribution is measured against the theoretical value of 1.0 to verify correct normalization. (See US-1)
- **SC-002**: The KS statistic and p-value are measured against the critical values for the exponential distribution to determine if the null hypothesis (exponentiality) is rejected or retained. (See US-2)
- **SC-003**: The trend of the KS statistic is measured against the asymptotic expectation that it decreases (or stabilizes) as $N$ increases, indicating convergence to the limiting distribution. (See US-3)
- **SC-004**: The visual alignment of the QQ-plot points against the line $y=x$ is measured against the standard visual criteria for exponential distribution fit. (See US-3)
- **SC-005**: The total memory usage of the sieve and analysis pipeline is measured against the 7 GB RAM limit of the GitHub Actions runner to ensure feasibility. (See US-1)

## Assumptions

- **Assumption about data source**: The integer range $\{1, \dots, N\}$ can be generated deterministically on the fly; no external dataset download is required or assumed.
- **Assumption about computational resources**: The linear sieve algorithm for $N=10^7$ will complete within the 6-hour GitHub Actions time limit and utilize less than 2 GB of RAM.
- **Assumption about statistical validity**: The sample sizes generated (approx. $6/\pi^2 \times 10^7 \approx 6 \times 10^6$ points) are sufficient for the Kolmogorov–Smirnov test to have adequate power to detect deviations from exponentiality.
- **Assumption about methodology**: The "random thinning" heuristic implies that the limiting distribution of normalized gaps is the standard exponential distribution (rate=1), serving as the ground truth for the KS test.
- **Assumption about software environment**: The `scipy` library (specifically `scipy.stats.kstest`) and `matplotlib` are available in the standard Python environment on the GitHub Actions runner without GPU acceleration.
