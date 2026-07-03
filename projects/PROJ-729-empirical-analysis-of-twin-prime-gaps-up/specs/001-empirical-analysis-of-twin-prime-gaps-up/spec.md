# Specification: Twin Prime Gap Analysis

## User Stories

### US1: Generate and Normalize Twin Prime Gaps (P1)
As a researcher, I want to generate a complete list of twin primes up to 10⁹ and compute their normalized gaps, so that I have a validated dataset for statistical analysis.
- **Acceptance Criteria**:
 - CSV file `data/raw/twin_primes.csv` exists.
 - Columns: `p`, `p_next`, `delta`, `normalized_gap`.
 - No NaN values.
 - Row count within ±5% of Hardy-Littlewood expectation.

### US2: Statistical Goodness-of-Fit Testing (P2)
As a researcher, I want to perform a Parametric Bootstrap KS test and generate a QQ-plot, so that I can determine if the data fits the exponential distribution.
- **Acceptance Criteria**:
 - `data/results/stats.json` contains KS statistic and p-value.
 - `data/figures/qq_plot.png` is generated.
 - Rejection status (p < 0.05) is recorded.

### US3: Localized Deviation Analysis (P3)
As a researcher, I want to analyze gaps in windows around powers of two, so that I can detect systematic deviations from the theoretical mean.
- **Acceptance Criteria**:
 - `data/results/local_stats.json` contains window metrics.
 - `data/figures/local_deviation.png` is generated.
 - One-sample t-tests are performed against mean 1.0.

## Functional Requirements
- **FR-001**: Use `primesieve` for generation.
- **FR-002**: Compute `delta = p_{n+1} - p_n` and `normalized = delta / log(p)`.
- **FR-003**: Use Parametric Bootstrap KS (10k iterations, seed=42).
- **FR-004**: Generate QQ-plot with reference line y=x.
- **FR-005**: Analyze windows [2^k - 10000, 2^k + 10000].
- **FR-006**: Generate final Markdown report.
- **FR-007**: Ensure RAM < 2GiB and time < 45 mins.

## Constraints
- CPU-only execution.
- Python 3.11+.
