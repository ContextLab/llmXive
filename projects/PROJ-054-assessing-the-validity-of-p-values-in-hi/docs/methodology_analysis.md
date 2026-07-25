# Methodology: P-Value Distribution Analysis

## Overview

This document describes the methodology for analyzing p-value distributions to assess their validity under high-dimensional data conditions and violated assumptions. The analysis quantifies deviations from the theoretical uniform distribution expected under a true null hypothesis.

## Analytical Framework

### 1. Gold Standard Reference

The analysis employs a permutation-based approach as the Gold Standard reference:
- Permutation tests preserve the exact correlation structure of the data
- They provide an empirical null distribution that respects the data's dependencies
- This reference is used to evaluate the validity of standard parametric tests

**Implementation:**
- `generate_permutation_reference()` in `code/analyze_pvalues.py`
- Multiple permutations are generated to construct a stable reference distribution
- The permutation procedure maintains the null hypothesis while respecting correlation

### 2. Kolmogorov-Smirnov (KS) Statistic

The primary metric for quantifying deviation is the KS statistic:
- Measures the maximum distance between the empirical p-value distribution and the reference
- Applied to compare standard t-test/F-test p-values against the permutation reference
- Higher KS values indicate greater anti-conservative bias

**Calculation:**
```python
KS = max|F_empirical(p) - F_reference(p)|
```
Where $F$ represents the cumulative distribution function of p-values.

### 3. QQ-Plot Analysis

Quantile-Quantile plots provide visual inspection of p-value distribution deviations:
- Plot empirical p-value quantiles against theoretical uniform quantiles
- Deviation from the diagonal line indicates bias
- Systematic patterns reveal the nature of the invalidity

**Implementation:**
- `generate_qq_plot()` in `code/plot_qq.py`
- Aggregation of p-values across iterations for stable visualization
- Confidence bands to assess statistical significance of deviations

## Sensitivity Analysis

The methodology includes systematic sensitivity analysis across correlation levels:

### Correlation Sweep

Analysis is performed across discrete correlation thresholds:
- $\rho \in \{0, 0.1, 0.3, 0.5, 0.7, 0.9\}$
- KS statistics are computed for each correlation level
- Trends reveal how correlation amplifies p-value invalidity

### Sample Size and Dimensionality

The analysis examines the interaction between:
- Sample size $n$ (small to very large)
- Dimensionality $p$ (small to very large)
- The ratio $n/p$ as a critical factor

## Bootstrap Confidence Intervals

To quantify uncertainty in KS statistics, bootstrap confidence intervals are computed:

### Procedure

1. Resample p-value trajectories with replacement
2. Recalculate KS statistic for each bootstrap sample
3. Construct percentile-based confidence intervals
4. Report lower and upper bounds with the point estimate

### Output Format

Results are stored in `data/results/bootstrap_cis.json`:
```json
{
 "KS_statistic": 0.123,
 "bootstrap_ci_lower": 0.098,
 "bootstrap_ci_upper": 0.148,
 "rho": 0.5,
 "n": 100,
 "p": 200,
 "seed": 42
}
```

## Interpretation Guidelines

### Valid p-Values

Under a true null hypothesis with valid assumptions:
- P-values follow a uniform distribution on [0, 1]
- KS statistic should be small (within sampling variability)
- QQ-plot should align with the diagonal

### Anti-Conservative Bias

When assumptions are violated (e.g., correlation, non-normality):
- P-values cluster near 0 (excess small p-values)
- KS statistic increases
- QQ-plot curves below the diagonal at low quantiles

### Severity Assessment

The magnitude of deviation indicates the severity of invalidity:
- Small KS: Minor impact, possibly acceptable
- Moderate KS: Notable bias, requires caution
- Large KS: Severe invalidity, standard tests unreliable

## Integration with Data Generation

The analysis pipeline is designed to work seamlessly with the data generation methodology:

1. **Input**: P-value trajectories from `data/synthetic/trajectories/{seed}.json`
2. **Processing**: KS calculation, QQ-plot generation, bootstrap CI
3. **Output**: Quantified deviation metrics and visual diagnostics

## Computational Considerations

### Memory Management

- Full p-value trajectories are stored to enable detailed analysis
- Bootstrap resampling is performed in chunks to manage memory
- Warning logged if RSS exceeds 6GB (Task T007)

### Reproducibility

- All analysis uses explicit random seeds
- Bootstrap iterations are deterministic given the seed
- Results are verifiable and repeatable

## Validation

The methodology includes built-in validation:
- Unit tests for KS statistic calculation (Task T024)
- Unit tests for QQ-plot generation (Task T025)
- Integration tests for full analysis pipeline

## References

- Task T026: Permutation test generator
- Task T027: KS statistic calculation
- Task T028: QQ-plot generation
- Task T029: Sensitivity analysis sweep
- Task T030: Bootstrap confidence interval calculation
- Task T024/T025: Unit tests for analysis components
