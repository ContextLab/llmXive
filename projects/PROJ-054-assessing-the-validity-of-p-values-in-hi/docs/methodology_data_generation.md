# Methodology: Synthetic Data Generation

## Overview

This document describes the methodology used to generate synthetic high-dimensional datasets for assessing the validity of p-values under controlled correlation structures and distributional violations. The generation process ensures that the null hypothesis is true by construction, allowing for a rigorous evaluation of statistical tests.

## Data Generation Pipeline

### 1. Correlation Structure Control

The core of our data generation strategy involves creating datasets with precise correlation structures. We use a parameter $\rho$ (rho) to control the strength of correlation between variables, spanning the range from no correlation ($\rho = 0$) to strong positive correlation ($\rho = 0.9$).

**Implementation Details:**
- **Function**: `generate_correlated_data` in `code/generate_data.py`
- **Mechanism**: We construct a target correlation matrix with a specific structure where off-diagonal elements are set to $\rho$. The Cholesky decomposition is applied to this matrix to generate a transformation matrix.
- **Process**:
 1. Generate independent standard normal random variables $Z \in \mathbb{R}^{n \times p}$.
 2. Compute the Cholesky factor $L$ of the target correlation matrix $\Sigma$ (where $\Sigma_{ii}=1, \Sigma_{ij}=\rho$).
 3. Transform the data: $X = Z L^T$.
- **Verification**: The generated data's empirical correlation matrix is checked against the target $\rho$ within numerical tolerance.

### 2. Distributional Violations

To assess robustness, we introduce controlled violations of the normality assumption, which is a prerequisite for standard t-tests and F-tests.

**Supported Distributions:**
- **Heavy-Tailed (Student's t)**: Generated using `scipy.stats.t.rvs` with a specified degrees of freedom ($df$). Low $df$ values (e.g., $df=3$) introduce significant heavy tails, challenging the central limit theorem in small samples.
- **Skewed Normal**: Generated using `scipy.stats.skewnorm.rvs` with a shape parameter $\alpha$. Positive $\alpha$ induces right skew, while negative $\alpha$ induces left skew.

**Implementation Details:**
- **Function**: `generate_distribution_violations` in `code/generate_data.py`
- **Process**: After generating the base correlated Gaussian data, we apply a component-wise transformation or directly sample from the target distribution while preserving the correlation structure via copula-like methods or direct generation if the distribution supports it.

### 3. Parameter Sweeps

We conduct a systematic sweep over key parameters to map the behavior of p-values across different regimes:
- **Sample Size ($n$)**: Ranging from small ($n=20$) to large ($n=1000$).
- **Dimension ($p$)**: Categorized as small, medium, large, and very large.
- **Correlation ($\rho$)**: Discrete values $\{0, 0.1, 0.3, 0.5, 0.7, 0.9\}$.
- **Distribution Type**: Normal, t-distribution, skewed normal.

The iteration count for each configuration is determined by the power analysis utility (`code/utils/simulation.py`) to ensure statistical power $\ge 0.8$ for detecting deviations in the KS statistic.

### 4. Null Hypothesis Validity

A critical feature of our methodology is that the null hypothesis is **true by construction**.
- We generate data for two groups (or conditions) from the *same* underlying distribution with identical means.
- Any rejection of the null hypothesis by standard tests is therefore a Type I error, directly measuring the inflation of false positives.

## Output Artifacts

- **Metadata Files**: `data/synthetic/{seed}.json` containing `sha256`, `rho`, `n`, `p`, `distribution_type`, and `seed`.
- **Trajectory Files**: `data/synthetic/trajectories/{seed}.json` storing full p-value trajectories for downstream analysis.
