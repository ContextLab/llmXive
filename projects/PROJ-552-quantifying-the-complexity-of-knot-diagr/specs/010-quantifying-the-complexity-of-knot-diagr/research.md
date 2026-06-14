# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research investigates the relationship between combinatorial invariants (crossing number, braid index) and geometric invariants (hyperbolic volume) for prime knots. Consistent with reviewer feedback (marie-curie-simulated), measurement precision for braid index is established prior to correlation analysis. **Important**: Braid index precision validation is deferred to Phase 2+ per FR-003; Phase 0 uses tabulated values from Knot Atlas as preliminary measurements with documented uncertainty. The dataset represents prime knots with crossing number EQUAL TO a specific magnitude (corresponding count per OEIS A002863), with cumulative total for all prime knots with crossing number ≤ 13 [deferred]+ knots. The analysis prioritizes descriptive statistics (effect sizes) over inferential statistics (p-values) per Constitution Principle VII.

## Dataset Strategy

| Dataset | Source / Loader | Verification Status | Notes |
|---------|-----------------|---------------------|-------|
| Knot Atlas (Prime Knots) | `https://katlas.org` | **Canonical primary source** | FR-001 requires download from Knot Atlas. Implementation will attempt canonical source; partial results cached per FR-008. |
| KnotInfo (Reference Validation) | `https://knotinfo.org` | **Canonical primary source** | FR-013 requires cross-check against KnotInfo. Implementation will attempt canonical source for consistency check. |
| Prime Knot Counts (OEIS A002863) | `https://oeis.org/A002863` | **Verified** | Used for enumeration bounds (9988 knots AT crossing number 13). Source verified per planning prompt. |

*Note: OEIS A002863 is the only verified dataset count source. Knot Atlas and KnotInfo are documented as canonical primary sources per FR-001 and FR-013, with implementation attempting programmatic download.*

## Measurement Precision (Phase 0 Scope)

Per reviewer marie-curie-simulated, measurement precision must be established before correlation analysis.

1.  **Crossing Number**: Tabulated from Knot Atlas (well-defined).
2.  **Braid Index**: Tabulated from Knot Atlas; algorithm validation deferred to Phase 2+ (FR-003). **Braid Index Precision Disclaimer**: Precision thresholds are NOT established in Phase 0/1. Phase 0/1 analysis treats braid index as a measured quantity from the source, not as a validated algorithm output. This is a known methodological limitation that will be addressed in Phase 2+. Uncertainty is propagated in all statistical results.
3.  **Hyperbolic Volume**: Tabulated from Knot Atlas; filtered for volume > 0 (hyperbolic knots only) per FR-012.

**Precision Threshold**: Required invariant fields (crossing number, braid index, hyperbolic volume) must have null percentage ≤ 5% per field across all records in the validated dataset subset (SC-013).

## Statistical Methodology

### Census Data Exception (Constitution Principle VII)

The dataset represents a census of prime knots with crossing number EQUAL TO 13 (9988 knots per OEIS A002863). Inferential statistics (p-values, confidence intervals) are inapplicable for complete enumeration.

*   **Primary Metrics**: Effect sizes (Cohen's d for group comparisons, r/r² for correlations).
*   **Secondary Metrics**: Descriptive statistics (mean differences, variance ratios, R²/AIC/BIC).
*   **Reporting**: P-values marked as "not applicable for census data" in final reports.

### Regression Models

Three model types will be compared for associating hyperbolic volume from crossing number and braid index:
1.  Linear Regression
2.  Polynomial Regression
3.  Logarithmic Regression

**Model Selection**: Based on goodness-of-fit metrics (R², AIC/BIC, MAE), not statistical power.

**Alternating/Non-Alternating Control**: Per reviewer feedback (methodology-2910cc65), alternating/non-alternating classification will be included as a control variable in joint regression models to avoid biased estimates of the crossing number/braid index relationship with hyperbolic volume.

### Multicollinearity Acknowledgment

Braid index ≤ crossing number is a known mathematical constraint. Variance Inflation Factor (VIF) will be computed to document multicollinearity as an expected consequence of predictor structure (FR-005).

### Uncertainty Propagation

Braid index values from Phase 0 carry documented uncertainty (not validated algorithm output). All correlation and regression results in Phase 1 will propagate this uncertainty and explicitly note the exploratory nature of braid index-based analyses.

### Validation Asymmetry

Hyperbolic volume has independent cross-validation via KnotInfo (FR-013, SC-014: ≥90% match threshold). Braid index precision validation is deferred to Phase 2+ per FR-003. This asymmetry in validation rigor is a known methodological limitation. All Phase 1 statistical results involving braid index explicitly document this uncertainty and treat braid index-based findings as exploratory pending Phase 2+ validation.

## Computational Constraints

*   **Execution Budget**: Pipeline must execute within a single GitHub-Actions-class job.
*   **Partitioning**: If any stage exceeds budget, it is partitioned into resumable sub-steps and documented in `docs/reproducibility/`.
*   **Resumability**: Retry logic with exponential backoff implemented for data download (FR-008).

## Reproducibility Artifacts

All transformations documented in `docs/reproducibility/`:
*   `checksums.md`: SHA-256 hashes for all data files.
*   `logs.md`: Timestamped logs of operations.
*   `random_seeds.md`: Documented random seed values.
*   `derivation_notes.md`: Step-by-step transformation logic with formula citations.
*   `tie_breaking_rules.md`: Documented tie-breaking rules for diagram representation ties (FR-011).
*   `residual_analysis.md`: Residual analysis identifying outlier knot families (SC-011).
*   `hyperbolic_volume_validation.md`: Hyperbolic volume cross-check documentation (SC-014).
*   `correlation_results.json`: Correlation analysis results (Spearman, Pearson, effect sizes).
*   `group_comparison_metrics.json`: Group comparison metrics (mean difference, variance ratio, Cohen's d).