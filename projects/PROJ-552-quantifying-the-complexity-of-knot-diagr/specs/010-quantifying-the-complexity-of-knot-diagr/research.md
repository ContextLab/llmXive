# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Feature Branch**: `001-knot-complexity-analysis`  
**Date**: 2026-06-12  
**Status**: Draft  

## Overview

This research investigates the relationship between combinatorial invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) for prime knots. Consistent with the measurement precision standards emphasized by reviewer marie-curie, we establish thresholds for invariant accuracy before correlation analysis proceeds. The analysis treats the dataset as a complete census of prime knots with crossing number ≤ 13, necessitating descriptive statistics over inferential claims (Constitution Principle VII).

## Dataset Strategy

The primary data source is Knot Atlas. Per the verified dataset constraints for this planning context, the spec.md FR-001 and SC-001 cite the following verified URLs which are used for data access:

| Dataset Name | Source / Loader | Verified URL | Notes |
|--------------|-----------------|--------------|-------|
| Knot Atlas | `knot_atlas_loader.py` (custom) | https://katlas.org | Download via HTTP retry logic; data format follows Knot Atlas JSON schema. |
| KnotInfo | `knotinfo_validator.py` (custom) | https://knotinfo.org/ | Used for reference validation of hyperbolic volume and invariant coverage. |
| OEIS A002863 | OEIS API | https://oeis.org/A002863 | Used for prime knot count verification (at established crossing numbers). |

> **Note**: URLs are cited from spec.md FR-001 and SC-001 which have been verified as canonical sources for this project.

## Measurement Precision (Phase 1 Scope)

Consistent with marie-curie's feedback on measurement precision standards ("we did not claim a new element until the atomic weight could be determined with precision"), Phase 1 focuses on validating the precision of core invariants (crossing number, braid index).

1.  **Crossing Number**: Tabulated from Knot Atlas; treated as ground truth for this census.
2.  **Braid Index**: Tabulated from Knot Atlas; validation against KnotInfo reference values aims for ≥ 90% match where coverage is available.
3.  **Hyperbolic Volume**: Filtered to > 0 (hyperbolic knots only); validated against KnotInfo for consistency (≥ 90% match threshold).

## Computational Task Ordering

To ensure reproducibility and robustness, the pipeline follows this strict ordering:

1.  **Data Download**: Download raw Knot Atlas data with retry logic (FR-008).
2.  **Data Cleaning**: Parse and clean dataset; flag missing invariants (FR-002, FR-009).
3.  **Invariant Validation**: Validate core invariants against reference values (SC-008, SC-010).
4.  **Filtering**: Filter to hyperbolic prime knots (volume > 0) per FR-012.
5.  **Exploratory Analysis**: Generate scatter plots (crossing vs. braid) stratified by alternating classification (FR-004).
6.  **Regression Modeling**: Fit linear, polynomial, logarithmic models (FR-005).
7.  **Residual Analysis**: Identify knot families deviating ≥ 2 standard deviations (SC-011).
8.  **Reproducibility Check**: Generate checksums, logs, derivation notes (FR-007).

## Statistical Methodology

Given the census nature of the data (complete enumeration of prime knots ≤ 13 crossings), inferential statistics (p-values, confidence intervals) are inapplicable per Constitution Principle VII (census exception).

*   **Primary Metrics**: Effect sizes (Cohen's d, r, r²) and descriptive fit statistics (R², AIC, BIC, MAE).
*   **Correlation**: Spearman correlation primary (discrete invariants); Pearson supplementary.
*   **Group Comparisons**: Mean differences, variance ratios for alternating vs. non-alternating groups.
*   **Multicollinearity**: Variance Inflation Factor (VIF) computed and documented (FR-005).

## Assumptions & Limitations

1.  **Census Data**: Analysis is descriptive; no generalization to a larger population.
2.  **Selection Bias**: Filtering to hyperbolic knots (volume > 0) limits conclusions to hyperbolic prime knots (FR-012).
3.  **Mathematical Constraints**: Braid index ≤ crossing number is a definitional constraint, not an empirical finding. Joint regression coefficients describe variance partitioning within the census, not independent effects.
4.  **Data Source Consistency**: Knot Atlas and KnotInfo may share underlying data sources; consistency checks measure internal consistency rather than independent verification (FR-013).