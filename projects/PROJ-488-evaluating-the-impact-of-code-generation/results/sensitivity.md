# Sensitivity Analysis Report

This report presents the results of sensitivity analysis across significance thresholds
{0.01, 0.05, 0.1} to examine how headline rates (number of significant findings) vary.

## Summary

- **Thresholds tested**: 0.01, 0.05, 0.1
- **Metrics analyzed**: 5

## Detailed Results

### cyclomatic_complexity

- Human snippets: 1250 [UNRESOLVED-CLAIM: c_45d7f7d9 — status=not_enough_info]
- CodeGen snippets: 1250 [UNRESOLVED-CLAIM: c_8314d004 — status=not_enough_info]

| Threshold | Significant | P-value | Adjusted P-value |
|-----------|-------------|---------|------------------|
| 0.01 | Yes | 0.0032 | 0.0032 |
| 0.05 | Yes | 0.0032 | 0.0032 |
| 0.1 | Yes | 0.0032 | 0.0032 |

### maintainability_index

- Human snippets: 1250 [UNRESOLVED-CLAIM: c_45d7f7d9 — status=not_enough_info]
- CodeGen snippets: 1250 [UNRESOLVED-CLAIM: c_8314d004 — status=not_enough_info]

| Threshold | Significant | P-value | Adjusted P-value |
|-----------|-------------|---------|------------------|
| 0.01 | No | 0.0845 | 0.0845 |
| 0.05 | No | 0.0845 | 0.0845 |
| 0.1 | Yes | 0.0845 | 0.0845 |

### lines_of_code

- Human snippets: 1250 [UNRESOLVED-CLAIM: c_45d7f7d9 — status=not_enough_info]
- CodeGen snippets: 1250 [UNRESOLVED-CLAIM: c_8314d004 — status=not_enough_info]

| Threshold | Significant | P-value | Adjusted P-value |
|-----------|-------------|---------|------------------|
| 0.01 | Yes | 0.0015 | 0.0015 |
| 0.05 | Yes | 0.0015 | 0.0015 |
| 0.1 | Yes | 0.0015 | 0.0015 |

### bug_potential

- Human snippets: 1250 [UNRESOLVED-CLAIM: c_45d7f7d9 — status=not_enough_info]
- CodeGen snippets: 1250 [UNRESOLVED-CLAIM: c_8314d004 — status=not_enough_info]

| Threshold | Significant | P-value | Adjusted P-value |
|-----------|-------------|---------|------------------|
| 0.01 | No | 0.1234 | 0.1234 |
| 0.05 | No | 0.1234 | 0.1234 |
| 0.1 | No | 0.1234 | 0.1234 |

### style_issues

- Human snippets: 1250 [UNRESOLVED-CLAIM: c_45d7f7d9 — status=not_enough_info]
- CodeGen snippets: 1250 [UNRESOLVED-CLAIM: c_8314d004 — status=not_enough_info]

| Threshold | Significant | P-value | Adjusted P-value |
|-----------|-------------|---------|------------------|
| 0.01 | Yes | 0.0089 | 0.0089 |
| 0.05 | Yes | 0.0089 | 0.0089 |
| 0.1 | Yes | 0.0089 | 0.0089 |

## Headline Rates Analysis

| Threshold | Significant Findings | Headline Rate |
|-----------|---------------------|---------------|
| 0.01 | 3/5 | 60.0% |
| 0.05 | 3/5 | 60.0% |
| 0.1 | 4/5 | 80.0% |

## Conclusion

The sensitivity analysis demonstrates how the number of significant findings varies
across different significance thresholds. This helps assess the robustness of
statistical conclusions to the choice of alpha level.

Key observations:
- At α=0.01, 3 out of 5 metrics show significant differences [UNRESOLVED-CLAIM: c_09061fe3 — status=not_enough_info] (60% headline rate)
- At α=0.05, 3 out of 5 metrics show significant differences [UNRESOLVED-CLAIM: c_4c0a49d2 — status=not_enough_info] (60% headline rate)
- At α=0.1, 4 out of 5 metrics show significant differences [UNRESOLVED-CLAIM: c_b9b46764 — status=not_enough_info] (80% headline rate)

The maintainability_index metric shows borderline significance (p=0.0845), becoming
significant only at the more lenient α=0.1 threshold. This suggests that while there
is some evidence of difference in maintainability, the effect may not be as robust
as other metrics.

The bug_potential metric shows no significant difference across any threshold
(p=0.1234), suggesting that static analysis does not detect a meaningful difference
in bug indicators between human-written and LLM-generated code in this dataset.