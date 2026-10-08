# Research: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## 1. Problem Formulation

The core research question is: *How does the asymptotic growth rate of the partition function $p_{\mathcal{P}}(n)$ (counting partitions of $n$ into distinct primes) deviate from the predictions of Meinardus' theorem when applied to the prime set, and can these deviations be modeled as a systematic correction term dependent on the prime density?*

This extends the classical partition problem $p(n)$ (unrestricted parts) to $p_{\mathcal{P}}(n)$ (distinct prime parts). The generating function for $p_{\mathcal{P}}(n)$ is:
$$ \sum_{n=0}^{\infty} p_{\mathcal{P}}(n) q^n = \prod_{p \in \mathbb{P}} (1 + q^p) $$
This differs fundamentally from the unrestricted partition generating function $\prod_{k=1}^{\infty} (1-q^k)^{-1}$. The distinctness constraint and the sparsity of primes ($\pi(x) \sim x/\ln x$) introduce unique combinatorial behaviors.

## 2. Theoretical Background: Meinardus' Theorem

Meinardus' theorem (1954) provides asymptotic formulas for coefficients of infinite products of the form $\prod (1-q^{a_k})^{-b_k}$. For distinct parts, the generating function is $\prod (1+q^{a_k}) = \prod (1-q^{2a_k}) / (1-q^{a_k})$.

**Applicability Check**:
Meinardus' conditions require:
1.  The Dirichlet series $D(s) = \sum a_k^{-s} b_k$ to converge for $\Re(s) > \alpha$.
2.  $D(s)$ to have a simple pole at $s=\alpha$ with residue $A$.
3.  Analytic continuation and growth conditions in the complex plane.

For distinct primes ($a_k = p_k, b_k = 1$), the relevant Dirichlet series is the Prime Zeta Function $P(s) = \sum p^{-s}$.
-   **Pole Structure**: $P(s)$ has a singularity at $s=1$ (related to the pole of the Riemann zeta function $\zeta(s)$).
-   **Derivation of Constants**: The asymptotic form $Q_{as}(n)$ depends on the residue $A$ of $P(s)$ at $s=1$ and the constant $C$ derived from the analytic continuation. Specifically, $Q_{as}(n) \sim C \cdot n^{-3/4} \exp(2\sqrt{\frac{n}{2} \cdot \frac{1}{\ln n}})$.
-   **Fallback Strategy**: If the pole structure or growth conditions are not strictly met for the finite range (or if numerical instability occurs), the plan will use a **truncated Dirichlet series approximation** to compute $Q_{as}(n)$, explicitly documenting the deviation in `applicability_report.json`.

## 3. Dataset Strategy

The study relies on computationally generated data, not external static datasets. The "dataset" is the sequence of primes and the resulting partition counts.

| Variable | Source/Method | Verification |
| :--- | :--- | :--- |
| **Primes ($p \le [deferred]$)** | Sieve of Eratosthenes | Verified against OEIS A000040 (first few terms) and $n=50,000$ count $\pi(50000) = 5133$. |
| **$p_{\mathcal{P}}(n)$** | Dynamic Programming (Batch/Stream) | Verified against known small values ($n=5, 6, 10$) and reference values for $n \le 100$. |
| **$Q_{as}(n)$** | Meinardus formula / Truncated Dirichlet | Derived from analytic number theory; constants calculated from $P(s)$ residues. |
| **Density Features** | $\pi(n)$, $1/\ln(n)$, $\sum_{p \le n} 1/p$ | Computed from the generated prime list. |

**Data Availability Note**: No external gated datasets are required. The prime list is generated on-the-fly, ensuring reproducibility and avoiding access-gated data issues.

## 4. Methodological Rigor & Statistical Plan

### 4.1. Exact Computation (FR-001)
-   **Algorithm**: 1D Dynamic Programming.
    -   Initialize `dp[0] = 1`, `dp[1..N] = 0`.
    -   Iterate through each prime $p$: `for j from N down to p: dp[j] += dp[j-p]`.
    -   **Memory Optimization**: To handle the super-polynomial growth of $p_{\mathcal{P}}(n)$ (thousands of digits at $n=50,000$), the algorithm will compute values in **batches** (e.g., $n \in [1, 1000], [1001, 2000], \dots$). Each batch is written to `partition_counts.csv` immediately and discarded from RAM. This ensures the process fits within the available RAM limit.
-   **Edge Cases**: Handle $n < 5$ (no partitions) by setting $p_{\mathcal{P}}(n)=0$. Log-residuals will exclude these cases.

### 4.2. Asymptotic Baseline (FR-002)
-   **Formula**: The distinct-partition asymptotic is roughly $Q_{as}(n) \sim C \cdot n^{-3/4} \exp(2\sqrt{\frac{n}{2} \cdot \frac{1}{\ln n}})$. (Specific constants derived from $P(1)$ and residues).
-   **Validation**: The `validate_meinardus.py` script will explicitly check the pole conditions. If conditions fail, it will switch to a truncated Dirichlet series and record the switch in `applicability_report.json`.
-   **Fallback**: If the formula yields negative/zero due to precision, clamp to $10^{-10}$.

### 4.3. Residual Analysis & Modeling (FR-003, FR-004, FR-005)
-   **Target**: $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$.
-   **Predictors**:
    1.  $X_1 = \pi(n)$ (Prime counting function).
    2.  $X_2 = 1/\ln(n)$ (Asymptotic density).
    3.  $X_3 = \sum_{p \le n} \frac{1}{p}$ (Cumulative density weighted by partition weight).
    -   *Note*: We explicitly **exclude** arbitrary trigonometric terms (sin/cos log n) as per FR-005 to avoid overfitting noise.
-   **Model**: Generalized Additive Model (GAM) or Linear Regression.
    -   $R(n) = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + \beta_3 X_3 + \epsilon$.
    -   **Null Model**: Intercept only ($R(n) = \beta_0 + \epsilon$). This is critical to ensure the correlation is not a tautology of the baseline definition.
-   **Statistical Corrections**:
    -   **Multiple Comparisons**: Apply **Benjamini-Hochberg** procedure to p-values of predictors to control False Discovery Rate (FDR).
    -   **Collinearity**: Check Variance Inflation Factor (VIF). If $X_1$ and $X_2$ are highly collinear (expected), report coefficients with caution or use regularization (Ridge).
    -   **Autocorrelation**: Since $n$ is sequential, residuals may be autocorrelated. We will use **Time-Series Cross-Validation** (blocking by $n$) and **Newey-West** standard errors to correct p-values.

### 4.4. Validation (FR-006, FR-007)
-   **Cross-Validation**: 10-fold **Time-Series CV** (blocking) on the regression model. Report Mean Squared Error (MSE) per fold and mean MSE.
-   **Visualization**: Plot $n$ vs. $R(n)$ (raw) and $n$ vs. $\hat{R}(n)$ (fitted).
-   **Success Criteria**:
    -   **SC-001**: $p < 0.05$ (adjusted) for at least one density predictor.
    -   **SC-002**: The model must show a statistically significant improvement over the Null Model (F-test or AIC comparison), rather than a fixed $R^2$ threshold, acknowledging that number-theoretic noise may keep $R^2$ low.

## 5. Compute Feasibility

- **CPU-First**: The DP algorithm is $O(N \cdot \pi(N))$. For $N=50,000$, $\pi(N) \approx [deferred]$. Operations $\approx 2.5 \times 10^8$, easily handled by 2 vCPU in < 1 hour.
- **Memory**: Batch processing ensures peak RAM < 1GB (storing only [deferred] large integers at a time).
-   **GPU**: Not required. No deep learning or large matrix inversions.
-   **Time Limit**: Full pipeline (gen, baseline, model, viz) estimated < 2 hours on free-tier runner.

## 6. Decision Rationale

-   **Why DP over recursion?** Recursion depth and overhead would be prohibitive. DP is optimal for partition counting.
- **Why Batch Processing?** Storing [deferred] integers with thousands of digits each would exceed 7GB RAM. Batch processing is the only feasible CPU-first approach.
-   **Why GAM/Linear over Neural Nets?** The sample size (50k) is small for deep learning, and the relationship is expected to be smooth/monotonic. Linear/GAM provides interpretable coefficients for the "systematic correction" hypothesis.
-   **Why Benjamini-Hochberg?** We are testing multiple predictors ($\pi(n)$, $1/\ln n$, etc.). Bonferroni is too conservative for exploratory analysis; BH controls FDR while maintaining power.
-   **Why Time-Series CV?** Standard K-fold CV assumes i.i.d. data. Since $n$ is sequential, blocking is required to prevent data leakage and ensure valid p-values.
