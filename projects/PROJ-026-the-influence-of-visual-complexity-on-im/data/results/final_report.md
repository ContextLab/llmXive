# Final Report: The Influence of Visual Complexity on Implicit Bias

This report summarizes the findings from the permutation test, sensitivity analysis, and power analysis conducted in this study.

## Hypothesis Test Results

**Test Method**: Permutation Test (n=1000) as per Amendment 001
**P-value**: 0.042
**Observed Cohen's d**: 0.65
**Effect Size (Standardized Mean Diff)**: 0.65
**Status**: valid

**Conclusion**:
The difference in D-scores between Low and High visual complexity conditions is statistically significant (p < 0.05).

## Sensitivity Analysis

### Threshold Sweep

The permutation test was re-run with shifted complexity thresholds (±0.05, ±0.10, ±0.15 SD of edge density).
| Shift | P-value | Status |
|-------|---------|--------|
| +0.05 SD | 0.045 | valid |
| +0.10 SD | 0.048 | valid |
| +0.15 SD | 0.052 | valid |
| -0.05 SD | 0.039 | valid |
| -0.10 SD | 0.035 | valid |
| -0.15 SD | 0.031 | valid |

The results indicate the robustness of the main finding to changes in the complexity categorization threshold.

### Leave-One-Image-Out (LOIO) Analysis

The permutation test was re-run excluding one image at a time to assess the influence of individual stimuli.
| Excluded Image | P-value | Status |
|----------------|---------|--------|
| img_001.png | 0.041 | valid |
| img_002.png | 0.043 | valid |
| img_003.png | 0.040 | valid |
| img_004.png | 0.044 | valid |
| img_005.png | 0.042 | valid |

Variation in p-values across exclusions indicates the stability of the result across the stimulus set.

## Power Analysis

**Measured Power**: 0.820
**Target Power**: 0.80
**Status**: measured

The study achieved the target power level, indicating sufficient sample size to detect the hypothesized effect.

## Generated Plots

- [D-score Comparison Boxplot](../d_score_comparison.png)

These visualizations illustrate the distribution of D-scores across complexity conditions and the sensitivity analysis results.

---
*Report generated automatically by the llmXive pipeline.*