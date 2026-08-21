# Statistical Methodology Log
Generated: 2023-10-27 10:00:00 UTC
Significance Level (alpha): 0.05

## Test Selection Rationale
Tests were selected based on the Shapiro-Wilk normality test of latency differences.
- If p > alpha: Paired t-test used (assumption of normality met).
- If p <= alpha: Wilcoxon signed-rank test used (non-parametric).

## Per-Task-Type Analysis

### occlusion
- Sample Size: 20 [UNRESOLVED-CLAIM: c_6a55adb8 — status=not_enough_info]
- {{claim:c_e71c07c5}}
- Normality Decision: Non-Normal
- Test Selected: Wilcoxon
- Rationale: Normality assumption violated (p <= 0.05)

### depth
- Sample Size: 20 [UNRESOLVED-CLAIM: c_6a55adb8 — status=not_enough_info]
- {{claim:c_45df8fa7}}
- Normality Decision: Normal
- Test Selected: t-test
- Rationale: Normality assumption met (p > 0.05)

### relative
- Sample Size: 20 [UNRESOLVED-CLAIM: c_6a55adb8 — status=not_enough_info]
- {{claim:c_963b20cb}}
- Normality Decision: Non-Normal
- Test Selected: Wilcoxon
- Rationale: Normality assumption violated (p <= 0.05)