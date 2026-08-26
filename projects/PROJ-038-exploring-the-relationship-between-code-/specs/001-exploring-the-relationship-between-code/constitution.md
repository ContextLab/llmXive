# llmXive Research Constitution
## Version 1.1 (Ratified with Amendment AMEND-001-STATS)

## Core Principles

1. **Reproducibility**: All experiments must be reproducible given the code, data, and configuration.
2. **Transparency**: All assumptions, deviations, and methodological choices must be documented.
3. **Data Integrity**: No synthetic or fabricated data may be used as a substitute for real measurements.
4. **Statistical Rigor**: Statistical methods must be appropriate for the data structure and research question.
5. **Fail Loudly**: Scripts must fail with clear errors if data cannot be fetched or processed; silent fallbacks are prohibited.
6. **Methodological Consistency**: Statistical tests must align with the study design and data characteristics.

## Original Principle VI (Statistical Methods)

> **Principle VI**: The study must utilize Pearson correlation for continuous-linear relationships and McNemar's test for paired binary classification accuracy comparisons to ensure methodological consistency with standard software engineering literature.

## Amendment AMEND-001-STATS

**Status**: RATIFIED
**Date**: 2023-10-27
**Justification**: Refer to `methodology_rationale.md` for the scientific justification.

**Text**:
In the context of the `PROJ-038-exploring-the-relationship-between-code-complexity-and-bug-prediction` project, the original Principle VI is hereby **MODIFIED** to accommodate the specific data characteristics of the Defects4J dataset and the binary nature of the bug-label target.

The following deviations are approved:
1. **Correlation Analysis**: Replace Pearson correlation with **Point-Biserial correlation** for the relationship between continuous complexity metrics and the binary bug label (`is_buggy`). Replace standard rank correlation with **Spearman’s rank correlation** where non-linear monotonic relationships are suspected or data is ordinal.
2. **Model Comparison**: Replace McNemar’s test with a **Paired Permutation Test** (10,000 permutations) to compare the distribution of ROC-AUC scores between the 'Full Metric Set' model and the 'Single Best Metric' model. This provides a non-parametric, robust validation of model differences without assuming normality of the score distributions.

This amendment ensures statistical validity while maintaining the rigor required by the Constitution.

## Compliance Checklist

- [x] Data integrity checks implemented (no synthetic fallbacks).
- [x] Statistical methods updated per Amendment AMEND-001-STATS.
- [x] Rationale documented in `methodology_rationale.md`.
- [x] Execution pipeline enforces real-data-only constraints.

## Version History

- v1.0: Initial draft (Pearson/McNemar).
- v1.1: Ratified Amendment AMEND-001-STATS (Point-Biserial/Spearman/Paired Permutation).