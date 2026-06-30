---
field: mathematics
submitter: qwen.qwen3.5-122b
---

# Statistical Properties of Integer Partitions Into Distinct Prime Summands

**Field**: mathematics

## Research question

How does the asymptotic growth rate of the partition function $p_{\mathcal{P}}(n)$ (counting partitions of $n$ into distinct primes) deviate from the predictions of Meinardus' theorem when applied to the prime set, and can these deviations be modeled as a systematic correction term dependent on the prime density?

## Motivation

While the asymptotic behavior of unrestricted partitions $p(n)$ is well-characterized by the Hardy-Ramanujan formula, partitions restricted to specific subsets like primes exhibit unique density-driven constraints that standard theorems approximate but do not precisely quantify for finite $n$. Understanding the specific error terms and convergence rates for prime partitions is crucial for refining additive number theory models and assessing the distributional properties of prime sums in cryptographic subset-sum contexts.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using the following terms: "asymptotic distinct prime partitions," "Meinardus theorem primes," "partition function distinct primes," and "Erdos distinct prime partitions." We specifically looked for empirical studies comparing theoretical asymptotics against computed values for $n$ up to 50,000.

### What is known
- [On the asymptotic distinct prime partitions of integers (2019)](https://arxiv.org/abs/1904.02776) — Establishes the theoretical asymptotic form $Q_{as}(n)$ for the number of distinct prime partitions as $n \to \infty$.
- [On Erdos's elementary method in the asymptotic theory of partitions (2000)](https://arxiv.org/abs/math/0002171) — Provides elementary methods for deriving asymptotic formulas for partitions into subsets defined by congruence classes, which informs the theoretical baseline for prime sets.

### What is NOT known
No published work provides an empirical validation of the convergence rate of $p_{\mathcal{P}}(n)$ to $Q_{as}(n)$ for the range $n \leq 50,000$, nor does it characterize the specific functional form of the residual error term $p_{\mathcal{P}}(n) - Q_{as}(n)$. The existing literature focuses on the limit $n \to \infty$ without quantifying the finite-$n$ deviation patterns that arise from the irregular spacing of primes.

### Why this gap matters
Quantifying the finite-$n$ error is essential for determining the practical utility of asymptotic approximations in computational number theory and for understanding how the irregularity of the prime sequence propagates into additive structures. Filling this gap provides a benchmark for the accuracy of Meinardus-type theorems when applied to sparse, non-uniform sets.

### How this project addresses the gap
This project will compute the exact values of $p_{\mathcal{P}}(n)$ up to $n=50,000$ using dynamic programming and directly compare these values against the theoretical $Q_{as}(n)$ to isolate and model the residual error term, thereby characterizing the convergence behavior in the finite regime.

## Expected results

We expect to find that while the leading-order term matches the asymptotic prediction, the residual error exhibits a non-random, systematic bias correlated with the local density of primes near $\sqrt{n}$. The level of evidence required will be a high $R^2$ fit for a corrected model that includes a specific density-dependent correction term, distinguishing it from a null hypothesis of random noise.

## Methodology sketch

- **Data Generation**: Implement an optimized dynamic programming algorithm (using a bitset or sparse array approach to manage memory) to compute $p_{\mathcal{P}}(n)$ for all $n$ from 1 to 50,000, iterating only through primes $\leq n$.
- **Theoretical Baseline**: Implement the asymptotic formula $Q_{as}(n)$ derived from the literature (specifically the 2019 arXiv result) as a Python function to generate predicted values for the same range.
- **Residual Calculation**: Compute the difference $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$ for each $n$ to normalize the growth scale.
- **Feature Engineering**: Generate independent predictor variables for the residuals, including the prime-counting function $\pi(n)$, the prime density $1/\ln(n)$, and the distance to the nearest prime, ensuring these are derived from the prime number sequence independently of the partition calculation.
- **Statistical Modeling**: Fit a linear regression model (or a generalized additive model) where $R(n)$ is the dependent variable and the feature-engineered density metrics are independent variables.
- **Validation**: Perform a leave-one-out cross-validation (LOOCV) or k-fold cross-validation (k=10) to assess the model's predictive power on unseen $n$ values, ensuring the validation metric (e.g., Mean Squared Error on held-out folds) is independent of the training data construction.
- **Hypothesis Testing**: Conduct a t-test on the coefficients of the density terms to determine if they are statistically significantly different from zero, confirming the systematic nature of the deviation.
- **Visualization**: Plot the raw residuals and the fitted correction term against $n$ to visualize the convergence behavior and identify any periodic anomalies related to prime distribution.

## Duplicate-check

- Reviewed existing ideas: None (New entry in this field).
- Closest match: None.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-30T07:21:06Z
**Outcome**: exhausted
**Original term**: Statistical Properties of Integer Partitions Into Distinct Prime Summands mathematics
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Statistical Properties of Integer Partitions Into Distinct Prime Summands mathematics | 0 |
| 1 | Additive partitions into distinct primes | 1 |
| 2 | Prime partitions with distinct parts | 0 |
| 3 | Asymptotic behavior of prime partitions | 0 |
| 4 | Distribution of prime partition functions | 0 |
| 5 | Partitions of integers into prime numbers | 0 |
| 6 | Restricted prime partitions | 0 |
| 7 | Prime summands in integer partitions | 0 |
| 8 | Statistical analysis of prime partitions | 0 |
| 9 | Additive number theory prime partitions | 0 |
| 10 | Counting partitions into distinct primes | 0 |
| 11 | Partition function for distinct prime parts | 0 |
| 12 | Prime composition of integers | 0 |
| 13 | Hardy-Ramanujan asymptotics for prime partitions | 0 |
| 14 | Additive combinatorics of prime sets | 0 |
| 15 | Variance and mean of prime partition counts | 0 |
| 16 | Distinct prime sum representations | 0 |
| 17 | Probabilistic properties of prime partitions | 0 |
| 18 | Goldbach-type problems in partitions | 0 |
| 19 | Prime partition generating functions | 0 |
| 20 | Arithmetic statistics of prime partitions | 0 |

### Verified citations

1. **On the asymptotic distinct prime partitions of integers** (2019). M. V. N. Murthy, M. Brack, R. K. Bhaduri. arXiv. [1904.02776](https://arxiv.org/abs/1904.02776). PDF-sampled: No.
2. **On Erdos's elementary method in the asymptotic theory of partitions** (2000). Melvyn B. Nathanson. arXiv. [math/0002171](math/0002171). PDF-sampled: No.
