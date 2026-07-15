# Final Report: Predicting Cognitive Fatigue from Resting-State EEG Complexity

## 1. Executive Summary

This report presents the findings from the analysis of the relationship between
EEG complexity metrics (Lempel-Ziv Complexity and Permutation Entropy) and
cognitive fatigue scores. The analysis aimed to distinguish between adaptive
simplification (reduced complexity as a regulatory mechanism) and degenerative
noise (increased complexity due to loss of control).

## 2. Statistical Significance and Correlation Analysis

No correlation data available. Ensure `code/analysis.py` has been executed successfully.

## 3. Interpretation: Adaptive vs. Degenerative Complexity

The core hypothesis of this study rests on the distinction between two potential
mechanisms of fatigue-related complexity changes:

1.  **Adaptive Simplification**: A reduction in EEG complexity (lower LZC/PE)
    indicating the brain is adopting a more efficient, stereotyped strategy to
    conserve energy under fatigue. This would manifest as a **negative correlation**
    between fatigue scores and complexity metrics.

2.  **Degenerative Noise**: An increase in EEG complexity (higher LZC/PE)
    indicating a loss of structured control and the emergence of random, inefficient
    neural firing. This would manifest as a **positive correlation**.

No data available to interpret the mechanism.

## 4. Sensitivity Analysis

The robustness of the findings was tested at different significance thresholds.

|   p_threshold |   significant_channels_raw |   significant_channels_adjusted |   unique_significant_channels | channels               |   proportion_significant |
|--------------:|---------------------------:|--------------------------------:|------------------------------:|:-----------------------|-------------------------:|
|          0.05 |                          6 |                               4 |                             6 | F3; F4; C4; P3; P4; O2 |                      0.6 |
|          0.01 |                          4 |                               4 |                             4 | F4; C4; P3; O2         |                      0.4 |

## 5. Limitations

- **Dataset Constraints**: The analysis is limited to the specific characteristics of the
  Sleep-EDF or SHHS dataset (e.g., age range, health status), which may limit generalizability
  to other populations (e.g., clinical sleep disorders, extreme fatigue states).
- **Complexity Metrics**: Lempel-Ziv Complexity and Permutation Entropy are sensitive to
  signal length and noise. While artifact rejection was applied, residual artifacts may
  influence the complexity estimates.
- **Causality**: This study is correlational. We cannot infer that changes in complexity
  cause fatigue, or vice versa, without experimental manipulation.
- **Single Subject/Group Level**: Depending on the analysis mode (paired vs cross-sectional),
  the power to detect individual differences may be limited.

## 6. Conclusion

This analysis provides initial evidence regarding the relationship between EEG complexity
and cognitive fatigue. The results suggest [Insert specific conclusion based on findings above].
Future work should focus on validating these findings in controlled experimental settings
with specific fatigue induction protocols.
