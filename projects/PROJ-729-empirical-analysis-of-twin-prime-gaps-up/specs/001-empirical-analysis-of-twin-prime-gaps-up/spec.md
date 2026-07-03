# Feature Specification: Empirical Analysis of Twin Prime Gaps up to 10⁹

**Feature Branch**: `001-twin-prime-gaps`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Empirical Analysis of Twin Prime Gaps up to 10⁹"

## User Scenarios & Testing

### User Story 1 - Generate and Normalize Twin Prime Gaps (Priority: P1)

**User Journey**: As a researcher, I want to generate the complete list of twin primes up to 10⁹ and compute their normalized gaps (Δₙ / log pₙ) so that I have the foundational dataset required to test the Cramér model hypothesis.

**Why this priority**: This is the core data acquisition step. Without this dataset, no statistical testing or visualization can occur. It is the minimum viable product (MVP) for the data pipeline.

**Independent Test**: Can be fully tested by running the generation script and verifying the output CSV contains the expected number of twin prime pairs and that the normalized gap column contains finite, positive values.

**Acceptance Scenarios**:

1. **Given** the system has access to a Python 3.11 environment with `primesieve` installed, **When** the script executes `generate_primes(0, 1_000_000_000)`, **Then** the script must successfully identify all twin prime pairs and output a CSV file containing a number of rows consistent with the theoretical expectation for the range (within a ±5% tolerance), with columns `p`, `p_next`, `delta`, and `normalized_gap`.
2. **Given** the sequence of twin prime pairs ordered by their first prime `pₙ`, **When** the normalization formula `delta / log(pₙ)` is applied where `delta` is defined as `p_{n+1} - pₙ` (the gap between the start of consecutive pairs), **Then** the resulting values must be finite and positive floats.
3. **Given** the project resource limits mandated by Constitution Principle VI, **When** the script processes the full prime list, **Then** the process must complete without exceeding 2 GiB of RAM usage or 45 minutes of wall-clock time.

---

### User Story 2 - Statistical Goodness-of-Fit Testing (Priority: P2)

**User Journey**: As a researcher, I want to perform Kolmogorov–Smirnov tests and generate QQ-plots comparing the empirical normalized gaps against the theoretical exponential distribution (λ=1) so that I can quantitatively assess the validity of the Cramér model.

**Why this priority**: This provides the primary statistical evidence for the research question. It transforms raw data into a testable conclusion regarding the hypothesis.

**Independent Test**: Can be tested by running the analysis module on the generated CSV and verifying that the KS test returns a p-value and that a PNG file containing the QQ-plot is generated with the empirical quantiles plotted against theoretical exponential quantiles.

**Acceptance Scenarios**:

1. **Given** the CSV of normalized gaps exists, **When** the `scipy.stats.kstest` function is applied against `expon(scale=1)`, **Then** the output must include a KS statistic and a p-value, saved to a JSON summary file. The system must explicitly document that this is a one-sample test on a self-normalized dataset, noting the potential for inflated p-values due to parameter estimation (mean forced to 1.0).
2. **Given** the set of normalized gaps, **When** the QQ-plot is generated, **Then** the plot must display the empirical quantiles on the y-axis and theoretical exponential quantiles on the x-axis, with a reference line `y=x` included for visual comparison.
3. **Given** the hypothesis that the data follows an exponential distribution, **When** the KS test is run, **Then** the system must handle the case where the p-value is < 0.05 (rejecting the null) or ≥ 0.05 (failing to reject) and explicitly flag this status in the summary report.

---

### User Story 3 - Localized Deviation Analysis near Powers of Two (Priority: P3)

**User Journey**: As a researcher, I want to analyze the distribution of normalized gaps specifically within windows surrounding powers of two (2^k ± 10⁴ for k=10..30) to detect any systematic deviations from the global exponential model in these specific numeric ranges.

**Why this priority**: This addresses the specific "systematic deviations" aspect of the research question. While important, it is an extension of the global analysis and depends on the success of the global dataset generation.

**Independent Test**: Can be tested by running the localized analysis script and verifying that a bar chart or summary table is produced showing the mean and variance of normalized gaps for each power-of-two window, compared against the theoretical expected value.

**Acceptance Scenarios**:

1. **Given** the global dataset of normalized gaps, **When** the script filters for primes within `[2^k - 10000, 2^k + 10000]` for `k` in `10..30`, **Then** the script must successfully compute the mean and variance for each window and save these metrics to a structured output file.
2. **Given** the computed window statistics, **When** a one-sample t-test is performed comparing each window's mean to the theoretical exponential mean (1.0), **Then** the system must output the t-statistic and p-value for each window, flagging any windows where the deviation is statistically significant (p < 0.05).
3. **Given** the results of the localized analysis, **When** the final report is generated, **Then** it must include a visualization (e.g., bar chart) showing the mean normalized gap for each power-of-two window relative to the expected value of 1.0.

---

### Edge Cases

- **What happens when** the prime generation library fails to install or the `primesieve` binary is missing on the runner? The script must detect this dependency failure and exit with a clear error code (e.g., 1) and a message suggesting the installation step, rather than crashing with a generic traceback.
- **How does the system handle** a scenario where the number of twin primes is significantly lower than the theoretical expectation (e.g., < 400,000)? The system must log a warning and flag the dataset as potentially incomplete, preventing downstream statistical tests from running on insufficient data.
- **What happens when** a normalized gap calculation results in a `log(0)` or `division by zero` (though mathematically impossible for primes > 1)? The script must include a guard clause to skip invalid entries and log the count of skipped entries to ensure data integrity.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate all prime numbers up to 1,000,000,000 using a CPU-tractable library (e.g., `primesieve`) and extract all twin prime pairs `(p, p+2)` within this range (See US-1).
- **FR-002**: System MUST compute the normalized gap `gₙ = (p_{n+1} - pₙ) / log(pₙ)` for every consecutive twin prime pair in the sequence, where `pₙ` is the first prime of the n-th twin pair and `p_{n+1}` is the first prime of the (n+1)-th twin pair, and persist these values to a CSV file (See US-1). This definition acknowledges the Hardy-Littlewood k-tuple conjecture context where the gap distribution may differ from the standard Cramér model by a constant factor.
- **FR-003**: System MUST perform a one-sample Kolmogorov–Smirnov test comparing the empirical distribution of `gₙ` against the theoretical exponential distribution with rate λ=1, explicitly noting the "self-normalized" nature of the data (See US-2).
- **FR-004**: System MUST generate a QQ-plot visualizing empirical quantiles of `gₙ` against theoretical exponential quantiles and save it as a PNG file (See US-2).
- **FR-005**: System MUST analyze subsets of data within windows `[2^k - 10000, 2^k + 10000]` for `k ∈ [10, 30]`, computing local means and variances, and perform one-sample t-tests against the theoretical mean of 1.0 (See US-3).
- **FR-006**: System MUST produce a final Markdown report summarizing the KS test statistics, p-values, and a summary of the localized deviation analysis (See US-2, US-3).
- **FR-007**: System MUST ensure all computations complete within ≤ 45 minutes and do not exceed 2 GiB of RAM usage, in compliance with Constitution Principle VI (See US-1, US-2).

### Key Entities

- **TwinPrimePair**: Represents a pair of primes `(p, p+2)`. Attributes: `p` (integer), `p_next` (integer), `delta` (integer, gap between starts of consecutive pairs), `normalized_gap` (float).
- **StatisticalResult**: Represents the outcome of a hypothesis test. Attributes: `test_name` (string), `statistic` (float), `p_value` (float), `rejection_status` (boolean).
- **WindowAnalysis**: Represents the analysis of a specific numeric range. Attributes: `power_of_two` (integer), `window_center` (float), `mean_gap` (float), `variance_gap` (float), `t_statistic` (float), `p_value` (float).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of generated twin prime pairs is recorded and the deviation from the theoretical expectation is reported in the final analysis (See US-1).
- **SC-002**: The Kolmogorov–Smirnov p-value is measured against the significance threshold of α=0.05 to determine if the empirical distribution significantly deviates from the exponential model (See US-2).
- **SC-003**: The deviation of local mean normalized gaps in power-of-two windows is measured against the theoretical mean (1.0) via one-sample t-tests to identify systematic anomalies (See US-3).
- **SC-004**: The total execution time of the data generation and analysis pipeline is measured against the ≤ 45 minutes limit mandated by Constitution Principle VI to ensure feasibility (See US-1, US-2, US-3).
- **SC-005**: The memory consumption of the prime generation process is measured against the ≤ 2 GiB RAM limit mandated by Constitution Principle VI to confirm the dataset fits within the compute box (See US-1).

## Assumptions

- The `primesieve` Python library (or its C++ binary equivalent) can be successfully installed and executed on the GitHub Actions free-tier runner (Ubuntu 22.04) without requiring GPU or specialized hardware.
- The total number of twin primes up to 10⁹ is small enough to be stored entirely in RAM (approx. 50-100 MB) and processed by standard Python libraries (`numpy`, `scipy`) without memory overflow.
- The Cramér model heuristic predicts that the normalized gaps `Δₙ / log pₙ` follow an exponential distribution with a rate parameter λ=1; this serves as the null hypothesis for the KS test. This heuristic is rooted in Cramér's foundational work and refined by Goldston, Pintz, and Yildirim (2005). Note: For twin primes specifically, the Hardy-Littlewood k-tuple conjecture suggests a correction factor (the twin prime constant C₂), which may influence the exact distributional shape., but the normalization `Δₙ / log pₙ` is the standard convention for testing the exponential scaling.
- The GitHub Actions free-tier runner provides sufficient disk space to store the generated prime list and the resulting CSV/figure artifacts.
- The statistical power of the sample size is sufficient to detect deviations from the exponential distribution, as the sample size is large enough for the Kolmogorov–Smirnov test to be sensitive to small discrepancies, even with the parameter estimation caveat.
- The definition of "normalized gap" as `Δₙ / log pₙ` is the standard convention used in the relevant literature (Cramér, 1936; Goldston et al.) for this specific analysis.