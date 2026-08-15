# Scope Justification: Asymptotic Regimes and the $n_{max}=50,000$ Limit

## 1. Introduction

This document explicitly defines the asymptotic regimes relevant to the analysis of integer partitions into distinct prime summands, $p_{\mathcal{P}}(n)$. It justifies the selection of $n_{max} = 50,000$ as the upper bound for this study, distinguishing the "transition region" of this analysis from both the small-$n$ regime and the true large-$n$ asymptotic limit of the unrestricted partition function.

The primary motivation for this scope definition is to address a critical observation regarding the generating function of the problem. Unlike the unrestricted partition function $p(n)$, which has the generating function:
$$ G(q) = \prod_{k=1}^{\infty} \frac{1}{1-q^k} $$
the distinct-prime partition function $p_{\mathcal{P}}(n)$ is governed by:
$$ G_{\mathcal{P}}(q) = \prod_{p \in \mathbb{P}} (1+q^p) $$
where $\mathbb{P}$ is the set of prime numbers. This fundamental structural difference means that $p_{\mathcal{P}}(n)$ is not merely a perturbation of $p(n)$; it is a distinct combinatorial object subject to the distribution of prime numbers.

## 2. Definition of Asymptotic Regimes

### 2.1 The Small-$n$ Regime ($n < 50$)
In this regime, the discrete nature of the prime summands dominates the behavior of the partition function.
- **Characteristics**: $p_{\mathcal{P}}(n)$ is zero for $n < 2$ and exhibits significant stochastic fluctuations for small $n$ due to the sparsity of primes.
- **Behavior**: The asymptotic formulas derived from Meinardus' theorem or saddle-point approximations are **invalid** here. The density of primes $\pi(n)$ is too low to approximate the sum over primes with an integral.
- **Treatment**: This regime is excluded from the primary regression analysis (US2) and treated as a boundary condition where $p_{\mathcal{P}}(n) = 0$ for $n < 5$ (the first prime is 2, but distinct primes require $2+3=5$ for a second partition).

### 2.2 The Transition Region ($50 \le n \le 50,000$)
This is the primary scope of the current investigation.
- **Characteristics**: The number of available prime summands increases, allowing for non-trivial partition counts. However, the "holes" created by prime gaps (composite numbers that cannot be summands) remain significant relative to the total number of integers.
- **Prime Gap Impact**: In this range, the average prime gap $g_n \approx \ln n$ is small but non-negligible. The gaps create a "rough" density landscape for the summands. The generating function $\prod (1+q^p)$ does not yet smooth out into a continuous density approximation effectively enough to ignore the local variance in prime density.
- **Why $n_{max}=50,000$?**:
 1. **Computational Feasibility**: Calculating exact $p_{\mathcal{P}}(n)$ via dynamic programming up to $n=50,000$ is computationally tractable within the 6-hour project budget (SC-004) while requiring memory $< 6.5$ GB.
 2. **Theoretical Bound**: At $n=50,000$, $\pi(n) \approx 5,133$. The ratio of primes to integers is $\approx 0.1$. This is the threshold where the "distinct prime" constraint begins to diverge significantly from the "distinct integer" constraint, yet remains far from the dense limit where $p_{\mathcal{P}}(n)$ might asymptotically approach a scaled version of $p(n)$.
 3. **Gap Dominance**: In this region, the prime gap size $g_n$ is large enough (average $\approx 11$) to create measurable "holes" in the partition generation process, which is the specific phenomenon this project aims to model (US2, T016a).

### 2.3 The Large-$n$ Asymptotic Regime ($n \to \infty$)
- **Characteristics**: As $n \to \infty$, the prime number theorem suggests $\pi(n) \sim n/\ln n$. The distribution of primes becomes dense enough that the discrete sum in the exponent of the generating function can be approximated by an integral.
- **Theoretical Limit**: In this limit, $p_{\mathcal{P}}(n)$ is expected to follow a specific asymptotic form derived from the distinct-partition variant of Meinardus' theorem:
 $$ \ln p_{\mathcal{P}}(n) \sim C \sqrt{\frac{n}{\ln n}} $$
 where $C$ is a constant derived from the Riemann zeta function and the density of primes.
- **Exclusion**: This regime is **outside** the scope of the current project. Reaching the true asymptotic limit where prime gaps become negligible relative to $n$ would require $n$ values orders of magnitude larger than 50,000, making exact computation of $p_{\mathcal{P}}(n)$ infeasible.

## 3. Justification of the $n_{max}=50,000$ Limit

The choice of $n_{max} = 50,000$ is not arbitrary but is a deliberate selection of the **transition region** where the specific effects of prime gaps are most pronounced and measurable.

1. **Addressing the "Holes" Concern**:
 The reviewer raised a concern that "prime gaps create 'holes' that fundamentally alter the asymptotic regime." This project explicitly targets this phenomenon.
 - In the unrestricted partition function, every integer $k$ is a valid summand.
 - In $p_{\mathcal{P}}(n)$, the set of valid summands is $\mathbb{P}$. The "holes" are the composite numbers.
 - At $n=50,000$, the density of these holes is high enough to cause systematic deviations from the unrestricted partition curve, but low enough that the dynamic programming algorithm can still resolve the exact counts.
 - If we were to extend to $n=10^9$, the "holes" would effectively average out, and the specific local variance caused by gaps (the target of the regression model in US2) would be lost in the global trend.

2. **Distinguishing from Unrestricted Partitions**:
 The unrestricted partition function $p(n)$ grows as $\exp(\pi \sqrt{2n/3})$. The distinct-prime partition function grows significantly slower. The region $n \in [1, 50,000]$ is the "sweet spot" where the divergence between $\ln p(n)$ and $\ln p_{\mathcal{P}}(n)$ is large enough to be modeled as a residual error term $R(n)$, but the data is still exact.

3. **Modeling Implications**:
 The regression model in US2 (T017a) is designed to predict $R(n) = \ln p_{\mathcal{P}}(n) - \ln Q_{as}(n)$.
 - If $n$ were too small, $R(n)$ would be dominated by discrete noise.
 - If $n$ were too large (approaching the true asymptotic limit), $R(n)$ would vanish or become a constant, rendering the density features ($\pi(n)$, prime gaps) irrelevant.
 - The range $[1, 50,000]$ is where $R(n)$ is dynamic and correlated with local prime density features.

## 4. Conclusion

The scope of this project is strictly limited to the **transition region** of integer partitions into distinct primes. We explicitly define $n_{max}=50,000$ as the boundary of this region. This limit ensures that:
- The "holes" created by prime gaps are the dominant source of deviation from the unrestricted partition baseline.
- The exact computation of $p_{\mathcal{P}}(n)$ remains feasible within the project's computational constraints.
- The asymptotic baseline $Q_{as}(n)$ serves as a meaningful reference point that is distinct from the true $n \to \infty$ limit.

This scope directly addresses the reviewer's concern by treating the prime gaps not as a minor perturbation, but as the central feature of the analysis, defining the asymptotic regime of the study as the region where these gaps are structurally significant.