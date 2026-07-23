# Data Model and Mathematical Notation
**Project**: Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis
**Version**: 1.0
**Date**: 2026-05-14

This document defines the mathematical entities, notation, and theoretical distributions used throughout the analysis pipeline, specifically supporting FR-004 (Pair-Correlation) and the derivation of the GUE Extreme Value Distribution for maximal gaps.

## 1. Fundamental Entities

### 1.1 Prime Gap ($g_p$)
Let $p_n$ denote the $n$-th prime number. The prime gap following $p_n$ is defined as:
$$ g_n = p_{n+1} - p_n $$

**Data Structure (`PrimeGap`)**:
- `prime_before`: $p_n$ (integer, $64$-bit)
- `prime_after`: $p_{n+1}$ (integer, $64$-bit)
- `gap_size`: $g_n$ (integer, $32$-bit)

### 1.2 Riemann Zeta Zero ($\gamma$)
Let $\rho = \frac{1}{2} + i\gamma$ be a non-trivial zero of the Riemann zeta function $\zeta(s)$, where $\gamma > 0$. We denote the ordered sequence of imaginary parts as $0 < \gamma_1 \le \gamma_2 \le \dots$.

**Data Structure (`ZetaZero`)**:
- `index`: $n$ (integer)
- `gamma`: $\gamma_n$ (float, $64$-bit)
- `spacing`: $\delta_n = \gamma_{n+1} - \gamma_n$ (float, $64$-bit)

## 2. Normalization and Scaling

### 2.1 Prime Gap Normalization
To compare gaps across different scales, we normalize by the Cramér prediction. The expected gap size near $p$ is $\ln p$. The normalized gap $x_n$ is:
$$ x_n = \frac{g_n}{(\ln p_n)^2} $$
*Note: The square $(\ln p_n)^2$ is used to normalize the distribution of *maximal* gaps to a non-degenerate limit, consistent with extreme value theory for the Poisson process of large gaps.*

### 2.2 Zeta Zero Spacing Normalization
The average spacing between zeros near height $T$ is approximately $2\pi / \ln T$. The normalized spacing $y_n$ for a zero at height $\gamma_n$ is:
$$ y_n = \frac{\gamma_{n+1} - \gamma_n}{2\pi / \ln \gamma_n} $$
Under the Riemann Hypothesis and the GUE hypothesis, the distribution of $y_n$ converges to the GUE spacing distribution (Dyson's sine kernel).

## 3. Theoretical Distributions

### 3.1 Pair-Correlation Distribution (GUE)
The pair-correlation function $R_2(u)$ for the normalized zero spacings, assuming the GUE hypothesis, is given by:
$$ R_2(u) = 1 - \left( \frac{\sin(\pi u)}{\pi u} \right)^2 $$
This describes the probability density of finding two zeros at a normalized distance $u$.

### 3.2 GUE-Derived Extreme Value CDF for Maximal Gaps
We are interested in the distribution of the *maximum* gap $M_W$ within a sliding window $W$ of normalized prime gaps.
According to the Montgomery-Odlyzko law, the local statistics of primes mimic those of the eigenvalues of large random matrices from the Gaussian Unitary Ensemble (GUE).

Let $F_{GUE}(x)$ be the cumulative distribution function (CDF) of the largest eigenvalue of an $N \times N$ GUE matrix, which converges to the Tracy-Widom distribution $F_2(s)$ as $N \to \infty$.

For the extreme values of the normalized prime gaps, we model the CDF of the maximum gap $M$ in a window as:
$$ P(M \le x) \approx F_2\left( \frac{x - \mu_W}{\sigma_W} \right) $$
where:
- $F_2(s)$ is the Tracy-Widom distribution for $\beta=2$ (GUE).
- $\mu_W$ and $\sigma_W$ are location and scale parameters dependent on the window size $W$.
- $\mu_W \approx \ln W$ (roughly, the expected maximum of $W$ i.i.d. exponential variables, adjusted for GUE repulsion).
- $\sigma_W \approx (\ln W)^{1/3}$.

**Tracy-Widom Approximation**:
The CDF $F_2(s)$ is defined via the solution $q(s)$ to the Painlevé II equation:
$$ q''(s) = s q(s) + 2 q(s)^3 $$
with asymptotic behavior $q(s) \sim \text{Ai}(s)$ as $s \to \infty$.
$$ F_2(s) = \exp\left( -\int_s^\infty (x-s) q(x)^2 \, dx \right) $$

In implementation (`src/analysis/distribution_test.py`), we use the `scipy.stats.tracywidom` or a numerical approximation of the Painlevé II solution to evaluate this CDF.

## 4. Hypothesis Testing Framework

### 4.1 Null Hypothesis ($H_0$)
The distribution of normalized maximal prime gaps in sliding windows is statistically indistinguishable from the theoretical GUE-derived extreme value distribution.

### 4.2 Test Statistic
The Kolmogorov-Smirnov (KS) statistic $D_{N}$ is used:
$$ D_N = \sup_x | F_{emp}(x) - F_{GUE}(x) | $$
where $F_{emp}$ is the empirical CDF of the observed normalized maximal gaps, and $F_{GUE}$ is the theoretical CDF defined in Section 3.2.

### 4.3 Significance
The p-value is calculated by comparing $D_N$ against a null distribution generated via:
1. Monte Carlo simulation of the Cramér model (random primes).
2. Permutation tests of the observed gap sequence.

## 5. Constants and Parameters

- $N_{max} = 10^{10}$: Upper bound for prime generation (FR-001).
- $W = 10^6$: Default sliding window size (FR-003).
- $WINDOW\_STEP = 1$: Default stride for sliding windows (configurable).
- $GLOBAL\_SEED$: Deterministic seed for reproducibility (config.py).

## 6. References

1. Odlyzko, A. M. (1987). "On the distribution of spacings between zeros of the zeta function".
2. Tracy, C. A., & Widom, H. (1994). "Level-spacing distributions and the Airy kernel".
3. Montgomery, H. L. (1973). "The pair correlation of zeros of the zeta function".
4. Cramér, H. (1936). "On the order of magnitude of the difference between consecutive prime numbers".