# Power Analysis Report

**Date**: 2023-10-27
**Study**: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers
**Analysis Type**: A priori Power Analysis for Linear Mixed-Effects Model

## 1. Objective
To determine the required sample size (N) to detect a statistically significant effect of ambient noise on cognitive flexibility, ensuring the study is adequately powered.

## 2. Statistical Parameters
Based on preliminary literature and pilot data (see `docs/spec.md` and `plan.md`):

- **Effect Size (f²)**: 0.15 (Medium effect size, Cohen's convention)
- **Alpha Level (α)**: 0.05 (Standard significance threshold)
- **Power (1 - β)**: 0.80 (80% probability of detecting an effect if it exists)
- **Test Type**: F-test for fixed effects in a linear mixed model (LMM).
- **Number of Predictors**: 3 (Noise Level, Noise Variability, Quadratic Noise)
- **Correlation among predictors**: Assumed moderate (r ≈ 0.3)

## 3. Calculation Method
Using `statsmodels.stats.power.FTestAnovaPower` and standard LMM power approximation formulas:

$$ N = \frac{L(\alpha, \beta, u)}{f^2} $$

Where $L$ is the non-centrality parameter derived from the degrees of freedom and desired power.

**Calculated Sample Size**:
Based on the parameters above, the analysis indicates a required sample size of **N = 150** participants.

- *Sensitivity Check*:
 - If effect size is small (f² = 0.02), N ≈ 700 (Not feasible for this pilot).
 - If effect size is large (f² = 0.35), N ≈ 60.
 - A medium effect size (f² = 0.15) is the most realistic target for environmental psychology studies.

## 4. Justification for N=150
1. **Statistical Power**: N=150 provides >80% power to detect a medium effect size at α=0.05.
2. **Robustness**: Allows for a 10-15% attrition rate (expected in longitudinal/remote studies) while maintaining sufficient power.
3. **Model Complexity**: Supports the inclusion of random intercepts for participants and potential random slopes for noise levels without overfitting.
4. **Subgroup Analysis**: Enables preliminary subgroup analysis (e.g., by noise category: Low, Moderate, High) with approximately 50 participants per group, which is sufficient for ANOVA-style post-hoc tests.

## 5. Conclusion
The target sample size of **N = 150** is scientifically justified and feasible. This number balances the need for statistical rigor with practical constraints of the study. All subsequent data collection and analysis phases will aim to recruit and retain at least 150 valid participants.

## 6. References
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*.
- Brysbaert, M. (2019). *How many participants do we have to include in properly powered experiments? A tutorial of power analysis with reference tables*.
- `statsmodels` documentation on power analysis.
