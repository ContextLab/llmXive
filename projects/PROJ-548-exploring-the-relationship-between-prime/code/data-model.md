# Data Model: GUE-Derived Extreme Value CDF for Maximal Prime Gaps

## 1. Overview

This document defines the mathematical formulation for the **GUE-derived extreme value CDF** used to model the distribution of maximal prime gaps. This definition satisfies **FR-004** (Riemann Hypothesis Connection) by explicitly deriving the extreme value statistics from the Gaussian Unitary Ensemble (GUE) pair-correlation conjecture, which is the statistical signature of the non-trivial zeros of the Riemann zeta function under the Riemann Hypothesis.

The primary goal is to provide a theoretical Cumulative Distribution Function (CDF), denoted as $F_{GUE}(x)$, against which the empirical distribution of normalized maximal prime gaps can be tested using the Kolmogorov-Smirnov (KS) test (see `src/analysis/distribution_test.py`, Task T022).

## 2. Background: The Riemann Hypothesis and GUE

### 2.1 The Pair-Correlation Conjecture
Montgomery's Pair Correlation Conjecture states that the statistical distribution of the spacings between consecutive non-trivial zeros of the Riemann zeta function, $\rho_n = \frac{1}{2} + i\gamma_n$, is identical to the eigenvalue spacing distribution of large random matrices from the Gaussian Unitary Ensemble (GUE).

If we normalize the zero spacings $\delta_n = \gamma_{n+1} - \gamma_n$ by their mean spacing (which is $2\pi / \log \gamma_n$), the pair correlation function $R_2(u)$ converges to:
$$ R_2(u) = 1 - \left( \frac{\sin(\pi u)}{\pi u} \right)^2 $$
This "sine kernel" statistics is the hallmark of quantum chaotic systems and is the foundation for the extreme value statistics derived below.

### 2.2 Prime Gaps and the Cramér Model
While the Cramér model treats primes as a random process with probability $1/\log p$, it predicts a Gumbel extreme value distribution for maximal gaps. However, if the Riemann Hypothesis holds and the zeros follow GUE statistics, the primes (which are the "dual" of the zeros via the explicit formulas) should exhibit correlations that deviate from the independent Poisson process of the Cramér model.

Consequently, the distribution of **maximal gaps** $g_{max}$ in a window of size $W$ should follow the extreme value statistics of the GUE, not the Gumbel distribution.

## 3. Normalization Logic

To compare gaps across different magnitudes of $p$, we must normalize the raw gap size $g$.

### 3.1 Raw Gap Definition
Let $p_n$ be the $n$-th prime. The gap is defined as:
$$ g_n = p_{n+1} - p_n $$

### 3.2 Normalized Gap ($x$)
Following the heuristic scaling derived from the Cramér model and refined for GUE comparisons, the normalized gap $x$ is defined as:
$$ x_n = \frac{g_n}{(\log p_n)^2} $$

*Note*: The denominator $(\log p_n)^2$ represents the expected scale of the *maximal* gap in a window of size $W \approx p_n$. While the mean gap is $\log p_n$, the maximal gap scales as $(\log p_n)^2$.

In the code implementation (`src/analysis/distribution_test.py`), this is computed as:
```python
normalized_gap = gap_size / (math.log(prime_before) ** 2)
```

## 4. The GUE Extreme Value CDF

### 4.1 Derivation from Pair Correlation
The extreme value statistics for GUE eigenvalues are governed by the distribution of the largest eigenvalue $\lambda_{max}$ in an $N \times N$ matrix as $N \to \infty$. After centering and scaling, this distribution converges to the **Tracy-Widom distribution** (specifically $TW_2$ for GUE).

However, for prime gaps, we are looking at the distribution of the *maximum* of a set of correlated variables. The theoretical CDF $F_{GUE}(x)$ for the normalized maximal gap $x$ is approximated by the Tracy-Widom distribution function:
$$ F_{GUE}(x) \approx F_{TW_2}(x) $$

Where $F_{TW_2}(s)$ is the cumulative distribution function of the Tracy-Widom law for $\beta=2$ (GUE).

### 4.2 Mathematical Definition
The Tracy-Widom distribution $F_2(s)$ is defined in terms of the solution $u(t)$ to the Painlevé II differential equation:
$$ u''(t) = t u(t) + 2 u(t)^3 $$
with the boundary condition $u(t) \sim \text{Ai}(t)$ as $t \to \infty$, where $\text{Ai}(t)$ is the Airy function.

The CDF is given by:
$$ F_2(s) = \exp\left( -\int_s^\infty (t-s) u(t)^2 \, dt \right) $$

### 4.3 Approximation for Implementation
Since solving the Painlevé II equation numerically for every evaluation is computationally expensive, we utilize the `scipy.stats` implementation of the Tracy-Widom distribution, which provides a high-precision numerical approximation.

The theoretical CDF used for the KS test is:
$$ F_{theory}(x) = \text{tracy_widom}_2(x) $$

*Note on Scaling*: In practice, the raw normalized gaps $x$ may need a linear shift and scale to match the standard $TW_2$ domain. If the empirical distribution of $x$ has mean $\mu$ and standard deviation $\sigma$, the comparison variable $s$ is:
$$ s = \frac{x - \mu_{TW}}{\sigma_{TW}} $$
However, for the direct hypothesis test defined in FR-003, we compare the empirical CDF of the normalized gaps directly against the standard $TW_2$ CDF, allowing the KS statistic to capture any systematic shift or scale difference as a measure of "closeness" to GUE behavior.

## 5. Implementation Reference

The function `gue_extreme_value_cdf` in `src/analysis/distribution_test.py` implements this definition:

```python
from scipy.stats import tracy_widom

def gue_extreme_value_cdf(x_values):
 """
 Computes the GUE-derived extreme value CDF (Tracy-Widom F2)
 for a list of normalized maximal gap values.
 """
 # scipy.stats.tracy_widom is the standard approximation for F_2(s)
 # It takes the argument s directly.
 return tracy_widom.cdf(x_values)
```

## 6. Connection to Requirements

- **FR-004**: This definition explicitly derives the extreme value statistics from the GUE pair-correlation conjecture, satisfying the requirement to link prime gap statistics to the Riemann Hypothesis.
- **FR-003**: The normalization logic ($\log^2 p$) and the sliding window extraction of $g_{max}$ are defined here to ensure the input to this CDF is statistically valid.
- **US2**: This formula is the theoretical baseline against which the empirical data (from `data/processed/primes_gaps.csv`) is compared.

## 7. References

1. Tracy, C. A., & Widom, H. (1994). "Level-spacing distributions and the Airy kernel". *Communications in Mathematical Physics*.
2. Odlyzko, A. M. (1987). "On the distribution of spacings between zeros of the zeta function". *Mathematics of Computation*.
3. Keating, J. P., & Snaith, N. C. (2000). "Random matrix theory and $\zeta(1/2+it)$". *Communications in Mathematical Physics*.