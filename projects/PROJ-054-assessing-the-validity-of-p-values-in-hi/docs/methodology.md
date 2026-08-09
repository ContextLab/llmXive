# Methodology: Assessing the Validity of p-Values in High-Dimensional Data

**Generated**: 2026-06-28 19:34:13

## 1. Overview

This study investigates the validity of standard parametric p-values (t-tests and F-tests)
in high-dimensional settings where the number of features $p$ is comparable to or exceeds
the number of samples $n$. We specifically examine how correlation structures and
distributional violations (heavy-tailed, skewed) affect the uniformity of p-values
under the null hypothesis.

## 2. Theoretical Background

### 2.1 The Null Hypothesis
Under the null hypothesis $H_0$, and assuming standard regularity conditions (independence,
normality), the p-value $P$ should follow a Uniform(0, 1) distribution.

$$ P \sim U(0, 1) $$

### 2.2 High-Dimensional Instability
In high-dimensional regimes ($n \approx p$ or $n < p$), the sample covariance matrix
becomes singular or ill-conditioned. This violates the assumptions of standard t-tests,
potentially leading to:
1. **Inflated Type I Error**: p-values cluster near 0 (anti-conservative).
2. **Deflated Power**: p-values cluster near 1 (conservative).

### 2.3 Gold Standard Reference
To quantify deviations, we establish a "Gold Standard" reference distribution using
permutation tests. By permuting labels, we preserve the correlation structure of the
data while destroying the signal, providing a valid empirical null distribution for
the specific dataset configuration.

## 3. Data Generation Methodology

### 3.1 Correlated Data Generation
We generate synthetic datasets $X \in \mathbb{R}^{n \times p}$ with a controlled
correlation structure.

1. **Covariance Construction**: A target correlation matrix $\Sigma$ is constructed
 with a discrete correlation threshold $\rho \in \{0.0, 0.1, 0.3, 0.5, 0.7, 0.9\}$.
2. **Cholesky Decomposition**: We compute $L$ such that $LL^T = \Sigma$.
3. **Transformation**: Independent standard normal vectors $Z$ are transformed:
 $$ X = Z L^T $$

### 3.2 Distributional Violations
To test robustness, we introduce non-Gaussian features:
- **Heavy-Tailed**: Samples drawn from a Student's t-distribution with low degrees of freedom ($df=3$).
- **Skewed**: Samples drawn from a Skew-Normal distribution.

### 3.3 Parameter Sweep
We sweep across:
- **Sample Size ($n$)**: Variable (see `data/sweep/params.csv`).
- **Dimensionality ($p$)**: $\{500, 1000, 2000, 5000\}$.
- **Correlation ($\rho$)**: $\{0.0, 0.1, 0.3, 0.5, 0.7, 0.9\}$.
- **Iterations**: Determined by power analysis to ensure statistical power $\ge 0.8$.

## 4. Hypothesis Testing Procedure

### 4.1 Standard Tests
For each generated dataset, we perform:
- **Two-sample t-test**: Comparing means of two groups (simulated null).
- **F-test**: Comparing variances.

These are implemented using `scipy.stats`.

### 4.2 Permutation Test (Gold Standard)
For each dataset, we run a permutation test:
1. Shuffle group labels $B$ times (e.g., $B=1000$).
2. Recalculate the test statistic for each permutation.
3. Construct the empirical null distribution.
4. Calculate the empirical p-value.

## 5. Analysis and Metrics

### 5.1 Kolmogorov-Smirnov (KS) Statistic
We quantify the deviation of the empirical p-value distribution from Uniform(0, 1)
using the KS statistic:

$$ D_{n} = \sup_x |F_n(x) - F_{ref}(x)| $$

Where $F_n$ is the empirical CDF of p-values and $F_{ref}$ is the CDF of the
Uniform(0, 1) distribution (or the permutation reference).

### 5.2 QQ-Plots
Quantile-Quantile plots are generated to visually inspect the tail behavior of the
p-value distribution against the theoretical uniform distribution.

### 5.3 Sensitivity Analysis
We analyze the relationship between the correlation parameter $\rho$ and the
resulting KS statistic to determine the threshold at which standard tests break down.

## 6. Reproducibility

All experiments are seeded. Metadata for each dataset includes:
- `seed`: Random seed used.
- `sha256`: Hash of the generated data matrix.
- `n, p, rho`: Parameters.
- `distribution_type`: Underlying distribution used.

Data artifacts are stored in `data/synthetic/` and `data/results/`.