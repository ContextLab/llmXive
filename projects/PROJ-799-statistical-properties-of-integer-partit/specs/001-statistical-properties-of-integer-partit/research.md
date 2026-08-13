# Research: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## Overview

This research investigates the deviation of the partition function $p_{\mathcal{P}}(n)$ (partitions of $n$ into distinct primes) from the asymptotic predictions of Meinardus' theorem. The core hypothesis is that the finite-regime error term $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$ is systematically correlated with prime density features, indicating a correction term dependent on the distribution of primes.

## Asymptotic Baseline: Meinardus' Theorem for Distinct Primes

### Theoretical Background

Meinardus' theorem provides an asymptotic formula for the coefficients of Dirichlet series generating functions. For unrestricted partitions, the generating function is $\prod_{k=1}^\infty (1-q^k)^{-1}$. For distinct prime partitions, the generating function is:
$$ \prod_{p \in \mathbb{P}} (1 + q^p) $$
This is a product over primes only, with each prime appearing at most once (distinct parts).

The asymptotic behavior of $p_{\mathcal{P}}(n)$ is given by:
$$ Q_{as}(n) \sim C n^{-\alpha} \exp\left( A n^{\beta} \right) $$
where $A$, $\alpha$, and $\beta$ are constants derived from the Dirichlet series of the prime set. Specifically, for distinct prime partitions, the exponent $\beta = 1/2$ (similar to unrestricted partitions), but the constant $A$ is derived from the prime zeta function $P(s) = \sum_{p} p^{-s}$.

### Derivation of $Q_{as}(n)$

Following Meinardus and Andrews (1998), the leading term for $p_{\mathcal{P}}(n)$ is derived from the generating function $\prod (1+q^p)$. The constant $A$ is given by:
$$ A = \sqrt{2 P(2)/3} $$
where $P(2) = \sum_{p} p^{-2}$ is the prime zeta function evaluated at $s=2$. Note that $P(s)$ yields a value distinct from $\zeta(s)$, where $\zeta(s)$ is the Riemann zeta function. The formula is:
$$ \log Q_{as}(n) \approx \sqrt{\frac{2 P(2) n}{3}} $$
The leading-order term depends on $\sqrt{n}$ and the constant $P(2)$. **Crucially, the term $1/\ln(n)$ does NOT appear in the leading-order exponent of $Q_{as}(n)$**. The $1/\ln(n)$ term appears in the *error* of the Prime Number Theorem, which drives the deviation.

**Verification**: This formula will be validated against known small values ($n \le 100$) where $p_{\mathcal{P}}(n)$ is known. Discrepancies will be analyzed as part of the residual study. The constant $A$ is fixed based on the Prime Zeta function to ensure the baseline is independent of the higher-order predictors used in the regression.

## Dataset Strategy

### Data Source: Primes

- **Source**: Generated on-the-fly using Sieve of Eratosthenes.
- **Range**: Primes up to $n_{max} = 50,000$.
- **Verification**: The sieve is deterministic and verified against known prime counts ($\pi([deferred]) = 5,133$).
- **No External Download**: Eliminates dependency on external datasets, ensuring reproducibility.

### Data Generation: $p_{\mathcal{P}}(n)$

- **Method**: Dynamic programming with 1D array optimization.
- **Memory**: Array size $\approx [deferred]$ arbitrary-precision integers (estimated ~2-3 GB), well within 7 GB RAM.
- **Algorithm**:
  ```python
  dp = [0] * (n_max + 1)
  dp[0] = 1
  for p in primes:
      for n in range(n_max, p - 1, -1):
          dp[n] += dp[n - p]
  ```
  This ensures each prime is used at most once (distinct parts).

### Data Generation: $Q_{as}(n)$

- **Method**: Direct evaluation of the asymptotic formula using $A = \sqrt{2 P(2)/3}$.
- **Edge Cases**: $Q_{as}(n)$ clamped to $\ge 10^{-10}$ to avoid log(0).

### Residual Calculation

- **Formula**: $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$.
- **Filtering**: Rows with $p_{\mathcal{P}}(n) = 0$ or $Q_{as}(n) \le 0$ are excluded.

## Feature Engineering

### Density Features

1. **$\pi(n)$**: Prime-counting function (number of primes $\le n$).
2. **$1/(\ln n)^2$**: Inverse squared logarithmic density (to avoid direct coupling with $Q_{as}(n)$ which uses $\sqrt{n}$ and $P(2)$).
3. **Distance to Nearest Prime**: $|n - \text{nearest\_prime}(n)|$ (absolute difference to the closest prime, either smaller or larger). This captures local fluctuations in the prime distribution. While $p_{\mathcal{P}}(n)$ is global, the *error term* in the Prime Number Theorem (which drives the asymptotic approximation) is locally sensitive to prime gaps. Thus, local gap features may capture systematic deviations in the approximation error.
4. **Oscillatory Terms**: $\sin(\log n)$, $\cos(\log n)$ to capture periodic fluctuations related to Riemann zeros.
5. **Global Gap Variance**: Variance of prime gaps up to $n$ (to capture global fluctuations and balance the local feature).

### Rationale

- **$\pi(n)$ and $1/(\ln n)^2$**: Capture global prime density trends and higher-order corrections.
- **Distance to Nearest Prime**: Captures local fluctuations. Justified by the sensitivity of the PNT error term to local prime gaps.
- **Oscillatory Terms**: Account for potential periodic components in the error term (e.g., related to the Riemann zeros).
- **Avoiding Circularity**: Predictors are explicitly chosen to be orthogonal to the leading-order term of $Q_{as}(n)$ (which uses $\sqrt{P(2)}$ and $\sqrt{n}$) to ensure the residual analysis is not tautological. Specifically, $1/(\ln n)^2$ is used instead of $1/\ln(n)$ to ensure no direct coupling, and the leading term of $Q_{as}(n)$ does not contain $1/\ln(n)$.

## Regression Model

### Model Choice

- **Primary**: Linear regression with regularization (Ridge/Lasso) to handle collinearity.
- **Secondary**: Generalized Additive Model (GAM) for non-linear relationships.
- **Null Model**: Intercept-only model to establish baseline (FR-008).

### Hypothesis Testing

- **Null Hypothesis**: Coefficients for density features are zero ($H_0: \beta_i = 0$).
- **Alternative**: At least one coefficient is non-zero.
- **Correction**: Bonferroni and Benjamini-Hochberg corrections for multiple comparisons (SC-005).
- **Autocorrelation**: Newey-West standard errors (or HAC estimators) will be used to correct p-values for serial correlation in $R(n)$.

### Cross-Validation

- **Method**: 10-fold cross-validation.
- **Metric**: Mean Squared Error (MSE).
- **Goal**: Assess generalizability and avoid overfitting.

## Statistical Rigor

### Multiple Comparisons

- **Method**: Bonferroni and Benjamini-Hochberg corrections applied to p-values.
- **Threshold**: $\alpha_{corrected} = 0.05 / k$, where $k$ is the number of predictors.

### Power Analysis

- **Sample Size**: $n=50,000$ provides high power to detect small effect sizes.
- **Effect Size**: Expected $R^2 \ge 0.05$ (SC-002).

### Collinearity

- **Check**: Variance Inflation Factor (VIF) for each predictor.
- **Mitigation**: Regularization (Ridge) if VIF $> 5$.

### Measurement Validity

- **Primes**: Exact by definition.
- **Partitions**: Exact via DP (no approximation).
- **Asymptotics**: Theoretical formula with known error bounds (verified against Meinardus/Andrews).

### Circularity Avoidance

- The leading-order term of $Q_{as}(n)$ is derived solely from the Prime Zeta function constant $P(2)$ and $\sqrt{n}$.
- Predictors such as $1/(\ln n)^2$, oscillatory terms, and gap variance are distinct from this leading term.
- The residual $R(n)$ measures the deviation of the *true* partition count from this specific leading-order baseline.
- Regressing $R(n)$ on these predictors tests if the *error* in the leading-order approximation correlates with higher-order density features, which is a valid non-tautological inquiry.

### Null Model

- An intercept-only model (constant prediction) will be fitted.
- Its performance (MSE, $R^2$) will be compared to the full model to ensure the density features add explanatory power.

## Decision/Rationale

- **CPU-First**: All computations are CPU-tractable; no GPU needed.
- **Data Generation**: On-the-fly prime generation ensures reproducibility and avoids external dependencies.
- **Model Choice**: Linear regression with regularization balances interpretability and performance. GAMs provide a robustness check for non-linearities.
- **Feature Set**: Includes global density, local gaps (justified by PNT error sensitivity), and oscillatory terms to capture the full spectrum of potential deviations. Predictors are orthogonal to the leading-order asymptotic term to avoid tautology.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| $Q_{as}(n)$ inaccurate for small $n$ | Exclude $n < 5$ from residual analysis; validate against known values. |
| Collinearity between $\pi(n)$ and $1/(\ln n)^2$ | Use Ridge regression; check VIF. |
| Overfitting in regression | 10-fold cross-validation; regularization. |
| Memory overflow in DP | 1D array optimization; monitor memory usage (expected ~2-3 GB). |
| Autocorrelation in residuals | Use Newey-West standard errors. |

## References

- Meinardus, G. (1954). *Asymptotische Aussagen über Partitionen*. Mathematische Zeitschrift.
- Andrews, G. E. (1998). *The Theory of Partitions*. Cambridge University Press.
- Hardy, G. H., & Ramanujan, S. (1918). *Asymptotic formulae for the distribution of integers*. Proceedings of the London Mathematical Society.
