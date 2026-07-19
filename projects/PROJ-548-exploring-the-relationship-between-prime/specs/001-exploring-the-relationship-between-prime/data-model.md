# Data Model and Mathematical Formulas

## Overview

This document defines the mathematical entities, data structures, and specific formulas used in the "Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis" project. It serves as the canonical reference for the implementation of statistical tests and data processing pipelines.

## 1. Core Entities

### 1.1 Prime Gap
A prime gap $g_n$ is the difference between consecutive prime numbers $p_{n+1}$ and $p_n$:
$$ g_n = p_{n+1} - p_n $$

**Data Representation**:
- `prime_before` (int): $p_n$
- `prime_after` (int): $p_{n+1}$
- `gap_size` (int): $g_n$
- `normalized_gap` (float): $g_n / (\ln p_n)^2$ (Cramér normalization)

### 1.2 Zeta Zero
A non-trivial zero of the Riemann zeta function $\zeta(s)$, located at $s = \frac{1}{2} + i\gamma$.

**Data Representation**:
- `index` (int): The $n$-th zero
- `imaginary_part` (float): $\gamma_n$
- `spacing` (float): $\gamma_{n+1} - \gamma_n$ (local spacing)

### 1.3 Window Statistics
Aggregated statistics computed over a sliding window of primes.

**Data Representation**:
- `window_start_prime` (int): $p_{start}$
- `window_end_prime` (int): $p_{end}$
- `max_gap` (int): $\max(g_i)$ within the window
- `normalized_max_gap` (float): $\max(g_i) / (\ln p_{start})^2$

---

## 2. Mathematical Formulas

### 2.1 Normalization (Cramér Model)
To compare gaps of different magnitudes, we normalize by the expected average gap size at $p$, which is $\ln p$. The Cramér model suggests that the distribution of normalized gaps $x = g / (\ln p)^2$ converges to an exponential distribution $e^{-x}$ for small gaps. However, for *extreme* values (maximal gaps), we look to Random Matrix Theory.

$$ \tilde{g}_n = \frac{g_n}{(\ln p_n)^2} $$

### 2.2 Zeta Zero Pair Correlation (GUE Hypothesis)
Montgomery's Pair Correlation Conjecture states that the normalized spacings between consecutive zeta zeros follow the same distribution as the eigenvalues of large random matrices from the Gaussian Unitary Ensemble (GUE).

The pair correlation function is:
$$ R_2(u) = 1 - \left( \frac{\sin(\pi u)}{\pi u} \right)^2 $$

### 2.3 GUE-Derived Extreme Value CDF for Maximal Gaps (FR-004)

**Derivation**:
The Riemann Hypothesis implies that the statistical properties of the zeta zeros are identical to the eigenvalues of GUE matrices. The distribution of the *maximum* of a set of correlated random variables (like eigenvalues in a window) is governed by Extreme Value Theory.

For the Gaussian Unitary Ensemble (GUE), the distribution of the largest eigenvalue $\lambda_{max}$, after appropriate centering and scaling, converges to the **Tracy-Widom distribution** ($F_2$).

While prime gaps are not eigenvalues, the GUE hypothesis for the zeros suggests that the *extremal statistics* of the prime gaps (when normalized and viewed through the lens of the zero spacings) should exhibit similar universal behavior. Specifically, the distribution of the maximal normalized gap $M_N = \max_{1 \le i \le N} \tilde{g}_i$ in a window of size $N$ is hypothesized to follow the Tracy-Widom $F_2$ distribution, shifted and scaled by the window parameters.

**The Formula**:
Let $x$ be the normalized maximal gap. The theoretical Cumulative Distribution Function (CDF) $F_{GUE}(x)$ is approximated by the Tracy-Widom distribution $F_2$:

$$ F_{GUE}(x) \approx F_2\left( \frac{x - \mu_N}{\sigma_N} \right) $$

Where:
- $F_2(s) = \exp\left( -\int_s^\infty (t-s) u(t)^2 dt \right)$
- $u(t)$ is the solution to the Painlevé II equation: $u'' = t u + 2u^3$ with boundary condition $u(t) \sim \text{Ai}(t)$ as $t \to \infty$.
- $\mu_N$ and $\sigma_N$ are location and scale parameters dependent on the window size $N$ and the density of primes/zeros.

**Approximation for Implementation**:
Since the exact Painlevé solution is computationally expensive, we utilize the `scipy.stats` implementation of the Tracy-Widom distribution ($F_2$) as the proxy for the GUE extreme value CDF.

The theoretical CDF for the normalized maximal gap $X$ is defined as:
$$ P(X \le x) = F_{TW2}\left( \frac{x - \mu}{\sigma} \right) $$

Where:
- $F_{TW2}$ is the Tracy-Widom $F_2$ CDF.
- $\mu$ is the mean of the maximal gap distribution for the specific window size.
- $\sigma$ is the standard deviation scaling factor.

**Normalization Logic**:
1. Calculate raw maximal gap $g_{max}$ in a window of primes.
2. Normalize: $x = g_{max} / (\ln p_{start})^2$.
3. Compare the empirical CDF of $x$ values against $F_{TW2}((x - \mu)/\sigma)$.

**Note on Derivation from Pair-Correlation**:
The pair-correlation function $R_2(u)$ describes the local density of zeros. The extreme value distribution is the integral of the probability that *no* eigenvalues (or zeros) exceed a certain threshold in a given interval. The Tracy-Widom distribution arises as the limiting distribution of the largest eigenvalue in the GUE, which is the mathematical object corresponding to the "largest gap" in the dual spectrum. Thus, the GUE extreme value CDF is the direct consequence of the pair-correlation hypothesis applied to the extremal statistics.

---

## 3. Data Files Schema

### 3.1 `data/processed/primes_gaps.csv`
| Column | Type | Description |
|:--- |:--- |:--- |
| prime_before | int64 | The smaller prime $p_n$ |
| prime_after | int64 | The larger prime $p_{n+1}$ |
| gap_size | int64 | $p_{n+1} - p_n$ |
| normalized_gap | float64 | $gap\_size / (\ln(prime\_before))^2$ |

### 3.2 `data/processed/zeta_zeros.csv`
| Column | Type | Description |
|:--- |:--- |:--- |
| index | int64 | $n$-th zero |
| gamma | float64 | Imaginary part $\gamma_n$ |
| spacing | float64 | $\gamma_n - \gamma_{n-1}$ (if $n>0$) |

### 3.3 `results/correlation_results.json`
| Key | Type | Description |
|:--- |:--- |:--- |
| ks_statistic | float | Kolmogorov-Smirnov statistic |
| p_value | float | P-value of the KS test |
| window_size | int | $W$ used in analysis |
| max_gap_mean | float | Mean of maximal gaps observed |
| max_gap_std | float | Std dev of maximal gaps observed |

---

## 4. Implementation Notes

- **Tracy-Widom Source**: Use `scipy.stats.tracy_widom` (if available) or a high-precision numerical approximation of $F_2$ for the theoretical CDF.
- **Parameters**: $\mu$ and $\sigma$ for the Tracy-Widom fit are derived empirically from the Cramér model simulation (Task T023) or analytically approximated as $\mu \approx 2\sqrt{N}$ and $\sigma \approx N^{-1/6}$ for GUE eigenvalues, adapted for the prime gap density.
- **Verification**: The KS test (Task T022) compares the empirical CDF of normalized maximal gaps against this theoretical $F_{GUE}$ CDF.