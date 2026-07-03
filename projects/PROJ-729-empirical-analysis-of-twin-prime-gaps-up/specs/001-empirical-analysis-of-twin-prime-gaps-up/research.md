# Research: Empirical Analysis of Twin Prime Gaps up to 10⁹

## Theoretical Background

### The Cramér Model and Prime Gaps
The foundational heuristic for prime gaps was proposed by Harald Cramér. Cramér modeled the primes as a random sequence where the probability that an integer $n$ is prime is $1/\log n$. Under this model, the gaps between consecutive primes, when normalized by $\log p_n$, are expected to follow an exponential distribution with rate parameter $\lambda = 1$.

For **twin primes** (pairs $(p, p+2)$), the situation is more nuanced. The Hardy-Littlewood k-tuple conjecture suggests that twin primes occur with a frequency governed by the twin prime constant $C_2 \approx 0.66016$. While the *density* of twin primes differs from the density of all primes, the distribution of the *gaps between consecutive twin primes* (normalized by $\log p_n$) is hypothesized to follow an exponential law, albeit potentially with a different scaling factor or subtle deviations due to the specific arithmetic structure of twin primes.

**Theoretical Context for Inter-Twin Gaps**:
The specific metric used here—the gap between the *starts* of consecutive twin prime pairs ($p_{n+1} - p_n$)—represents the distribution of "inter-twin" gaps. Unlike the gaps between all primes, which are dense, inter-twin gaps are sparse and clustered. The hypothesis that these normalized inter-twin gaps follow an exponential distribution is a specific application of the probabilistic model to a thin subsequence of primes. This is grounded in the broader probabilistic number theory framework (Cramér 1936) but requires careful interpretation of the "randomness" assumption for this specific subset. Recent refinements by Goldston, Pintz, and Yıldırım on small gaps between primes provide context for the limits of such models, but for the *distribution* of gaps (not just the liminf), the exponential model remains the standard null hypothesis for empirical testing of this specific metric.

> **Reviewer Note (dan-rockmore-simulated)**: This experiment sits within the broader tapestry of probabilistic number theory. While Cramér (1936) provides the baseline heuristic, the specific application to twin primes requires acknowledging the refinements by Goldston, Pintz, and Yıldırım (2005), who demonstrated that $\liminf (p_{n+1}-p_n)/\log p_n = 0$. However, for the *distribution* of gaps (not just the liminf), the exponential model remains the standard null hypothesis for empirical testing.

### Hypothesis Formulation
- **Null Hypothesis ($H_0$)**: The normalized gaps $g_n = \Delta_n / \log p_n$ between consecutive twin prime pairs follow an exponential distribution with $\lambda = 1$.
- **Alternative Hypothesis ($H_1$)**: The distribution deviates significantly from the exponential model (e.g., heavier tails, systematic shifts).

## Dataset Strategy

Since the dataset is **generated** rather than downloaded, the "dataset" is the output of the `generate_primes` script.
- **Source**: Algorithmically generated using the `primesieve` library.
- **Scope**: All twin prime pairs $(p, p+2)$ where $p < 10^9$.
- **Variables**:
  - `p`: The first prime of the twin pair.
  - `p_next`: The first prime of the subsequent twin pair.
  - `delta`: The gap $p_{next} - p$.
  - `normalized_gap`: $\Delta_n / \log(p_n)$.

*Note: No external verified dataset URLs are required as the data is synthetic and deterministic.*

## Statistical Methodology

### 1. Goodness-of-Fit (Global) - Parametric Bootstrap KS Test
The standard one-sample Kolmogorov–Smirnov (KS) test is **invalid** for this dataset because the data is "self-normalized" (the mean of the empirical distribution is forced to be close to 1.0 by the definition of the normalization). Using standard KS tables would inflate p-values and reduce power.

**Corrected Methodology**:
- **Test**: Parametric Bootstrap Kolmogorov–Smirnov Test.
- **Procedure**:
  1. Calculate the observed KS statistic $D_{obs}$ between the empirical data and the theoretical $Exponential(\lambda=1)$.
  2. Simulate $B=10,000$ synthetic datasets of size $N$ (where $N$ is the number of twin primes) from $Exponential(\lambda=1)$.
  3. For each synthetic dataset, normalize it by its own mean (mimicking the data generation process) and calculate the KS statistic against $Exponential(\lambda=1)$.
  4. The p-value is the proportion of synthetic statistics $\ge D_{obs}$.
- **Visualization**: QQ-Plot (Empirical Quantiles vs. Theoretical Quantiles).
- **Caveat**: This method corrects for the bias introduced by parameter estimation (mean forced to 1.0).

### 2. Localized Deviation Analysis - Two-Sample Distribution Tests
The one-sample t-test against a theoretical mean of 1.0 is **tautological** for self-normalized data, as the global mean is fixed at 1.0. Testing local windows against 1.0 without accounting for the global constraint is methodologically unsound.

**Corrected Methodology**:
- **Scope**: Windows $[2^k - 10^4, 2^k + 10^4]$ for $k \in [10, 30]$.
- **Test**: Two-Sample Kolmogorov–Smirnov Test (or Anderson-Darling).
- **Comparison**: Compare the distribution of `normalized_gap` within the local window against the distribution of `normalized_gap` in the **global dataset** (excluding the window).
- **Rationale**: This tests whether the local window is drawn from the same distribution as the global set, avoiding the circular reference of testing against a fixed constant (1.0).
- **Correction**: Since 21 windows are tested, a Bonferroni correction (or similar) will be applied to the significance threshold ($\alpha_{adj} = 0.05 / 21 \approx 0.0024$) to control the family-wise error rate.

## Feasibility & Resource Analysis

- **Memory**: The number of twin primes up to a large bound is expected to be substantial, consistent with asymptotic predictions. Storing 440k rows of floats/ints requires < 50 MB RAM. The `primesieve` library uses a segmented sieve, keeping memory usage low. This is well within the 2 GiB limit.
- **Time**: `primesieve` can generate primes up to $^9$ in [deferred] on modern CPUs. The statistical analysis on 440k points is instantaneous (< 1 second). The Parametric Bootstrap (sufficient iterations for stability) may take a moderate amount of time. The total pipeline will comfortably fit within the allotted time limit.
- **Dependencies**: `primesieve` is available via `pip` and relies on a pre-compiled C++ binary, ensuring no compilation overhead on the CI runner.

## Risk Assessment

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| `primesieve` installation failure on CI | High | Fallback to a pure Python segmented sieve (slower) or explicit error handling with installation instructions. |
| Memory overflow during generation | Low | `primesieve` is memory-efficient; monitor peak usage. |
| Statistical power issues | Low | Sample size (large) is large; Bootstrap KS test will be highly sensitive. |
| Self-normalization bias | Medium | Explicitly addressed by using Parametric Bootstrap and Two-Sample tests. |

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| Use `primesieve` over `sympy` | `sympy` is too slow for generating primes up to $10^9$ in the allotted time. |
| Use Parametric Bootstrap KS | Standard KS tables are invalid for self-normalized data; Bootstrap corrects the p-value distribution. |
| Use Two-Sample KS for local windows | One-sample t-tests against 1.0 are tautological; Two-Sample tests compare local vs. global distribution. |
| Apply Bonferroni correction | Necessary for the 21 localized tests to avoid false positives. |
