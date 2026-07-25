# Methodology: Synthetic High-Dimensional Data Generation

## Overview

This document describes the methodology for generating synthetic high-dimensional datasets used to assess the validity of p-values under controlled violations of statistical assumptions. The generation process is designed to produce data with known ground-truth properties, enabling rigorous empirical evaluation of hypothesis testing procedures.

## Core Principles

### 1. Controlled Correlation Structures

The synthetic datasets are generated with precisely controlled correlation structures parameterized by a discrete correlation threshold $\rho$. The correlation matrix is constructed to span a range from no correlation ($\rho = 0$) to strong positive correlation ($\rho = 0.9$).

**Implementation Details:**
- Correlation matrices are generated using a factor model approach
- Discrete thresholds: $\rho \in \{0, 0.1, 0.3, 0.5, 0.7, 0.9\}$
- The correlation structure is verified post-generation to ensure numerical accuracy within tolerance

### 2. Sample-to-Dimension Ratios

The methodology systematically varies the relationship between sample size $n$ and dimensionality $p$:

- **Small**: $n < p$ (underdetermined regime)
- **Medium**: $n \approx p$ (boundary regime)
- **Large**: $n \gg p$ (classical regime)
- **Very Large**: $n \ggg p$ (asymptotic regime)

This sweep enables analysis of how p-value validity degrades as the dimensionality increases relative to sample size.

### 3. Distributional Violations

To test the robustness of standard hypothesis tests, the methodology introduces controlled violations of the normality assumption:

- **Heavy-tailed distributions**: Student's t-distribution with low degrees of freedom
- **Skewed distributions**: Skew-normal distribution with varying skewness parameters

These violations are applied while maintaining the null hypothesis condition (no mean differences between groups) to isolate the effect of distributional assumptions on p-value validity.

## Data Generation Pipeline

### Step 1: Parameter Configuration

Each dataset generation is controlled by a configuration specifying:
- Sample size $n$
- Dimensionality $p$
- Correlation threshold $\rho$
- Distribution type (normal, t-distribution, skew-normal)
- Random seed for reproducibility

### Step 2: Correlation Matrix Construction

The correlation matrix $\Sigma$ is constructed to reflect the specified correlation structure:
1. Generate a base correlation structure
2. Apply the discrete correlation threshold $\rho$
3. Verify the resulting matrix is positive semi-definite
4. Apply regularization if condition number exceeds $10^{12}$

### Step 3: Data Generation

Data is generated from a multivariate distribution with:
- Mean vector $\mu = 0$ (ensuring true null hypothesis)
- Covariance structure defined by $\Sigma$
- Marginal distributions matching the specified distribution type

### Step 4: Metadata and Verification

Each generated dataset is accompanied by metadata stored in `data/synthetic/{seed}.json`:
- SHA256 hash of the dataset for integrity verification
- Generation parameters ($\rho$, $n$, $p$, distribution_type, seed)
- Verification that the correlation structure matches specifications

## Power Analysis and Iteration Count

The number of simulation iterations is determined by a power analysis (Task T008) to ensure:
- Statistical power $\geq 0.8$ for detecting a Kolmogorov-Smirnov statistic deviation $> 0.05$
- Sufficient samples to construct reliable confidence intervals for KS statistics
- Balance between computational cost and statistical precision

## Memory Management

The generation process includes memory monitoring to prevent system overload:
- Warning logged if RSS exceeds 6GB (Task T007)
- No hard error raised for memory threshold (as it is not in the specification)
- Regularization applied for high condition numbers to prevent numerical instability

## Output Artifacts

Generated data is stored in the following structure:
- `data/synthetic/{seed}.json`: Dataset metadata and hash
- `data/synthetic/trajectories/{seed}.json`: Full p-value trajectories for analysis

## Reproducibility

All generation is controlled by explicit random seeds, ensuring:
- Exact reproducibility of datasets
- Independent verification of results
- Consistent comparison across different parameter configurations

## References

- Task T013: Implementation of `generate_correlated_data`
- Task T014: Implementation of distributional violation generators
- Task T015: Parameter sweep logic
- Task T016: Metadata writing and verification
- Task T017: Trajectory storage
- Task T008: Power analysis utility
- Task T007: Memory monitoring
- Task T004: Covariance regularization
