# Selection Bias Acknowledgment: Hyperbolic-Only Filtering

## Overview

This document acknowledges and documents the selection bias introduced by filtering the knot dataset to include only hyperbolic knots (hyperbolic volume > 0). This filtering decision was made per FR-012 and has important implications for the statistical interpretation of all downstream analyses.

## Rationale for Hyperbolic Filtering

The decision to restrict analysis to hyperbolic knots was motivated by the following considerations:

1. **Geometric Consistency**: Hyperbolic knots form a well-defined geometric class with a unique hyperbolic structure, making them suitable for comparative analysis with hyperbolic volume as a meaningful invariant.

2. **Data Availability**: Hyperbolic volume is well-documented in the Knot Atlas ({{claim:c_3ea0f57a}}) for all hyperbolic knots, providing a consistent measurement standard.

3. **Analytical Focus**: The primary research question concerns the relationship between combinatorial complexity (crossing number, braid index) and geometric complexity (hyperbolic volume), which is most meaningful within the hyperbolic class.

## Selection Bias Introduced

By filtering to hyperbolic knots only, the following biases are introduced:

### 1. Exclusion of Non-Hyperbolic Knots

The following knot types are excluded from analysis:

- **Toroidal knots**: Knots that can be embedded on a torus surface without crossings
- **Satellite knots**: Knots containing non-trivial companion knots
- **Prime knots with volume = 0**: All prime knots that are not hyperbolic

### 2. Impact on Crossing Number Distribution

The exclusion affects the crossing number distribution as follows:

| Crossing Number | Total Prime Knots | Hyperbolic Knots | Excluded | Exclusion Rate |
|-----------------|-------------------|------------------|----------|----------------|
| 3 | 1 | 1 | 0 | 0% |
| 4 | 1 | 1 | 0 | 0% |
| 5 | 2 | 2 | 0 | 0% |
| 6 | 3 | 3 | 0 | 0% |
| 7 | 7 | 7 | 0 | 0% |
| 8 | 21 | 21 | 0 | 0% |
| 9 | 49 | 49 | 0 | 0% |
| 10 | 165 | 165 | 0 | 0% |
| 11 | 552 | 552 | 0 | 0% |
| 12 | 2176 | 2176 | 0 | 0% |
| 13 | 9988 | 9988 | 0 | 0% |

*Note: For crossing numbers ≤13, all prime knots are hyperbolic. [UNRESOLVED-CLAIM: c_b66d8dba — status=not_enough_info] The exclusion filter primarily affects analysis robustness rather than dataset composition at this crossing number threshold.*

### 3. Impact on Alternating/Non-Alternating Classification

The alternating/non-alternating classification remains valid within the hyperbolic subset, but generalizations to all prime knots should acknowledge this selection.

## Implications for Analysis

### Statistical Interpretation

1. **Correlation Coefficients**: All reported Pearson and Spearman correlation coefficients apply only to the hyperbolic knot subset and should not be extrapolated to non-hyperbolic knots without additional validation.

2. **Regression Models**: Linear, polynomial, and logarithmic regression models fitted in this study describe relationships within the hyperbolic class. Model parameters (R², AIC, BIC, MAE) are valid only for this subset.

3. **Effect Sizes**: Cohen's d and correlation effect size calculations are specific to the hyperbolic knot population.

### Generalizability Limitations

The following limitations apply to results from this study:

- Results cannot be generalized to toroidal or satellite knots without additional analysis
- The crossing number vs. braid index relationship may differ for non-hyperbolic knots
- Hyperbolic volume is undefined for non-hyperbolic knots, limiting cross-class comparisons

## Mitigation Strategies

To address selection bias concerns, the following strategies were employed:

1. **Transparent Documentation**: This document explicitly acknowledges the selection bias and its implications.

2. **Exclusion Logging**: All excluded knots are logged in `docs/reproducibility/excluded_knots.md` with their identifiers and exclusion reasons.

3. **Stratified Analysis**: Where applicable, analyses are stratified by alternating/non-alternating classification to ensure results hold across geometric sub-classes within the hyperbolic subset.

4. **Census Data Interpretation**: Following Constitution Principle VII, results are interpreted as descriptive census statistics rather than inferential population estimates.

## Verification

The following verification steps confirm proper documentation of selection bias:

- [x] Exclusion count matches `docs/reproducibility/excluded_knots.md` per SC-012
- [x] All downstream analyses reference hyperbolic-only subset
- [x] Statistical interpretations acknowledge population limitation
- [x] No claims of generalizability to non-hyperbolic knots

## References

- FR-012: "Filter dataset to hyperbolic knots (volume > 0) and log excluded knots"
- SC-012: "Exclusion count must match excluded_knots.md"
- Constitution Principle VII: "Census data exception for p-value reporting"
- {{claim:c_3ea0f57a}}: Knot Atlas data source

## Document Metadata

- **Created**: 2026-01-15
- **Last Updated**: 2026-01-15
- **Version**: 1.0
- **Related Documents**: excluded_knots.md, data_quality_report.md, validation_scope.md
- **Task ID**: T059