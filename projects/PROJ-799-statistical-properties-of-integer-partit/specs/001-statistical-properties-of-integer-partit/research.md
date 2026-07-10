# Research: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## 1. Problem Definition

The project investigates the asymptotic behavior of $p_{\mathcal{P}}(n)$, the number of partitions of an integer $n$ into **distinct prime** summands. The generating function for this sequence is:
$$ G(q) = \prod_{p \in \mathcal{P}} (1 + q^p) $$
where $\mathcal{P}$ is the set of prime numbers.

The research question is whether the deviation between the exact count $p_{\mathcal{P}}(n)$ and the theoretical asymptotic prediction $Q_{as}(n)$ (derived from the rigorous Roth & Szekeres expansion) exhibits a systematic correlation with *higher-order* prime density metrics, specifically those not captured by the leading-order term.

## 2. Theoretical Background: Roth & Szekeres Expansion (Distinct Prime Parts)

The asymptotic behavior for distinct prime partitions is rigorously established by Roth and Szekeres. Unlike the unrestricted partition function, the generating function $\prod (1+q^p)$ involves the Prime Zeta function $P(s) = \sum p^{-s}$, which has a singularity at $s=1$ with logarithmic behavior.

The precise asymptotic expansion for $p_{\mathcal{P}}(n)$ as $n \to \infty$ is:
$$ \log p_{\mathcal{P}}(n) \sim \frac{2\pi}{\sqrt{3}} \sqrt{\frac{n}{\ln n}} \left( 1 + \frac{\ln \ln n - \ln(2\pi) - \gamma}{2 \ln n} + O\left(\frac{1}{(\ln n)^2}\right) \right) $$
where $\gamma$ is the Euler-Mascheroni constant.

The baseline $Q_{as}(n)$ used in this project is the **leading-order term** of this expansion:
$$ Q_{as}(n) = \exp\left( \frac{2\pi}{\sqrt{3}} \sqrt{\frac{n}{\ln n}} \right) $$
*Note*: The prefactor and the $O(1/\ln n)$ correction terms are **not** included in $Q_{as}(n)$. They are the target of the residual analysis. This ensures the baseline is a fixed, theoretical prediction, and the residuals $R(n)$ capture the missing higher-order structure. The regression will aim to recover these known missing terms and detect any additional systematic structure.

**Reference**: Roth, K. F., & Szekeres, G. (1954). "Some asymptotic formulae in the theory of partitions." *The Quarterly Journal of Mathematics*, 5(1), 241-259.

## 3. Dataset Strategy

There are no pre-existing datasets for $p_{\mathcal{P}}(n)$ up to $n=50,000$ in standard repositories.
**Action**: The dataset will be **generated** by the `generate_partitions.py` script using exact dynamic programming.
**Verification**:
1.  **Primes**: Generated via Sieve of Eratosthenes up to 50,000.
2.  **Partitions**: Computed via Dynamic Programming (exact integer arithmetic).
3.  **Baseline**: Computed via the leading-order Roth & Szekeres formula.

**Data Sources**:
*   Primes: Generated internally (Sieve).
*   Reference Values (for small $n$): Will be cross-referenced against OEIS A000607 (unrestricted) and manually verified small cases for distinct primes.

## 4. Feature Engineering Strategy

To explain the residual $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$, we will construct predictors that represent **higher-order** corrections, explicitly excluding the leading $1/\ln n$ term which is already in the baseline:
1.  **Higher-Order Density**: $1 / (\ln n)^2$ and $\ln \ln n / \ln n$.
2.  **Local Density**: $\pi(n) / n$ (Actual prime density).
3.  **Distance to Nearest Prime**: $d_{min}(n) = \min_{p \in \mathcal{P}} |n - p|$.
4.  **Oscillatory Terms**: $\sin(\log n)$, $\cos(\log n)$ to capture periodic fluctuations driven by the zeros of the Prime Zeta function.

## 5. Statistical Methodology

*   **Model**: Generalized Additive Model (GAM) with smooth splines for density terms and Fourier terms for periodicity. This avoids the assumption of a linear relationship and captures the non-linear structure of the error term.
*   **Hypothesis**: $R(n)$ is significantly correlated with *higher-order* density terms (e.g., $1/(\ln n)^2$) and local prime gap metrics. The analysis acknowledges that a correlation with the leading-order density term is a tautology of the baseline definition; the goal is to detect *additional* systematic structure.
*   **Validation**: 10-Fold Cross-Validation.
*   **Multiple Testing Correction**: Bonferroni correction applied to p-values of all regression coefficients to control Family-Wise Error Rate (FWER).
*   **Null Model**: Intercept-only model to establish baseline variance.
*   **Collinearity Check**: Variance Inflation Factor (VIF) calculated for all predictors. If VIF > 5, the collinear predictor is removed or combined.

## 6. Compute Feasibility & Constraints

* **Memory**: The DP array is $O(N)$ integers. $[deferred] \times \text{bytes per integer} \approx \text{memory footprint}$. Safe.
*   **Time**: $N \times \pi(N) \approx 2.5 \times 10^8$ operations. With optimized Python (NumPy), this should take $< 2$ hours on a 2-core runner. GAM fitting on large-scale datasets is trivial on CPU.
*   **Precision**: `int64` for counts. `float64` for asymptotics. Logarithms will be taken to handle large numbers.

## 7. Risks & Mitigations

*   **Risk**: The asymptotic formula $Q_{as}(n)$ is inaccurate for $n < 5000$.
    *   *Mitigation*: The regression will be performed on the full range, but we will also test a subset $n > 5000$ to see if the correlation strengthens.
*   **Risk**: $p_{\mathcal{P}}(n) = 0$ for small $n$.
    *   *Mitigation*: Filter out $n$ where $p_{\mathcal{P}}(n) = 0$ before taking logarithms.
*   **Risk**: Collinearity between $\pi(n)$ and $n/\ln(n)$.
    *   *Mitigation*: Use Variance Inflation Factor (VIF) to detect collinearity. If high, remove one predictor.