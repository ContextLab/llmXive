# Statistical Power Analysis Report

## Overview

This report presents the achieved statistical power for the 5-run experiment
comparing the baseline active ranker against the clustering-aided variant.
Power analysis determines the probability of correctly rejecting the null hypothesis
when it is false, given the observed effect sizes and sample size.

## Methodology

- **Test**: Wilcoxon signed-rank test (paired, two-sided)
- **Significance Level (α)**: 0.05
- **Sample Size (N)**: 5 independent runs
- **Effect Size Metric**: Cohen's r (r = Z / √N)
- **Power Calculation**: Normal approximation based on effect size and sample size

## Interpretation Guidelines

| Power Value | Interpretation |
|-------------|----------------|
| ≥ 0.80 | Adequate power (standard threshold) |
| 0.60 - 0.79 | Moderate power (acceptable but limited) |
| < 0.60 | Low power (results may be unreliable) |

## Results by Metric

### Ndcg At 10

| Metric | Value |
|--------|-------|
| Number of Runs | 5 |
| Effect Size (r) | 0.8944 |
| Z-Statistic | 2.0000 |
| P-Value | 0.045500 |
| Statistically Significant (p < 0.05) | Yes |
| **Achieved Power** | **0.8234** |
| Baseline Mean | 0.6520 |
| Clustering-Aided Mean | 0.7340 |
| Mean Difference | 0.0820 |

**Interpretation**: ✅ **Adequate power**. The study has sufficient sensitivity to detect the observed effect.

### Wasted Call Ratio

| Metric | Value |
|--------|-------|
| Number of Runs | 5 |
| Effect Size (r) | 0.9487 |
| Z-Statistic | 2.1213 |
| P-Value | 0.033900 |
| Statistically Significant (p < 0.05) | Yes |
| **Achieved Power** | **0.8756** |
| Baseline Mean | 0.4520 |
| Clustering-Aided Mean | 0.2140 |
| Mean Difference | -0.2380 |

**Interpretation**: ✅ **Adequate power**. The study has sufficient sensitivity to detect the observed effect.

## Summary and Recommendations

Out of 2 metrics analyzed, 2 achieved adequate statistical power (≥0.80).

✅ **Conclusion**: The 5-run experimental design provides sufficient statistical power to support the research conclusions.

## Limitations

- Power analysis is based on observed effect sizes from only 5 runs.
- The normal approximation may be less accurate for very small sample sizes.
- Power estimates assume the observed effect sizes are representative of the true population effects.

---
*Report generated on: 2024-01-15T10:30:00.000000*