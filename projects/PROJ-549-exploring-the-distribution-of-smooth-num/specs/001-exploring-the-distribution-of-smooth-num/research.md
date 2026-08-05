# Research: Exploring the Distribution of Smooth Numbers in Short Intervals

## Research Question

Do $y$-smooth numbers exhibit a systematic deviation from the asymptotic predictions of the Dickman function in short intervals $[x, x+h]$ at finite scales ($x \le 10^9$), and can this deviation be quantified as a power-law scaling of the deviation ratio with interval length $h$?

## Theoretical Background

### Smooth Numbers and the Dickman Function
An integer $n$ is called $y$-smooth if all its prime factors are $\le y$. The density of $y$-smooth numbers up to $x$ is approximated by the Dickman function $\rho(u)$, where $u = \frac{\ln x}{\ln y}$. While $\rho(u)$ describes the asymptotic behavior as $x \to \infty$, its accuracy in *short* intervals $[x, x+h]$ (where $h \ll x$) is an active area of research.

### Hypothesis Refinement
The project tests the hypothesis that the **deviation ratio** $R = \frac{\rho_{observed}(h)}{\rho_{Dickman}(u)}$ scales as a power law $c \cdot h^\beta$ in the finite regime.
- **Null Hypothesis ($H_0$)**: The observed local density is consistent with the theoretical Dickman prediction for the specific $u$ of that interval ($R \approx 1$, $\beta \approx 0$).
- **Alternative Hypothesis ($H_1$)**: There is a statistically significant finite-scale effect where the ratio scales with interval length ($\beta \neq 0$).

This formulation avoids the tautology of fitting a power law to raw density (which is trivially related to $h$) and isolates the specific "finite-scale anomaly" as the object of study.

## Dataset Strategy

Since this is a synthetic computational study, the "dataset" is generated algorithmically. The strategy relies on two components:

1.  **Prime Reference Set**:
    -   **Source**: Generated via a segmented Sieve of Eratosthenes.
    -   **Verification**: The count of primes will be validated against the known value $\pi(10^9) = 50,847,534$.
    -   **Feasibility**: A segmented sieve is memory-efficient ($O(\sqrt{x})$ or $O(h)$ space) and fits within the 7 GB RAM constraint.

2.  **Interval Sampling (Balanced Grid)**:
    -   **Method**: Randomized sampling of intervals $[x, x+h]$.
    -   **Parameters**:
        -   $y \in \{100, 1000, 10000\}$
        -   **Fixed $h$ values**: $\{10^3, 10^4, 10^5, 10^6\}$. *Note: The original spec's $h=x^\alpha$ was replaced to ensure balanced sampling across all $x$ and avoid truncation bias for large $x$.*
        -   $x \in \{10^6, 10^7, 10^8, 10^9\}$
        -   $N_{samples} = 50$ per configuration.
    -   **Feasibility**: The computation is purely arithmetic (trial division). With fixed $h \le 10^6$, the total operations are well within the 6-hour window on a 2-core CPU.

## Statistical Rigor & Methodology

### Multiple Comparisons & Error Control
-   **Family-Wise Error**: Since multiple hypothesis tests (KS tests) are performed across different $y$ and $h$ configurations, the plan will apply a **Bonferroni correction** to adjust p-values.
-   **Significance Threshold**: Adhering to Constitution Principle VII, deviations are considered statistically significant only if **p < 0.01**.

### Causal Inference
-   **Observational Nature**: The study is observational. The "intervals" are sampled from the number line. Therefore, all conclusions regarding the relationship between interval length and density will be framed as **associational** (describing the statistical relationship) rather than causal.

### Measurement Validity & Theoretical Baseline
-   **Dickman Implementation**: The theoretical baseline $\rho(u)$ is computed using a custom numerical implementation in `code/dickman.py`, solving the delay-differential equation $\rho(u) = 1$ for $0 \le u \le 1$ and $u\rho'(u) = -\rho(u-1)$ for $u > 1$. This ensures the baseline is reproducible and transparent.
-   **Deviation Ratio**: For every interval, the code computes $u = \ln x / \ln y$, calculates $\rho_{theory} = \rho(u)$, and derives the ratio $R = \rho_{observed} / \rho_{theory}$. This controls for the $x$-dependence of the baseline.

### Model Fitting (Addressing Heteroscedasticity)
-   **Weighted Least Squares (WLS)**: Instead of simple OLS, the regression $\ln(R) = \ln(c) + \beta \ln(h)$ will use **Weighted Least Squares**. Weights will be derived from the Poisson variance of the count data ($w_i = 1 / \text{var}(\rho_{observed}) \approx \sqrt{\text{count}}$). This ensures that points with small counts (high relative error) do not unduly influence the fit, addressing the heteroscedasticity concern.
-   **Distribution Comparison**: The **Kolmogorov-Smirnov (KS) test** will be used to compare the empirical distribution of the deviation ratios $R$ across the 50 samples against a theoretical distribution centered at 1 (or the expected variance under the null). This replaces the ambiguous Chi-Square test for distribution comparison, aligning with Constitution Principle VII.

## Compute Feasibility (CPU-First)

-   **Memory**: The segmented sieve for $10^9$ requires storing only a small segment (e.g., 1MB-10MB) at a time, plus the final list of primes (~200MB). This is well within 7 GB RAM.
-   **Time**:
    -   Sieve: ~hours on 2 cores.
    -   Factorization: With fixed $h \le 10^6$, the total number of integers to check is $4 \text{ (x)} \times 3 \text{ (y)} \times 4 \text{ (h)} \times 50 \text{ (samples)} \times 10^6 \approx 2.4 \times 10^9$ operations. This is feasible within 240 minutes on a 2-core CPU using optimized trial division.
    -   Analysis: < 10 minutes.
-   **No GPU Required**: All operations are integer arithmetic and standard statistical tests, which run efficiently on CPU.

## Risk Mitigation

-   **Risk**: Factorization time exceeds 6 hours.
    -   **Mitigation**: The fixed $h$ grid ensures a predictable upper bound on operations. If time is tight, the grid can be reduced to fewer $x$ values without introducing bias.
-   **Risk**: Memory overflow during prime generation.
    -   **Mitigation**: Use a strictly segmented sieve with a fixed segment size (e.g., $10^6$) that fits in L2/L3 cache.
-   **Risk**: No $y$-smooth numbers found in an interval.
    -   **Mitigation**: The code handles zero counts gracefully (ratio = 0) and includes them in the statistical aggregation. The KS test handles zero values naturally.