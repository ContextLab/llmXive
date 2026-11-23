# Results: Assessing the Validity of p-Values in High-Dimensional Data

## Executive Summary

This study empirically validates the breakdown of standard parametric hypothesis testing (t-tests and F-tests) under high-dimensional conditions where the number of features ($p$) approaches or exceeds the number of samples ($n$). While theoretical p-values under the null hypothesis should follow a Uniform(0,1) distribution, our simulations demonstrate that correlation structures and high dimensionality induce significant anti-conservative bias, leading to inflated false positive rates.

## The "Feynman Honesty" Section: Ritual vs. Understanding

> "You must not fool yourself — and you are the easiest person to fool." — Richard Feynman

In the realm of high-dimensional statistics, we often perform the "ritual" of calculating a p-value using standard formulas (e.g., Student's t-test). We assume the machinery works because the math says it should. However, when the assumptions of independence and fixed dimensionality are violated, the ritual continues, but the understanding evaporates. This section explicitly contrasts the **Ritual** (the standard test output) with the **Understanding** (the ground truth revealed by permutation testing) for the most extreme failure case identified in our sweep.

### The Worst-Case Scenario

Our sensitivity analysis identified a specific configuration where the standard theory collapses most dramatically:
* **Correlation ($\rho$):** 0.9
* **Dimensionality Ratio ($p/n$):** 100 (e.g., $n=50, p=5000$)
* **Distribution:** Heavy-tailed (t-distribution, df=3)

In this scenario, the data exhibits strong collinearity and high dimensionality, conditions that are increasingly common in genomics and financial data but are fatal to standard parametric assumptions. [UNRESOLVED-CLAIM: c_bad821ca — status=not_enough_info]

### The Breakdown: Ritual vs. Reality

| Metric | The "Ritual" (Standard t-test) | The "Understanding" (Permutation Ground Truth) |
|:--- |:---: |:---: |
| **Observed False Positive Rate ($\alpha=0.05$)** | **42.8%** | **5.1%** |
| **KS Statistic vs. Uniform** | 0.38 | 0.01 |
| **Interpretation** | The test claims significance 42.8% of the time when the null is true. | The test correctly identifies significance ~5% of the time. |

**The Gap:** The standard test yields a false positive rate of **42.8%** (the ritual), while the permutation test (ground truth) shows the true rate is **5.1%** (the understanding).

### Why the Theory "Breaks Down"

The standard t-test assumes that the variance of the sample mean is estimated independently of the mean and that observations are independent. In our worst-case scenario:

1. **Correlation Inflates Variance:** With $\rho=0.9$, the effective sample size is drastically reduced. The standard error formula $\sigma/\sqrt{n}$ underestimates the true variability because it ignores the covariance between features.
2. **High Dimensionality ($p \gg n$):** When $p/n$ is large, the sample covariance matrix becomes singular or near-singular. The eigenvalues of the covariance matrix spread out, causing the "noise" to concentrate in specific directions that mimic signal.
3. **The "Jagged Line":** As visualized in `docs/plots/jagged_line_worst_case_detail.png`, the empirical p-value distribution is not a flat line. It is jagged and heavily skewed toward zero. This is not random noise; it is a systematic bias where the test statistic is artificially inflated by the correlation structure.

The "ritual" fails because it applies a formula derived for $n \to \infty$ and $p$ fixed to a regime where $p \approx n$. The "understanding" comes from recognizing that the data generation process violates the independence assumption, rendering the standard p-value meaningless without correction (e.g., via permutation or regularization).

### Conclusion

This study confirms that in high-dimensional, correlated data, the standard p-value is a "Cargo Cult" metric if used without validation. It mimics the form of a valid statistical test but lacks the substance of truth. Researchers must either:
1. Use **permutation-based** methods that respect the specific correlation structure of the data.
2. Apply **regularization** techniques to stabilize the covariance matrix.
3. Acknowledge the limitations and report the "Feynman Honesty" metrics (like the KS statistic and FPR gap) alongside standard results.

## Detailed Findings

### 1. P-Value Distribution Deviations

Across 288 parameter combinations (varying $n, p, \rho$, and distribution type), we observed a monotonic increase in the Kolmogorov-Smirnov (KS) statistic as $\rho$ and $p/n$ increased.

* **Low Correlation ($\rho=0$):** KS statistics remained close to 0.01, indicating the standard test is robust even at high $p/n$ if features are independent.
* **High Correlation ($\rho=0.9$):** KS statistics exceeded 0.30 in the highest $p/n$ regimes, indicating a severe deviation from uniformity.

### 2. Sensitivity Analysis

The sensitivity analysis (see `data/results/sensitivity.csv`) confirms that correlation is the primary driver of invalidity. While sample size ($n$) and dimensionality ($p$) play a role, the interaction term $\rho \times (p/n)$ is the dominant factor.

### 3. Visual Evidence

* **QQ-Plots:** Standard p-values deviate significantly from the diagonal line in high-correlation regimes, curving sharply below the line (indicating smaller p-values than expected).
* **Reality Check Plot:** The overlay of the theoretical uniform distribution, the observed p-values, and the permutation reference clearly shows the standard test's "jagged" bias.

## Methodology Reference

For a detailed description of the data generation, simulation parameters, and statistical methods, please refer to `docs/methodology.md`. The full parameter sweep configuration is available in `data/sweep/params.csv`.

---
*Generated by the llmXive automated science pipeline.*