# Research: Normalized Gaps Between Consecutive Squarefree Numbers

## Background

The distribution of gaps between consecutive integers with specific number-theoretic properties is a classic problem in analytic number theory. Squarefree numbers (integers not divisible by any perfect square > 1) have a density of $6/\pi^2 \approx 0.6079$. The "random thinning" heuristic suggests that the sequence of squarefree numbers behaves like a Poisson process where each integer is retained with probability $p = 6/\pi^2$. In a Poisson process, the inter-arrival times (gaps) follow an exponential distribution.

This project investigates whether the *normalized* gaps (raw gap divided by the empirical mean) of squarefree numbers converge to a standard exponential distribution (rate=1) as $N \to \infty$.

## Dataset Strategy

Since the integer sequence $\{1, \dots, N\}$ is generated deterministically, no external dataset download is required. The "dataset" is the sequence of squarefree numbers generated via the linear sieve.

| Dataset Name | Source / Generation Method | Verified URL | Notes |
|--------------|----------------------------|--------------|-------|
| **SquarefreeSequence** | Generated locally via `code/sieve.py` (Linear Sieve) | N/A (Local Generation) | Deterministic generation up to $N=10^7$. No external URL needed. |
| **GapDataset** | Derived from SquarefreeSequence | N/A | Contains raw and normalized gaps. |
| **ControlDataset** | Generated via random thinning ($p=6/\pi^2$) | N/A | Synthetic control for heuristic validation. |
| **GammaControlDataset** | Generated via Gamma distribution normalization | N/A | Secondary control to test rejection power. |

**Data Availability Note**: The "Verified datasets" block provided for this project indicates "NO verified source found" for `GapDataset` and lists only external CDF datasets unrelated to this number-theoretic problem. This is consistent with the project's design: the data is *generated*, not *downloaded*. The plan relies on the deterministic generation of integers, which is fully feasible on the GitHub Actions runner without network dependencies.

## Methodology

### 1. Squarefree Generation (Linear Sieve)
A linear sieve (O(N log log N)) is used to identify squarefree numbers.
- **Algorithm**: Iterate $i$ from 1 to $N$. Maintain a `min_prime` array. Mark multiples of $p^2$ as non-squarefree.
- **Output**: Ordered list $S = [s_1, s_2, \dots, s_k]$.
- **Verification**: Count of squarefree numbers $\approx N \times 6/\pi^2$.

### 2. Gap Calculation & Normalization
- **Raw Gaps**: $\Delta_i = s_{i+1} - s_i$.
- **Empirical Mean**: $\bar{\Delta} = \frac{1}{k-1} \sum \Delta_i$.
- **Normalized Gaps**: $g_i = \Delta_i / \bar{\Delta}$.
- **Check**: $\sum g_i = k-1$ (mean is exactly 1.0).

### 3. Statistical Testing (Lilliefors-style)
Standard Kolmogorov-Smirnov (KS) tests assume known parameters. Since the mean is estimated from the data, the KS distribution is invalid. The proposed Monte Carlo Lilliefors test is **not circular** and is methodologically sound as follows:

1.  **Compute Observed Statistic**: Calculate the KS statistic $D_{obs}$ between the *empirical CDF* of the normalized squarefree gaps and the *theoretical CDF of the normalized exponential distribution* (denoted $F_{norm}(x)$). Note: $F_{norm}(x)$ is not simply $1-e^{-x}$; it is the CDF of $X/\bar{X}$ where $X \sim Exp(1)$.
2.  **Generate Synthetic Datasets**: Generate $M=10,000$ synthetic datasets of size $k$ from $Exp(1)$.
3.  **Normalize Synthetic Data**: For each synthetic dataset, estimate its *own* sample mean $\bar{X}_{sim}$ and normalize the data ($X_{sim} / \bar{X}_{sim}$).
4.  **Compute Simulated Statistics**: For each normalized synthetic dataset, compute the KS statistic $D_{sim}$ against the *same* theoretical CDF $F_{norm}(x)$.
    - **Critical Distinction**: The distribution of $D_{sim}$ is the null distribution of the test statistic *under the hypothesis that the data is exponential and normalized*. This distribution is distinct from the distribution of KS statistics for raw data with known parameters.
5.  **Calculate p-value**: $p\text{-value} = \frac{\text{count}(D_{sim} \ge D_{obs}) + 1}{M + 1}$.
6.  **Decision**: If $p > 0.05$, retain null hypothesis (gaps are exponential).

**Why this is not circular**: The test does not assume the data is exponential to prove it is exponential. It tests whether the *shape* of the normalized gap distribution matches the *expected shape* of normalized exponential data. The null distribution of the KS statistic for normalized exponential data is mathematically distinct from that of normalized data from other distributions (e.g., Gamma, Weibull). The test specifically checks if the *shape* of the normalized distribution matches the expected shape of normalized exponential data, leveraging the fact that the null distribution of the KS statistic depends on the underlying distribution's shape even after mean normalization.

### 4. Control Experiment
- **Primary Control (Random Thinning)**:
  - **Generation**: Random thinning of $\{1, \dots, N\}$ with probability $p=6/\pi^2$.
  - **Analysis**: Apply the same Lilliefors test.
  - **Comparison**: $|D_{squarefree} - D_{control}| < 0.01$ supports the heuristic.
- **Secondary Control (Gamma)**:
  - **Generation**: Generate gaps from a Gamma distribution (shape=2, scale=1), normalize by mean.
  - **Analysis**: Apply the same Lilliefors test.
  - **Expected Result**: The test should *reject* the null hypothesis (low p-value), demonstrating that the test has power to detect non-exponential distributions (SC-007).

## Compute Feasibility

- **CPU-First**: The linear sieve and statistical tests are purely CPU-bound and highly efficient.
  - **Memory**: Sieve for $N=10^7$ requires $\approx 10^7$ integers (40 MB) + boolean flags (10 MB). Well within 2 GB limit.
  - **Time**: Sieve for a large-scale instance takes seconds. Monte Carlo (a large number of resamples) on 6M points takes minutes. Total runtime < 1 hour.
- **GPU**: Not required. No neural networks or heavy matrix operations.
- **Data Streaming**: Not required for $N=10^7$ (fits in RAM). If $N$ were increased to a magnitude requiring streaming, that approach would be needed, but that is out of scope.

## Statistical Rigor & Spec Corrections

- **Multiple Comparisons**: Not applicable (single hypothesis test per $N$, though run across 3 $N$ values for convergence). No correction needed for the convergence analysis as it is exploratory.
- **Power**: Sample size $\approx 6 \times 10^6$ is extremely large, providing high power to detect even minute deviations from exponentiality.
- **Causal/Associational**: This is a descriptive statistical study of a deterministic sequence. No causal claims are made; the "random thinning" is a heuristic model, not a causal mechanism.
- **Collinearity**: Not applicable (gaps are independent in the Poisson model, though in reality they are weakly dependent due to the sieve structure).
- **Measurement Validity**: The "instrument" is the linear sieve algorithm, which is mathematically exact. The statistical test is a standard Monte Carlo implementation.

**Correction of Success Criteria (SC-003 & SC-004)**:
The source `spec.md` has been updated to correct flawed Success Criteria:
- **SC-003**: Replaced the flawed "[deferred] difference in KS" with a requirement for stability of $KS \times \sqrt{N}$, consistent with the expected $O(1/\sqrt{N})$ convergence of the KS statistic.
- **SC-004**: Replaced the trivial "R^2 > 0.99" with a requirement for the Anderson-Darling statistic, which has higher power for large samples and is sensitive to tail deviations.
- **SC-007**: Added a new criterion requiring the test to reject the Gamma control, validating the test's power.

## Data Model & Contracts

All data is stored in Parquet format for efficiency and type safety. The following schemas in `contracts/` define the data structures:
- `SquarefreeSequence.schema.yaml`: Metadata for the generated integer sequence.
- `GapDataset.schema.yaml`: Metadata and paths for raw/normalized gaps.
- `TestResult.schema.yaml`: Metadata for the Lilliefors test results.
