# Power Analysis for Molecular Interaction Prediction Study

## Overview
This document details the statistical power analysis conducted to determine the minimum sample size required for the study on predicting molecular interactions in polymer composites using Graph Neural Networks. The analysis ensures the study is adequately powered to detect meaningful effects while adhering to computational constraints.

## Effect Size
- **Assumed Effect Size**: Medium (Cohen's d = 0.5)
- **Rationale**: Based on preliminary literature review of similar polymer-filler interaction studies and the expected improvement of GAT models over baseline random guessing. A medium effect size represents a practical, non-trivial improvement in prediction accuracy (MSE reduction) that would be scientifically significant for material science applications.
- **Metric**: The primary metric for effect size is the reduction in Mean Squared Error (MSE) between the trained GAT model and a baseline (random or simple heuristic) model.

## Alpha (Significance Level)
- **Value**: α = 0.05
- **Rationale**: Standard threshold for scientific research, balancing the risk of Type I errors (false positives) with the need to detect true effects. This aligns with the permutation test significance threshold used in the study's validation phase (T034).

## Power (1 - β)
- **Target Power**: 0.80 (80%)
- **Rationale**: The conventional standard for adequate statistical power, ensuring an 80% probability of correctly rejecting the null hypothesis when a medium effect size is present. This minimizes the risk of Type II errors (false negatives) while remaining feasible within the project's resource constraints.

## Required N (Sample Size)
- **Calculated Required N**: 128
- **Calculation Method**: Two-tailed t-test for independent means (comparing model performance against baseline).
 - Formula: N = 2 * ((Z_alpha/2 + Z_beta) / d)^2
 - Z_alpha/2 (for α=0.05) ≈ 1.96
 - Z_beta (for Power=0.80) ≈ 0.84
 - d (Effect Size) = 0.5
 - N ≈ 2 * ((1.96 + 0.84) / 0.5)^2 ≈ 2 * (5.6)^2 ≈ 62.72 per group
 - Total N (two groups: train/test or model vs baseline) ≈ 128
- **Contextual Adjustment**: The curated dataset target (T016) was set at ≥500 rows, which significantly exceeds the calculated minimum of 128. This provides a robust buffer for:
 - Data cleaning losses (missing values, invalid entries).
 - Train/test splits (80/20 split of 500 yields 400 training samples, well above the 64 per group minimum).
 - Increased statistical power (>99% for N=500 with d=0.5).
 - Subgroup analyses (e.g., by polymer type or filler class).

## Limitations
1. **Effect Size Estimation**: The medium effect size (d=0.5) is an estimate based on domain literature. If the true effect size is smaller (e.g., small effect d=0.2), the required N would increase to approximately 788, which may exceed the practical limits of the available MolNet dataset or computational budget for full re-training permutations.
2. **Data Availability**: The power analysis assumes the availability of a curated dataset with high-quality adhesion energy measurements. If the actual dataset size after cleaning falls below the required N (128), the study's power will be compromised, increasing the risk of Type II errors.
3. **Model Complexity**: The analysis treats the model as a "black box" for power calculation. It does not account for the internal variance introduced by the GAT architecture (e.g., dropout, random initialization) which might require a larger sample to stabilize performance metrics.
4. **Permutation Test Constraints**: While the permutation test (T033) uses 1000 iterations, the power of this non-parametric test is also dependent on the sample size. A small N might result in a coarse distribution of permuted MSEs, reducing the precision of the p-value calculation.
5. **Computational Budget**: The 6-hour runtime limit (T027) for the full training loop constrains the feasible dataset size for iterative re-training in the permutation test. If the dataset is too large, the 1000 permutations may not be executable within the time limit, forcing a reduction in iterations (which lowers power) or a smaller sample size.

## Conclusion
The study is designed with a target dataset size (N ≥ 500) that provides high statistical power (>99%) for detecting a medium effect size. This exceeds the minimum requirement (N=128) and offers a safety margin for data cleaning and split requirements. However, researchers must remain vigilant if the final curated dataset falls below 128 rows, as this would render the study underpowered for the assumed effect size. In such a case, the study would need to report the achieved power or adjust the effect size expectations accordingly.

## References
- Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.). Lawrence Erlbaum Associates.
- Field, A. (2013). Discovering Statistics Using IBM SPSS Statistics. Sage.
- Project Plan: "Critical Note on Spec Alignment" regarding dataset size and abort conditions.
- Spec FR-005: Permutation test requirements (1000 iterations).