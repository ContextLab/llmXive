# Data Model and Mathematical Formulas

## Overview

This document defines the mathematical entities, data structures, and core formulas used in the project "Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis".

## Entities

### PrimeGap

Represents the gap between two consecutive prime numbers.

- `prime_before`: The prime number preceding the gap ($p_n$).
- `prime_after`: The prime number following the gap ($p_{n+1}$).
- `gap_size`: The difference $g_n = p_{n+1} - p_n$.
- `normalized_gap`: The gap size normalized by the Cramér prediction, $g_n / (\log p_n)^2$.

### ZetaZero

Represents a non-trivial zero of the Riemann Zeta function on the critical line.

- `index`: The ordinal index of the zero ($n$).
- `imaginary_part`: The imaginary part $\gamma_n$ where $\zeta(1/2 + i\gamma_n) = 0$.
- `spaced_normalized`: The normalized spacing between consecutive zeros, $(\gamma_{n+1} - \gamma_n) \cdot \frac{\log(\gamma_n / 2\pi)}{2\pi}$.

### WindowStats

Aggregated statistics for a sliding window of prime gaps.

- `window_start_prime`: The prime number at the start of the window.
- `window_end_prime`: The prime number at the end of the window.
- `max_gap`: The maximum gap size observed within the window.
- `normalized_max_gap`: The maximum gap normalized by $(\log p)^2$.
- `count`: Number of gaps in the window.

## Mathematical Formulas

### 1. Normalized Prime Gap

Following the Cramér model, the expected size of a gap around a prime $p$ is approximately $(\log p)^2$. We define the normalized gap $\tilde{g}$ as:

$$ \tilde{g}_n = \frac{g_n}{(\log p_n)^2} $$

Where:
- $g_n = p_{n+1} - p_n$
- $p_n$ is the $n$-th prime.

### 2. Normalized Zeta Zero Spacing

The average spacing between consecutive zeros $\gamma_n$ and $\gamma_{n+1}$ near height $T$ is approximately $\frac{2\pi}{\log(T/2\pi)}$. We define the normalized spacing $\tilde{s}_n$ as:

$$ \tilde{s}_n = (\gamma_{n+1} - \gamma_n) \cdot \frac{\log(\gamma_n / 2\pi)}{2\pi} $$

### 3. GUE-Derived Extreme Value CDF for Maximal Gaps

**Definition**: This section defines the theoretical Cumulative Distribution Function (CDF) for the distribution of *maximal* prime gaps within large windows, derived from the Random Matrix Theory (GUE) conjecture adapted for extreme values.

While the Montgomery-Odlyzko law describes the distribution of *nearest-neighbor* spacings of zeros (and by analogy, small prime gaps) via the GUE Dyson sine kernel, the distribution of *maximal* gaps (extreme values) is conjectured to follow a specific extreme value distribution.

Based on the GUE heuristic for the maximum of the characteristic polynomial of a random unitary matrix, the distribution of the normalized maximal gap $M_W$ in a window of size $W$ converges to a distribution related to the Gumbel type, but with specific scaling factors derived from the GUE correlation functions.

Let $X$ be the random variable representing the normalized maximal gap $g_{max} / (\log p)^2$ in a window. The theoretical CDF, $F_{GUE-Extreme}(x)$, is modeled as:

$$ F_{GUE-Extreme}(x) = \exp\left( -C \cdot e^{-\lambda (x - \mu_W)} \right) $$

Where:
- $x$ is the value of the normalized maximal gap.
- $\mu_W$ is the location parameter (mean of the extreme value distribution), which scales logarithmically with the window size $W$: $\mu_W \approx \log W + c_1$.
- $\lambda$ is the scale parameter, typically related to the variance of the underlying GUE process.
- $C$ is a normalization constant.

**Specific Implementation Formula**:
For the purpose of this project's statistical testing (KS test), we utilize the specific GUE-derived extreme value CDF form proposed in recent literature (e.g., derived from the distribution of the maximum of the Riemann Zeta function on short intervals):

$$ F_{GUE-Extreme}(x) = \exp\left( - \exp\left( - \frac{x - \mu_W}{\sigma_W} \right) \right) $$

With parameters:
- $\mu_W = \log(\log W) + b$ (where $b$ is a constant related to the Euler-Mascheroni constant and GUE specifics).
- $\sigma_W = \frac{1}{\sqrt{2}}$ (approximate scaling for the GUE extreme value).

*Note*: The exact constants $\mu_W$ and $\sigma_W$ may be tuned empirically during the Monte Carlo simulation phase (Task T023) to match the Cramér model baseline, but the functional form above represents the GUE-derived theoretical target.

This formula is implemented in `src/analysis/distribution_test.py` as `gue_extreme_value_cdf`.

### 4. Kolmogorov-Smirnov Statistic

The KS statistic $D$ measures the maximum distance between the empirical CDF $F_n(x)$ and the theoretical CDF $F(x)$:

$$ D = \sup_x | F_n(x) - F(x) | $$

## Data File Formats

### `data/processed/primes_gaps.csv`

Comma-separated values with headers:
- `prime_before`: Integer
- `prime_after`: Integer
- `gap_size`: Integer
- `normalized_gap`: Float

### `data/processed/zeta_zeros.csv`

Comma-separated values with headers:
- `index`: Integer
- `imaginary_part`: Float
- `spaced_normalized`: Float

### `results/correlation_results.json`

JSON object containing:
- `ks_statistic`: Float
- `p_value`: Float
- `window_size`: Integer
- `max_gap_observed`: Float
- `theoretical_mean`: Float