# Statistical Interpretation Guidelines

This document provides guidance on interpreting the statistical outputs of the
cognitive fatigue analysis pipeline, particularly regarding complexity metrics
and their relationship to fatigue states.

## Correlation Analysis (US3)

### Paired Analysis (Delta vs. Delta)
- **Metric**: Change in complexity (Post - Pre) vs. Change in fatigue score.
- **Interpretation**:
 - **Negative Correlation**: As fatigue increases, complexity decreases.
 - Suggests "adaptive simplification" (system conserving resources).
 - **Positive Correlation**: As fatigue increases, complexity increases.
 - Suggests "degenerative noise" (system losing control).
- **Statistical Test**: Pearson (normal) or Spearman (non-normal) correlation.

### Cross-Sectional Analysis (Baseline vs. Baseline)
- **Metric**: Baseline complexity vs. Baseline fatigue score.
- **Usage**: Fallback when paired data is missing (per T018 logic).
- **Interpretation**: Similar to paired analysis but less robust to individual variability.

## Multiple Comparison Correction (FR-005)

- **Method**: Benjamini-Hochberg (BH) Procedure
- **Goal**: Control False Discovery Rate (FDR) across multiple electrode comparisons.
- **Threshold**: q-value ≤ 0.05
- **Reporting**: Only correlations surviving BH correction are considered statistically significant.

## Sensitivity Analysis (FR-006)

- **Purpose**: Assess robustness of findings to different significance thresholds.
- **Output**: `data/analysis/sensitivity_table.csv`
- **Interpretation**:
 - Consistent significance across p ≤ 0.05 and p ≤ 0.01 indicates strong evidence.
 - Results significant only at p ≤ 0.05 should be reported with caution.

## Collinearity Diagnostics (SC-004)

- **Metric**: Variance Inflation Factor (VIF)
- **Threshold**: VIF < 5
- **Usage**: Ensures that combined metrics (e.g., LZC + PE) are not redundant.
- **Action**: If VIF ≥ 5, metrics should be analyzed separately or dimensionality reduction applied.

## Limitations and Caveats

- **Complexity as a Proxy**: LZC and PE are proxies for system state; they do not
 directly measure neural mechanisms.
- **Sample Size**: N ≥ 30 is a minimum; larger samples improve power. [UNRESOLVED-CLAIM: c_c1a7a6ac — status=not_enough_info]
- **Artifact Residuals**: Despite rejection, some artifacts may remain; results
 should be interpreted with this uncertainty.
- **Causality**: Correlation does not imply causation; fatigue may influence complexity,
 or complexity may predict fatigue, or both may be driven by a third factor.

## Reviewer Note (David Krakauer)

Per reviewer feedback, complexity metrics should not be viewed as simple resource
depletion indicators. Instead, consider them as indicators of a "phase transition"
in the system's problem-solving capacity. A drop in complexity may represent a
shift to a more efficient, simplified state (adaptive), while an increase may
represent a loss of coherence (degenerative). The direction of correlation is
critical for distinguishing these hypotheses.