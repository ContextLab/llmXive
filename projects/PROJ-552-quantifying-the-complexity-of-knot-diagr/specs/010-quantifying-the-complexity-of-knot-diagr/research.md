# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Executive Summary

This research quantifies the relationship between topological invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) for prime knots. The analysis focuses on core methodology: crossing number and braid index as separate predictors, with hyperbolic volume as the target variable for regression analysis.

## Dataset Strategy

| Dataset | Source | Purpose | Verification Status |
|---------|--------|---------|---------------------|
| Prime Knot Census (≤13 crossings) | Knot Atlas | Primary data source for crossing number, braid index, hyperbolic volume, alternating classification | NO verified source found (per verified datasets block); will attempt download with retry logic per FR-008 |
| OEIS Prime Knot Counts | OEIS A002863, https://oeis.org/A002863 | Validation benchmark for dataset completeness | VERIFIED (9988 prime knots at crossing number ≤13) |
| KnotInfo Reference Values | KnotInfo | Validation reference for hyperbolic volume (FR-013) | NO verified source found (per verified datasets block); validation documented with skip rationale if coverage insufficient |

**Data Download Strategy**:
1. Attempt download from Knot Atlas with exponential backoff (initial=1s, max=32s, multiplier=2)
2. After 3 consecutive failures, cache partial results to disk
3. Validate completeness against OEIS counts for crossing numbers ≤10 (Phase 1 scope)
4. Document any missing invariants with missing_invariant_flags (per FR-009)

**Phase 1 Scope Limitation**: While data availability extends to crossing number ≤13, validated completeness focuses on crossing number ≤10. All Phase 1 conclusions must be explicitly qualified as limited to validated crossing number ≤10 data.

## Measurement Precision Standards

Following marie-curie's feedback on measurement precision: "We did not claim a new element until the atomic weight could be determined with precision." This work establishes precision thresholds for core invariants before correlation analysis.

| Invariant | Precision Standard | Validation Method |
|-----------|-------------------|-------------------|
| Crossing Number | Tabulated (exact) | Cross-check against Knot Atlas enumeration |
| Braid Index | Tabulated (exact) | Cross-check against Knot Atlas enumeration |
| Hyperbolic Volume | Computed (numerical) | Validate against KnotInfo where reference coverage ≥90% |

**Core Invariants**: Crossing number and braid index are tabulated from Knot Atlas (per SC-008). Additional invariants (arc index, Seifert circle count, bridge number) are deferred to Phase 2+ per original idea methodology boundary.

## Statistical Methodology

### Correlation Analysis
- **Primary**: Spearman correlation (appropriate for discrete integer-valued invariants)
- **Supplementary**: Pearson correlation (reported for completeness; interpretation limited by discrete data)
- **Effect Sizes**: Cohen's d for group comparisons; r or r² for correlations

### Regression Models
Three model types will be compared:
1. Linear regression
2. Polynomial regression (non-linear)
3. Logarithmic regression

**Goodness-of-Fit Metrics**: R², AIC, BIC, MAE documented for each model type.

**Census Data Acknowledgment**: Since the dataset represents a complete census of prime knots ≤13 crossings rather than a sample, statistical analysis is descriptive rather than inferential. Effect sizes are primary metrics; p-values documented for convention only and marked as 'not applicable for census data' when making inferential claims.

### Multicollinearity Assessment
Variance Inflation Factor (VIF) computed for all joint regression models. High VIF expected due to mathematical constraint (braid index ≤ crossing number). Document VIF values as expected consequence of predictor structure.

## Edge Case Handling

| Edge Case | Handling Strategy | Documentation |
|-----------|-------------------|---------------|
| Knot Atlas unavailable | Exponential backoff with partial result caching | docs/reproducibility/logs/ |
| Missing invariant data | Flag with missing_invariant_flags (not silent exclusion) | docs/reproducibility/data_quality_report.md |
| Ambiguous alternating classification | Exclude from stratified analysis or mark "unclassifiable" | docs/reproducibility/validation_status.md |
| Diagram representation ties | Documented tie-breaking rules applied consistently | docs/reproducibility/tie_breaking_rules.md |
| Zero/undefined hyperbolic volume | Filter out (torus/satellite knots); document exclusions | docs/reproducibility/excluded_knots.md |

## Reproducibility Requirements

All code and data transformations documented per FR-007:
- SHA-256 checksums for all data files (recorded under data/)
- Derivation notes with formula citations and step-by-step logic
- Timestamped logs with operation/input/output/parameters/status/duration_ms
- Random seed values documented in docs/reproducibility/random_seeds.md

## Selection Bias Acknowledgment

Filtering to hyperbolic prime knots (volume > 0) means conclusions apply only to hyperbolic prime knots, not all prime knots. This selection bias must be acknowledged in all final reports.

## Source Independence Assessment

Knot Atlas and KnotInfo may share underlying data sources (e.g., Hoste-Thistlethwaite-Weeks enumeration). If both databases derive from common sources, validation is cross-checking for consistency, NOT independent verification. This limitation documented in docs/reproducibility/hyperbolic_volume_validation.md.
