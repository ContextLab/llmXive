# Deviation Report: FR-004 Target Permutation Test

## Summary
This document formally records the methodological deviation from the original Feature Specification (FR-004) regarding the "Target Permutation Test" and confirms the adoption of the "Feature Permutation Test" as implemented in the `src/modeling/significance_test.py` module.

## Original Specification (FR-004)
The original specification mandated a "Target Permutation Test" involving the shuffling of the target variable ($Y$) to establish a null distribution for model performance.

## Reason for Deviation
The "Target Permutation Test" was deemed **methodologically invalid** for the specific goal of predicting the impact of impurities on superconductivity ($T_c$) for the following reasons:

1. **Invalid Null Hypothesis**: Shuffling the target variable ($Y$) tests the null hypothesis that "there is no relationship between *any* features and the target." While this is a valid test for overall model significance, it does not isolate the impact of *specific* impurities. It destroys the signal globally, making it impossible to attribute performance degradation to specific feature interactions.
2. **Incompatibility with Feature Importance**: The project goal is to quantify the $\Delta T_c$ per atomic % for specific impurities. A target permutation test yields a single global p-value for the model's existence, not a p-value for individual feature coefficients or contributions.
3. **Methodological Standard**: In regression analysis and feature attribution, the standard method for assessing the significance of a specific predictor (impurity) while controlling for others is **Feature Permutation Importance** (shuffling the specific feature column $X_i$) or statistical inference on coefficients (ANOVA/t-tests), not target shuffling.

## Adopted Methodology: Feature Permutation Test
Per the Implementation Plan's correction to FR-004, the system implements **Feature Permutation Importance**:
- **Mechanism**: The specific feature column (e.g., `impurity_C_atomic_pct`) is shuffled while all other features and the target remain intact.
- **Logic**: The model's performance (e.g., $R^2$ or MAE) is recalculated on the permuted data.
- **Significance**: The drop in performance relative to the baseline (unpermuted) model quantifies the importance of that specific impurity.
- **Implementation**: This logic is implemented in `src/modeling/significance_test.py` via the `run_feature_permutation` function, which generates a null distribution for specific features and calculates p-values.

## Verification
- **Code Artifact**: `src/modeling/significance_test.py` implements `run_feature_permutation` and `run_anova`.
- **Test Artifact**: `tests/unit/test_significance.py` verifies the generation of null distributions and p-value calculations for individual features.
- **Output**: The pipeline generates `data/processed/significance_results_reduced.json` containing p-values for specific impurity features, satisfying the requirement to validate impurity impact significance (p < 0.05).

## Conclusion
The deviation from "Target Permutation" to "Feature Permutation" is necessary to achieve the scientific objective of the project: isolating and quantifying the causal impact of specific impurities on $T_c$. The original specification's method would have produced a global model validity metric insufficient for feature-level attribution.