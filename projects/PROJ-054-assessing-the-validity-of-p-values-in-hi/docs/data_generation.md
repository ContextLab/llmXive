# Data Generation Specification

## Introduction

This document details the algorithms and parameters used to generate the synthetic
datasets for the p-value validity study. The primary goal is to create data where
the null hypothesis is **known to be true by construction**, allowing us to
measure the false positive rate of standard statistical tests.

## Data Model

Each dataset is defined by the following parameters:
- **$n$**: Number of samples per group.
- **$p$**: Number of features (dimensions).
- **$\rho$**: Target correlation threshold.
- **$distribution$**: Type of marginal distribution (Normal, t-distribution, Skew-Normal).
- **$seed$**: Random seed for reproducibility.

## Generation Algorithms

### 1. Correlated Gaussian Data

To generate $n \times p$ data with correlation $\rho$:

1. Generate a $p \times p$ correlation matrix $R$ where $R_{ij} = \rho^{|i-j|}$
 (or a block structure if specified).
2. Compute the Cholesky decomposition $L$ such that $L L^T = R$.
3. Generate an $n \times p$ matrix $Z$ of independent standard normal variables.
4. Compute $X = Z L$. The rows of $X$ are now correlated with structure $R$.

**Constraint**: If the condition number of $R$ exceeds $10^{12}$, the system
raises `HighDimensionalInstabilityError` (see `code/utils/exceptions.py`).

### 2. Heavy-Tailed Data (Student's t)

1. Generate correlated Gaussian data $X$ as above.
2. Generate a scaling vector $S$ of size $n \times 1$ from a Chi-squared
 distribution with $df=3$.
3. Compute $X_{t} = X / \sqrt{S/df}$.
4. This introduces heavy tails while preserving the correlation structure.

### 3. Skewed Data (Skew-Normal)

1. Generate two independent standard normal matrices $Z_0$ and $Z_1$.
2. Compute $X = \delta |Z_0| + \sqrt{1-\delta^2} Z_1$, where $\delta$ controls
 skewness.
3. Apply the correlation transformation $L$ as in the Gaussian case.

## Output Artifacts

For each simulation run (defined by a unique seed), the following files are
produced:

1. **Metadata JSON**: `data/synthetic/{seed}.json`
 - Contains: `seed`, `n`, `p`, `rho`, `distribution_type`, `sha256`.
 - The `sha256` is the hash of the raw data matrix to ensure integrity.

2. **Trajectory Data**: `data/synthetic/trajectories/{seed}.npy`
 - Format: NumPy binary (`.npy`).
 - Content: A 2D array of shape `(iterations, p)` containing all p-values
 generated across all iterations for all features.
 - Dtype: `float32` to balance precision and storage.

## Parameter Sweeps

The `code/generate_data.py` module supports a parameter sweep logic defined in
`tasks.md` (T015):
- $p \in \{500, 1000, 2000, 5000\}$
- $\rho \in \{0.0, 0.1, 0.3, 0.5, 0.7, 0.9\}$
- $n$ varies to achieve specific $n/p$ ratios.

The resulting parameter combinations are logged to `data/sweep/params.csv`.

## Reproducibility

All random number generation is seeded using the provided `seed` parameter.
The `numpy.random.Generator` is used with `PCG64` bit generator to ensure
cross-platform reproducibility.
