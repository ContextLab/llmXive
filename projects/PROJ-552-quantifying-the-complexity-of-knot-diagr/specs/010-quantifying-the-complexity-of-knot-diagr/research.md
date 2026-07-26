# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research project investigates the relationship between combinatorial invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) across the complete census of prime knots with crossing number ≤ 13. The study aims to determine whether joint invariants describe geometric complexity better than individual measures and to identify specific knot families that deviate from global trends.

## Dataset Strategy

### Primary Data Source: KnotInfo via `database-knotinfo`

The project utilizes the `database-knotinfo` Python library as the canonical, verified source for knot data. This library provides programmatic access to the KnotInfo database, ensuring reproducibility and avoiding the need for manual scraping or unverified URLs.

- **Source**: `database-knotinfo` library (verified access recipe provided in spec).
- **Access Method**: `from database_knotinfo import link_list; records = list(link_list())`.
- **Coverage**: The library contains records for all prime knots up to a specified crossing number (source: OEIS A002863).
- **Fields**: Includes crossing number, braid index, hyperbolic volume, alternating classification, and numerous other invariants.
- **Verification**: The library has been tested to return real, non-placeholder data with the expected schema.

### Data Quality & Completeness

- **Target**: All prime knots with crossing number ≤ 13.
- **Validation Benchmark**: Phase 1 focuses on completeness for crossing number ≤ 10; crossing number 11-13 data is available for exploratory analysis.
- **Null Threshold**: Required fields (crossing number, braid index, hyperbolic volume) must have null percentage ≤ 5% in the validated subset.
- **Duplicate Handling**: Duplicate knot IDs are flagged and removed; target duplicate count = 0.

### Data Processing Pipeline

1.  **Download**: Fetch all records via `database-knotinfo`.
2.  **Parse**: Convert raw records to `KnotRecord` objects; validate against `knot_record.schema.yaml`.
3.  **Filter**: Retain only hyperbolic knots (volume > 0) for volume prediction analysis.
4.  **Flag**: Mark records with missing invariants or ambiguous classifications.
5.  **Clean**: Apply tie-breaking rules for diagram representations.

## Statistical Methodology

### Census Data Interpretation

The dataset represents a complete census of the target population (all prime knots ≤ 13 crossings). Therefore:
- **Descriptive, Not Inferential**: All statistical analysis is descriptive. Effect sizes (Cohen's d, r) are the primary metrics.
- **No P-Values**: P-values and confidence intervals are not reported for census data, as there is no larger population to generalize to (Constitution Principle VII exception).
- **Model Selection**: Based on goodness-of-fit metrics (R², AIC/BIC, MAE), not statistical power.

### Correlation Analysis

- **Primary Method**: Spearman correlation (appropriate for discrete integer-valued invariants).
- **Supplementary Method**: Pearson correlation (reported for completeness, with acknowledgment of discrete data limitations).
- **Effect Sizes**: Report r (for correlations) and r² (for variance explained).

### Regression Modeling

- **Model Types**: Linear, polynomial (degree 2), and logarithmic regression.
- **Predictors**: Crossing number, braid index (jointly).
- **Outcome**: Hyperbolic volume.
- **Multicollinearity**: Variance Inflation Factor (VIF) computed to assess multicollinearity between predictors (expected to be high due to mathematical constraint braid index ≤ crossing number).
- **Interpretation**: Coefficients are descriptive associations within the census, not independent explanatory power.

### Residual Analysis

- **Objective**: Identify specific hyperbolic knot families (e.g., pretzel, hyperbolic non-alternating) that deviate significantly (≥ 2 standard deviations) from the fitted trend.
- **Scope**: Targets only hyperbolic knots (torus/satellite excluded).
- **Documentation**: Deviations documented in `docs/reproducibility/residual_analysis.md`.

## Edge Case Handling

### API Unavailability & Rate Limiting

- **Retry Logic**: Exponential backoff (initial 1s, multiplier 2, max 32s) implemented in `code/download/knot_info_loader.py`.
- **Partial Results**: Cached to disk after consecutive failures.

### Missing Invariants

- **Flagging**: Records with missing invariants are flagged with `missing_invariant_flags` (not silently excluded).
- **Phase 1 Scope**: Core invariants (crossing number, braid index) are tabulated; missing flags apply only to computed invariants (Phase 2+).

### Ambiguous Classifications

- **Alternating/Non-Alternating**: Records with ambiguous classification are either excluded from stratified analysis (with count logged) or marked as "unclassifiable".

### Diagram Representation Ties

- **Tie-Breaking Rules**:
    1.  Prefer braid word representation over Dowker-Thistlethwaite (DT) code.
    2.  If multiple DT codes exist, prefer lexicographically first.
- **Validation**: Consistency checked via `docs/reproducibility/tie_breaking_validator.py`.

### Zero/Undefined Hyperbolic Volume

- **Filtering**: Knots with volume = 0 or undefined (torus/satellite) are excluded from volume prediction analysis.
- **Documentation**: Excluded records logged in `docs/reproducibility/excluded_knots.md`.

## Compute Feasibility

- **CPU-First**: All analysis (data download, parsing, statistical regression) is CPU-tractable.
- **Resource Limits**: Fits within GitHub Actions free-tier (standard CPU allocation, standard RAM, 14GB disk).
- **No GPU Required**: No transformer models or heavy numerical linear algebra requiring CUDA.
- **Streaming**: Data is loaded in memory via `database-knotinfo`; no need for streaming large files.

## Decision Rationale

- **Source Selection**: `database-knotinfo` chosen for verified, programmatic access to KnotInfo data, ensuring reproducibility and avoiding fabrication risks.
- **Statistical Approach**: Census data exception applied to Constitution Principle VII; effect sizes prioritized over p-values.
- **Model Complexity**: Linear, polynomial, and logarithmic models selected based on prior knot theory literature showing non-linear relationships.
- **Edge Case Handling**: Explicit flagging and logging ensure robustness and transparency in data quality.

## Verified Datasets

- **KnotInfo**: NO verified source found (do NOT cite a URL for it). (Note: `database-knotinfo` library is the verified access method, not a raw URL).
- **OEIS A002863**: https://oeis.org/A002863 (source for total prime knot count).

## References

- Birman, J. S., & Menasco, W. W. (1988). *Mathematische Annalen*.
- Ohyama, Y. (1993). *J. Knot Theory Ramifications*.
- Hoste, J., Thistlethwaite, M. B., & Weeks, J. R. (1998). *The first [deferred] knots*.
- OEIS A002863: Number of prime knots with n crossings.
