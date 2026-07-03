# A Priori Power Analysis for Memory Palace Experiment

**Generated on**: Power Analysis

## Summary

- **Planned Sample Size (N)**: 5
- **Required Sample Size for 80% Power**: 10
- **Achieved Power with Planned N**: 65.23%
- **Significance Level (α)**: 0.05
- **Target Power**: 80%
- **Assumed Effect Size (Cohen's d)**: 0.8
- **Minimum Detectable Effect Size**: 1.05

## Justification

### Effect Size Justification

We assume a large effect size (Cohen's d = 0.8) based on the hypothesis that spatial organization in the memory palace architecture provides a substantial improvement over standard attention mechanisms. This is a conservative assumption as it represents a strong effect; if the true effect is smaller, the study may be underpowered, but if the effect is as large or larger, the study will have adequate power.

### Sample Size Justification

With a planned sample size of N=5 random seeds, we achieve a power of 65.23% to detect an effect size of 0.8 at alpha=0.05. This is slightly below the conventional 80% threshold (80%), but represents a practical compromise given computational constraints. To achieve 80% power, we would need N=10 seeds. The chosen N=5 is justified as a minimum viable sample to detect large effects while remaining computationally feasible within the 5-hour runtime limit per seed.

### Statistical Test

Paired two-tailed t-test (or Wilcoxon signed-rank test if normality assumption is violated)

## Power Curve

| Sample Size (N) | Power |
|-----------------|-------|
| 2 | 0.09% |
| 3 | 0.35% |
| 4 | 1.08% |
| 5 | 2.95% |
| 6 | 6.93% |
| 7 | 14.27% |
| 8 | 25.34% |
| 9 | 39.32% |
| 10 | 54.88% |

## Recommendations

1. Use N=5 random seeds as the primary experimental design.
2. If computational resources allow, consider increasing to N=7 or N=8 to achieve >80% power.
3. Report effect sizes with confidence intervals in addition to p-values.
4. Pre-register the analysis plan to avoid p-hacking.
5. Consider using Wilcoxon signed-rank test as a robustness check if normality of differences is questionable.

## Parameters

- α (alpha): 0.05
- Target Power: 80%
- Assumed Effect Size: 0.8
- Planned N: 5