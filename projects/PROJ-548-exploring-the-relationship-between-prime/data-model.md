# Data Model: Prime Gaps and Zeta Zero Spacings

This document defines the mathematical entities, normalization procedures, and theoretical distributions used in the analysis of the relationship between prime gaps and the Riemann Hypothesis.

## 1. Core Entities

### 1.1 Prime Gap ($g_n$)
Let $p_n$ denote the $n$-th prime number. The prime gap $g_n$ is defined as:
$$ g_n = p_{n+1} - p_n $$

### 1.2 Zeta Zero Spacing ($\delta_n$)
Let $\gamma_n$ denote the imaginary part of the $n$-th non-trivial zero of the Riemann zeta function $\zeta(s)$ on the critical line $\text{Re}(s) = 1/2$, ordered such that $0 < \gamma_1 \le \gamma_2 \le \dots$.
The average spacing between zeros near $\gamma_n$ is given by the density:
$$ \Delta_n = \frac{2\pi}{\ln \gamma_n} $$
The normalized spacing $\delta_n$ is:
$$ \delta_n = \frac{\gamma_{n+1} - \gamma_n}{\Delta_n} $$

## 2. Normalization of Prime Gaps

To compare prime gaps with the GUE predictions, we must normalize the gaps to account for the increasing density of primes.

### 2.1 Cramér Prediction
According to the Cramér model, the expected size of a gap near $p$ is $\ln p$.
However, for the distribution of *maximal* gaps in a window, the appropriate normalization involves the variance of the gap distribution.

### 2.2 Log-Squared Normalization
Following the methodology for extremal gap analysis (FR-003), we define the normalized gap $\tilde{g}$ for a gap $g$ occurring at prime $p$ as:
$$ \tilde{g} = \frac{g}{(\ln p)^2} $$
This normalization is derived from the expectation that the maximal gap in a range up to $x$ scales as $\ln^2 x$.

## 3. Theoretical Distributions

### 3.1 Pair-Correlation Distribution (GUE)
The Montgomery pair-correlation conjecture states that the statistics of normalized zero spacings match those of eigenvalues of random matrices from the Gaussian Unitary Ensemble (GUE).
The pair-correlation function for GUE is:
$$ R_2(u) = 1 - \left( \frac{\sin(\pi u)}{\pi u} \right)^2 $$
where $u$ is the normalized spacing.

### 3.2 GUE-Derived Extreme Value CDF
We are interested in the distribution of the *maximum* normalized gap within a sliding window of primes, or equivalently, the maximum spacing of GUE eigenvalues in a window.

According to random matrix theory, the distribution of the largest eigenvalue (or maximal spacing) of an $N \times N$ GUE matrix, when properly centered and scaled, converges to the **Tracy-Widom distribution** ($TW_2$) as $N \to \infty$.

Let $M_N$ be the maximum of $N$ normalized spacings (or the largest eigenvalue). The limiting cumulative distribution function (CDF) is:
$$ F_2(s) = \exp\left( - \int_s^\infty (x-s) u(x)^2 dx \right) $$
where $u(x)$ is the solution to the Painlevé II equation:
$$ u''(x) = x u(x) + 2 u(x)^3 $$
with boundary condition $u(x) \sim \text{Ai}(x)$ as $x \to \infty$ (Ai is the Airy function).

#### 3.2.1 Approximation for Implementation
For computational purposes, the CDF of the Tracy-Widom distribution ($F_2$) is approximated using the `scipy.stats` implementation or the following asymptotic expansion for the CDF:
$$ F_2(s) \approx \exp\left( - \frac{1}{16} |s|^{-3} e^{-\frac{4}{3}|s|^{3/2}} \right) \quad \text{for } s \to -\infty $$
(Note: Exact numerical evaluation via `scipy.stats.tracywidom` or integration of the Painlevé II solution is required for the analysis script).

### 3.3 Normalization Logic for Comparison
To compare the empirical maximal gap distribution $F_{\text{emp}}(x)$ against the theoretical $F_2(s)$, we must apply the same centering and scaling parameters derived from the window size $W$.

Let $x_{\text{max}}$ be the observed maximal normalized gap in a window.
The standardized variable $s$ is:
$$ s = \frac{x_{\text{max}} - \mu_W}{\sigma_W} $$
where:
- $\mu_W \approx 2 - W^{-2/3}$ (approximate mean for GUE maxima)
- $\sigma_W \approx W^{-2/3}$ (approximate scaling factor)

The theoretical CDF value for an observed maximal gap $x_{\text{max}}$ is:
$$ P(X \le x_{\text{max}}) = F_2\left( \frac{x_{\text{max}} - \mu_W}{\sigma_W} \right) $$

This formula is implemented in `src/analysis/distribution_test.py` via the `gue_extreme_value_cdf` function.

## 4. Reference
- Tracy, C. A., & Widom, H. (1994). "Level-spacing distributions and the Airy kernel". Communications in Mathematical Physics.
- Montgomery, H. L. (1973). "The pair correlation of zeros of the zeta function". Analytic Number Theory.
- Odlyzko, A. M. (1987). "On the distribution of spacings between zeros of the zeta function". Mathematics of Computation.