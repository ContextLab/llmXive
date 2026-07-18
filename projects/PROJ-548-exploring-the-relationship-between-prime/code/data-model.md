# Data Model and Mathematical Formulas

This document defines the mathematical entities, formulas, and data structures used in the project "Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis".

## 1. Entities

### 1.1 PrimeGap
Represents the gap between two consecutive prime numbers.
- `prime_before`: The prime number $p_n$.
- `prime_after`: The next prime number $p_{n+1}$.
- `gap_size`: $g_n = p_{n+1} - p_n$.
- `normalized_gap`: $g_n / (\ln p_n)^2$.

### 1.2 ZetaZero
Represents a non-trivial zero of the Riemann Zeta function.
- `index`: The ordinal position $n$ of the zero (1, 2, 3...).
- `imaginary_part`: The value $\gamma_n$ where $\zeta(1/2 + i\gamma_n) = 0$.
- `normalized_spacing`: $\Delta_n = \gamma_{n+1} - \gamma_n$ (often normalized by average spacing).

### 1.3 WindowStats
Aggregated statistics for a sliding window of prime gaps.
- `window_start_prime`: The prime number at the start of the window.
- `window_size`: Number of primes or range covered.
- `max_gap`: The maximum gap size observed in this window.
- `normalized_max_gap`: The maximum gap normalized by $\ln^2 p$.

## 2. Mathematical Formulas

### 2.1 Prime Gap Normalization
Following the Cramér model, the expected size of a gap near $p$ is $(\ln p)^2$.
$$ \tilde{g}_n = \frac{g_n}{(\ln p_n)^2} $$

### 2.2 Zeta Zero Spacing Normalization
The average spacing between zeros near height $T$ is $2\pi / \ln T$.
$$ \tilde{\gamma}_n = (\gamma_{n+1} - \gamma_n) \frac{\ln \gamma_n}{2\pi} $$

### 2.3 GUE-Derived Extreme Value CDF for Maximal Gaps (FR-003)

The central theoretical component of this research is the comparison of the distribution of maximal prime gaps against the predictions of the Gaussian Unitary Ensemble (GUE) from Random Matrix Theory.

**Context**:
While the distribution of *typical* normalized prime gaps is conjectured to follow an exponential distribution (Poisson process), the distribution of *maximal* gaps within large windows is expected to follow an extreme value distribution derived from GUE statistics.

**The Formula**:
Let $M_W$ be the maximum normalized gap observed in a window of size $W$.
The cumulative distribution function (CDF) for $M_W$, denoted as $F_{GUE}(x)$, is modeled by the Gumbel distribution (Type I extreme value distribution) with parameters derived from the GUE spacing statistics.

$$ F_{GUE}(x) = \exp\left( - \exp\left( - \frac{x - \mu_W}{\beta_W} \right) \right) $$

Where:
- $x$ is the normalized maximal gap value ($g_{max} / \ln^2 p$).
- $\mu_W$ is the location parameter (mode) for window size $W$.
- $\beta_W$ is the scale parameter for window size $W$.

**Parameter Derivation**:
Based on the Montgomery-Odlyzko law and subsequent extreme value analysis of GUE eigenvalues:
- The scale parameter $\beta_W$ is approximately $1 / \ln W$.
- The location parameter $\mu_W$ scales as $\ln W - \ln(\ln W) + C$, where $C$ is the Euler-Mascheroni constant ($\approx 0.577$).

Specifically, for the purpose of this implementation (Task T021b), we utilize the asymptotic form:
$$ \mu_W \approx \ln(W) + C $$
$$ \beta_W \approx \frac{1}{\ln(W)} $$

*Note: The exact constants may be refined during the Monte Carlo simulation phase (Task T023) to fit the empirical Cramér null distribution, but the functional form remains the Gumbel CDF above.*

## 3. Data Formats

### 3.1 Input: Primes/Gaps CSV
`data/processed/primes_gaps.csv`
Columns: `prime_before`, `prime_after`, `gap_size`, `normalized_gap`

### 3.2 Input: Zeta Zeros CSV
`data/processed/zeta_zeros.csv`
Columns: `index`, `imaginary_part`, `normalized_spacing`

### 3.3 Output: KS Test Results JSON
`results/correlation_results.json`
Structure:
```json
{
 "ks_statistic": float,
 "p_value": float,
 "empirical_cdf_points": [{"x": float, "cdf": float},...],
 "theoretical_cdf_params": {"mu": float, "beta": float},
 "window_size": int
}
```