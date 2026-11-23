# Data Model and Mathematical Notation

This document defines the mathematical entities, notation, and distributions used throughout the `PROJ-548-exploring-the-relationship-between-prime` pipeline. It serves as the reference for implementing data structures in `src/utils/models.py` and analysis logic in `src/analysis/distribution_test.py`.

## 1. Prime Gap Entity

The fundamental unit of analysis is the gap between consecutive prime numbers.

### Definition
Let $p_n$ denote the $n$-th prime number. The prime gap $g_n$ is defined as:
$$ g_n = p_{n+1} - p_n $$

### Normalized Prime Gap
To compare gaps across different magnitudes of $p_n$, we normalize by the Cramér prediction. The normalized gap $\tilde{g}_n$ is:
$$ \tilde{g}_n = \frac{g_n}{(\ln p_n)^2} $$
where $\ln$ denotes the natural logarithm.

### Data Structure (PrimeGap)
In the implementation (`src/utils/models.py`), a `PrimeGap` record contains:
- `prime_before` ($p_n$): The prime number preceding the gap.
- `prime_after` ($p_{n+1}$): The prime number following the gap.
- `gap_size` ($g_n$): The integer difference $p_{n+1} - p_n$.
- `normalized_gap` ($\tilde{g}_n$): The float value $g_n / (\ln p_n)^2$.

## 2. Zeta Zero Entity

The non-trivial zeros of the Riemann zeta function, $\zeta(s)$, are denoted by $\rho = \frac{1}{2} + i\gamma$.

### Definition
We consider the imaginary parts $\gamma_n$ of the zeros on the critical line, ordered such that $0 < \gamma_1 \le \gamma_2 \le \dots$.

### Normalized Zero Spacing
The local spacing between consecutive zeros $\gamma_n$ and $\gamma_{n+1}$ is normalized by the mean spacing at that height. The average spacing near $\gamma$ is approximately $\frac{2\pi}{\ln(\gamma/2\pi)}$. The normalized spacing $\tilde{\delta}_n$ is:
$$ \tilde{\delta}_n = \frac{\gamma_{n+1} - \gamma_n}{\frac{2\pi}{\ln(\gamma_n/2\pi)}} $$
Under the Riemann Hypothesis, the distribution of these normalized spacings is conjectured to match the eigenvalue spacing of the Gaussian Unitary Ensemble (GUE).

### Data Structure (ZetaZero)
In the implementation (`src/utils/models.py`), a `ZetaZero` record contains:
- `index` ($n$): The ordinal index of the zero.
- `imaginary_part` ($\gamma_n$): The real value of the imaginary part.
- `spacing` ($\gamma_{n+1} - \gamma_n$): The difference to the next zero.
- `normalized_spacing` ($\tilde{\delta}_n$): The normalized value.

## 3. Sliding Window Statistics

To analyze maximal gaps within a specific range, we employ a sliding window approach.

### Definition
Let $W$ be the window size (number of primes or magnitude range, configurable in `src/utils/config.py`). Let $S$ be the step size (stride).
For a window $[p_k, p_{k+W}]$, we define the maximal gap within that window:
$$ G_{max}^{(k)} = \max \{ g_i \mid k \le i < k+W \} $$

### Data Structure (WindowStats)
In the implementation (`src/utils/models.py`), a `WindowStats` record contains:
- `window_start_prime` ($p_k$): The starting prime of the window.
- `window_end_prime` ($p_{k+W}$): The ending prime of the window.
- `max_gap` ($G_{max}^{(k)}$): The maximum gap size observed in this window.
- `normalized_max_gap`: The Cramér-normalized value of the maximal gap.

## 4. GUE-Derived Extreme Value CDF

This section defines the theoretical distribution against which empirical maximal gaps are compared.

### Theoretical Basis
According to the GUE hypothesis, the local statistics of the Riemann zeros match the eigenvalues of large random Hermitian matrices from the Gaussian Unitary Ensemble. The distribution of the *largest* eigenvalue (extreme value) in the GUE, after appropriate scaling, converges to the Tracy-Widom distribution $F_2$.

However, for maximal *gaps* (extreme values of the spacing distribution), we are looking at the tail of the spacing distribution. While the pair-correlation function $1 - (\frac{\sin(\pi x)}{\pi x})^2$ describes local spacing, the distribution of the *maximum* of $N$ such spacings in a window follows Extreme Value Theory.

For the GUE, the distribution of the maximum eigenvalue $\lambda_{max}$ (centered at $2\sqrt{N}$ and scaled by $N^{-1/6}$) converges to the Tracy-Widom $F_2$ distribution:
$$ F_2(s) = \exp\left( -\int_s^\infty (x-s) u(x)^2 dx \right) $$
where $u(x)$ satisfies the Painlevé II equation: $u'' = xu + 2u^3$ with asymptotic behavior $u(x) \sim \text{Ai}(x)$ as $x \to \infty$.

### Application to Prime Gaps
We approximate the distribution of normalized maximal gaps $Y = \max(\tilde{g}_i)$ in a window of size $W$ using the Tracy-Widom $F_2$ distribution, assuming the GUE universality class applies to the extremes of the prime gap sequence (as a null hypothesis for comparison).

The theoretical CDF $F_{GUE}(y)$ for the normalized maximal gap $y$ is modeled as:
$$ F_{GUE}(y; \mu, \sigma) = F_2\left( \frac{y - \mu_W}{\sigma_W} \right) $$
where:
- $F_2$ is the Tracy-Widom distribution function (implemented via `scipy.stats.tracywidom` or numerical integration of Painlevé II).
- $\mu_W$ is the expected location of the maximum for window size $W$.
- $\sigma_W$ is the scaling factor for the fluctuations.

*Note: The exact mapping of prime gap extremes to Tracy-Widom parameters is an active area of research. For this implementation, we use the standard $F_2$ distribution as the primary theoretical reference for GUE behavior, as specified in FR-004.*

### Implementation Reference
The function `gue_extreme_value_cdf` in `src/analysis/distribution_test.py` implements this CDF. It takes a value $y$ and returns $F_2(y)$.

## 5. Pair-Correlation Distribution

The pair-correlation function $\rho_2(x)$ describes the probability density of finding two zeros with normalized spacing $x$.

### Definition
$$ \rho_2(x) = 1 - \left( \frac{\sin(\pi x)}{\pi x} \right)^2 $$
This function is used in `src/analysis/distribution_test.py` (Task T021c) to generate the theoretical baseline for local spacing, distinct from the extreme value distribution used for maximal gaps.

## 6. Summary of Constants and Parameters

| Symbol | Meaning | Default Value | Source |
|:--- |:--- |:--- |:--- |
| $N$ | Upper bound for prime generation | $10^{10}$ | `src/utils/config.py` |
| $W$ | Sliding window size | $10^6$ | `src/utils/config.py` |
| $S$ | Window step/stride | $1$ | `src/utils/config.py` |
| $GLOBAL\_SEED$ | Deterministic seed | `42` | `src/utils/config.py` |
| $C_{Cramér}$ | Normalization constant | $1$ | Cramér Model |

This model definition satisfies FR-004 (Mathematical Notation) and provides the necessary formulas for T010a and T021b.