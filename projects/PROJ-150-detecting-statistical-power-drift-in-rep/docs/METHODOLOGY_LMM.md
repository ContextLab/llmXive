# Linear Mixed-Effects Model Methodology for Statistical Power Drift Detection

## Overview

This document details the statistical methodology implemented in the `PROJ-150-detecting-statistical-power-drift-in-rep` project. The primary goal is to detect and quantify temporal drift in statistical power across replicated studies using a Linear Mixed-Effects Model (LMM).

## Statistical Model

We employ a Linear Mixed-Effects Model to account for both fixed effects (global trends) and random effects (hierarchical structure) in the data.

### Model Specification

The full model is specified as:

$$ \text{power\_est}_{ij} = \beta_0 + \beta_1 \cdot \text{year}_{ij} + \beta_2 \cdot \text{effect\_size}_{ij} + \beta_3 \cdot \text{sample\_size}_{ij} + u_{0j}^{(\text{field})} + u_{0k}^{(\text{study})} + \epsilon_{ij} $$

Where:
- $\text{power\_est}_{ij}$: The estimated statistical power for observation $i$ in field $j$ and original study $k$.
- $\text{year}_{ij}$: The publication year of the replication.
- $\text{effect\_size}_{ij}$: The observed effect size (e.g., Cohen's $d$ or Pearson's $r$).
- $\text{sample\_size}_{ij}$: The sample size of the replication study.
- $u_{0j}^{(\text{field})}$: Random intercept for the scientific field (captures field-specific baseline power).
- $u_{0k}^{(\text{study})}$: Random intercept for the original study (captures study-specific baseline power).
- $\epsilon_{ij}$: Residual error term, assumed $\epsilon_{ij} \sim \mathcal{N}(0, \sigma^2)$.

### Hypothesis Testing

The primary hypothesis of interest is whether there is a significant temporal trend in statistical power:

- **Null Hypothesis ($H_0$)**: $\beta_1 = 0$ (No drift in power over time).
- **Alternative Hypothesis ($H_1$)**: $\beta_1 \neq 0$ (Significant drift exists).

To test this, we perform a **Likelihood-Ratio Test (LRT)** comparing the full model (including `year`) against a reduced model (excluding `year`):

$$ \text{Reduced Model: } \text{power\_est} \sim \text{effect\_size} + \text{sample\_size} + (1|\text{field}) + (1|\text{original\_study\_id}) $$

The test statistic follows a Chi-squared distribution with degrees of freedom equal to the difference in the number of parameters between the models ($\Delta df = 1$).

## Implementation Details

### Data Preprocessing

1. **Missing Data Handling**: Rows with missing values in `year`, `effect_size`, or `sample_size` are excluded.
2. **Grouping Validation**: We verify that grouping factors (`field`, `original_study_id`) have:
 - More than 1 unique level.
 - Non-zero variance in the target variable (`power_est`).
 Factors failing these checks are excluded from the random effects structure with a warning logged.

### Model Fitting

- **Library**: `statsmodels` (specifically `MixedLM`).
- **Optimization**: Restricted Maximum Likelihood (REML) is used for variance component estimation, while Maximum Likelihood (ML) is used for the Likelihood-Ratio Test to ensure comparability.
- **Convergence Handling**: If the model fails to converge or estimates zero variance for a random effect, that specific effect is removed, and the model is re-fitted.

### Robustness Checks

1. **Permutation Test**: To validate the LRT results, we perform a non-parametric permutation test by shuffling `year` labels (10,000 iterations) to generate a null distribution of the drift coefficient.
2. **Sensitivity Analysis**: We sweep alpha thresholds ($\{0.01, 0.05, 0.1\}$) to assess the stability of drift significance.
3. **Cross-Field Aggregation**: Using DerSimonian-Laird weighting, we aggregate field-specific drift estimates to validate consistency across heterogeneous domains.

## Output Artifacts

The implementation generates the following key artifacts:

- `results/lmm_final_summary.json`: Contains the slope for `year`, standard error, confidence intervals, and LRT statistics.
- `data/derived/residuals.csv`: Residual power values (observed - reduced model prediction) used for visualization.
- `results/power_drift_scatter.png`: Visual representation of residual power vs. year with a fitted trend line.
- `results/permutation_pvalue.json`: Empirical p-value from the permutation test.

## References

- Bates, D., et al. (2015). Fitting Linear Mixed-Effects Models Using lme4. *Journal of Statistical Software*.
- Pinheiro, J. C., & Bates, D. M. (2000). *Mixed-Effects Models in S and S-PLUS*. Springer.
- OSF Reproducibility Project: Psychology (2015). *Science*.
