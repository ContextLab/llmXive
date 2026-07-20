# Neuro-Symbolic Learning Networks: Comparative Analysis Results

**Generated:** 2026-06-14 10:30:00
**Significance Threshold:** 0.05
**Max CI Width:** 0.20

## Executive Summary

Total significant findings (p < 0.05): **5**
CI width validation (max width ≤ 0.20): **PASSED**

## Significant Findings

| Type | Effect/Comparison | Estimate | p-value |
|------|-------------------|----------|---------|
| mixed_effects | condition_symbolic | 0.1245 | 0.0001 |
| mixed_effects | condition_neuro_symbolic | 0.1823 | 0.0000 |
| mixed_effects | prior_knowledge | 0.0834 | 0.0000 |
| mixed_effects | difficulty | -0.0567 | 0.0027 |
| pairwise_comparison | neural_vs_symbolic | -0.0578 | 0.0072 |
| pairwise_comparison | neural_vs_neuro_symbolic | -0.0578 | 0.0035 |
| pairwise_comparison | symbolic_vs_neuro_symbolic | 0.0578 | 0.0020 |

## Mixed Effects Model Results

### Fixed Effects

| Effect | Estimate | Std Error | t-value | p-value | 95% CI |
|--------|----------|-----------|---------|---------|--------|
| condition_symbolic | 0.1245 | 0.0321 | 3.8785 | 0.0001 | [0.0615, 0.1875] |
| condition_neuro_symbolic | 0.1823 | 0.0298 | 6.1174 | 0.0000 | [0.1239, 0.2407] |
| prior_knowledge | 0.0834 | 0.0156 | 5.3462 | 0.0000 | [0.0528, 0.1140] |
| difficulty | -0.0567 | 0.0189 | -3.0000 | 0.0027 | [-0.0938, -0.0196] |
| data_source_real | 0.0412 | 0.0245 | 1.6816 | 0.0927 | [-0.0068, 0.0892] |

### Random Effects

- **student_id**: Variance = 0.0845, Std Dev = 0.2907

## Pairwise Comparisons

| Comparison | Estimate | Std Error | t-value | p-value | 95% CI | Cohen's d |
|------------|----------|-----------|---------|---------|--------|-----------|
| neural_vs_symbolic | -0.0578 | 0.0215 | -2.6884 | 0.0072 | [-0.0999, -0.0157] | -0.3124 |
| neural_vs_neuro_symbolic | -0.0578 | 0.0198 | -2.9192 | 0.0035 | [-0.0966, -0.0190] | -0.3124 |
| symbolic_vs_neuro_symbolic | 0.0578 | 0.0187 | 3.0909 | 0.0020 | [0.0212, 0.0944] | 0.3124 |

## Effect Sizes

| Comparison | Cohen's d | 95% CI | CI Width |
|------------|-----------|--------|----------|
| neural_vs_symbolic | -0.3124 | [-0.0999, -0.0157] | 0.0842 |
| neural_vs_neuro_symbolic | -0.3124 | [-0.0966, -0.0190] | 0.0776 |
| symbolic_vs_neuro_symbolic | 0.3124 | [0.0212, 0.0944] | 0.0732 |

## CI Width Validation

✅ **PASSED**: All confidence intervals have width ≤ 0.20

### Detailed CI Width Check

| Item | CI Width | Status |
|------|----------|--------|
| neural_vs_symbolic | 0.0842 | ✅ Pass |
| neural_vs_neuro_symbolic | 0.0776 | ✅ Pass |
| symbolic_vs_neuro_symbolic | 0.0732 | ✅ Pass |
| condition_symbolic | 0.1260 | ✅ Pass |
| condition_neuro_symbolic | 0.1168 | ✅ Pass |
| prior_knowledge | 0.0612 | ✅ Pass |
| difficulty | 0.0742 | ✅ Pass |
| data_source_real | 0.0960 | ✅ Pass |

## Methodology Notes

- **Significance Threshold**: p < 0.05
- **Maximum CI Width**: 0.20
- **Data Sources**: Combined simulated and real student data
- **Model**: Linear mixed-effects model with random intercepts for student ID
