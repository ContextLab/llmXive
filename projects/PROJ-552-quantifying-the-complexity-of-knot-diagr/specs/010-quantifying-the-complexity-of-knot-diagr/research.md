# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research quantifies knot complexity through two classical topological invariants: crossing number (minimum number of crossings in any diagram) and braid index (minimum number of strands in any braid representation). The analysis examines their joint relationship with hyperbolic volume, a geometric invariant measuring the complexity of the knot complement.

## Dataset Strategy

| Dataset | Source | Access Method | Phase 1 Scope | Verified URL | Verification Status |
|---------|--------|---------------|---------------|--------------|---------------------|
| Knot Atlas Prime Knots | Knot Atlas | HTTP download with retry logic | All prime knots within a specified crossing number range; validated completeness for a lower subset | https://katlas.org | pending verification |
| OEIS Prime Knot Enumeration | OEIS A002863 | Reference for validation | The complete set of prime knots at crossing number up to a specified threshold (total census count) | https://oeis.org/A002863 | verified |
| KnotInfo Reference Values | KnotInfo | API validation (Phase 2+) | Hyperbolic volume validation for subset | https://knotinfo.math.indiana.edu/knotinfo/ | pending verification |

**Verification Procedure**: Knot Atlas and KnotInfo URLs will be verified via HTTP HEAD request before implementation begins. Verification status will be updated in this table upon successful confirmation.

**Data Quality Reference**: Required invariant fields (crossing number, braid index, hyperbolic volume) must have null percentage within acceptable limits across all records in the validated dataset subset for hyperbolic prime knots (volume > 0), per SC-013.

**Phase 1 Scope Limitation**: All Phase 1 conclusions must be explicitly qualified as limited to validated crossing number ≤10 data; any analysis using crossing number 11-13 data must be marked as exploratory/unvalidated in final reports.

**Population Scope**: All conclusions apply only to hyperbolic prime knots (volume > 0), not all prime knots. This selection bias is documented in `docs/reproducibility/excluded_knots.md`.

## Computational Task Order

The analysis pipeline follows this strict ordering to ensure reproducibility and prevent circular dependencies:

1. **Data Download** (FR-001, FR-008): Download Knot Atlas data with exponential backoff retry logic
2. **Data Cleaning** (FR-002): Parse, validate, and clean dataset; create checksummed files
3. **Data Filtering** (FR-012): Filter to hyperbolic knots (volume > 0); document exclusions
4. **Exploratory Analysis** (FR-004): Generate scatter plots of crossing number vs. braid index
5. **Regression Modeling** (FR-005): Fit linear, polynomial, and logarithmic models
6. **Statistical Testing** (FR-006): Compute correlation coefficients and effect sizes
7. **Residual Analysis** (FR-005, SC-011): Identify hyperbolic knot families deviating from predictions
8. **Reproducibility Documentation** (FR-007): Generate checksums, derivation notes, logs

**Note**: Additional invariant computation (arc index, Seifert circle count, bridge number) is deferred to Phase 2+ per FR-003.

## Measurement Precision Standards

Consistent with rigorous scientific measurement standards (per reviewer marie-curie-simulated), the analysis establishes precision thresholds for all core invariants before correlation analysis proceeds:

- **Crossing Number**: Tabulated from Knot Atlas; precision is exact (integer-valued)
- **Braid Index**: Tabulated from Knot Atlas; precision is exact (integer-valued)
- **Hyperbolic Volume**: Tabulated from Knot Atlas; validated against KnotInfo reference values per FR-013

**Phase 1 Scope**: Only core invariants (crossing number, braid index) are validated in Phase 1. Additional invariants (arc index, Seifert circle count, bridge number) are deferred to Phase 2+ per original idea methodology boundary.

## Mathematical Constraints Acknowledgment

**Braid Index ≤ Crossing Number**: This is a known mathematical constraint (inequality), not an empirical finding. This creates a definitional relationship that must be acknowledged in all analysis and coefficient interpretation. Joint regression answers a variance partitioning question rather than independent explanatory power.

**Variance Partitioning Clarification**: The variance partitioning question acknowledges the mathematical constraint between predictors; joint regression describes variance attribution within the finite census dataset, not independent explanatory power. All final reports MUST explicitly state that regression analysis measures variance partitioning within the finite census, NOT independent predictive power.

**Multicollinearity Acknowledgment**: Crossing number and braid index are not fully independent predictors. VIF assessment (per FR-005) will quantify multicollinearity concerns as expected consequence of predictor structure.

## Census Data Statistical Interpretation

Since the dataset represents a complete census of all prime knots ≤13 crossings rather than a sample from a larger population, all statistical analysis is descriptive rather than inferential:

- **Effect sizes** (Cohen's d, r) are the primary metrics of interest
- **P-values** are documented for reporting convention only and must not support inferential claims
- **Train/test splits, ANOVA, and cross-validation** are not applicable for complete census data
- **Descriptive statistics** (mean differences, variance ratios) suffice for exact population parameters

## Model Selection Methodology

Model forms (linear, polynomial, logarithmic) are selected based on prior knot theory literature showing non-linear relationships between topological invariants (e.g., Birman & Menasco foundational work; Ohyama prior work). Model selection uses goodness-of-fit metrics (R², AIC/BIC, MAE), not statistical power.

**Descriptive Interpretation**: R², AIC, and BIC are interpreted as descriptive fit statistics for finite census dataset rather than variance explained in any meaningful statistical sense.

## Edge Case Handling

| Edge Case | Handling Strategy | Documentation Location |
|-----------|------------------|----------------------|
| Knot Atlas unavailable | Exponential backoff retry (initial=1s, max=32s, multiplier=2); partial results cached after 3 failures | `code/download/retry_utils.py` |
| Missing invariant data | Flag with `missing_invariant_flags` rather than silent exclusion | `data/processed/knots_cleaned.parquet` |
| Ambiguous alternating classification | Exclude from stratified analysis or mark as "unclassifiable" | `docs/reproducibility/validation_scope.md` |
| Diagram representation ties | Prefer braid word over DT code; prefer lexicographically first DT code | `docs/reproducibility/tie_breaking_rules.md` |
| Zero/undefined hyperbolic volume | Filter out (torus/satellite knots); document exclusions | `docs/reproducibility/excluded_knots.md` |

## Source Independence Documentation (FR-013)

Hyperbolic volume validation against KnotInfo (FR-013, SC-014) requires explicit source independence documentation. Knot Atlas and KnotInfo may share underlying data sources (e.g., Hoste-Thistlethwaite-Weeks enumeration). This validation is a consistency cross-check, NOT independent verification. All final reports MUST explicitly state this limitation. Derivation notes with formula citations and source documentation are required in `docs/reproducibility/hyperbolic_volume_validation.md`.

**KnotInfo Endpoint**: https://knotinfo.math.indiana.edu/knotinfo/

**Note**: The KnotInfo endpoint URL https://knotinfo.math.indiana.edu/knotinfo/ is documented here for reproducibility. The spec.md FR-013 text requires separate update to include this URL per Constitution Principle I (Reproducibility).

## Reproducibility Requirements

All code and data transformations must be documented with:
- SHA-256 checksums for all data files (FR-007)
- Derivation notes with formula citations and step-by-step logic (FR-007)
- Timestamped logs with operation/input/output/parameters/status/duration_ms (FR-007)
- Random seed values documented in `docs/reproducibility/random_seeds.md` (FR-007)

**Validation Scope Document**: The `validation_scope.md` document must contain: (1) crossing number ≤10 vs ≤13 distinction with data availability counts, (2) justification for Phase 1 scope limitation, (3) data availability vs validated completeness table showing counts per crossing number.