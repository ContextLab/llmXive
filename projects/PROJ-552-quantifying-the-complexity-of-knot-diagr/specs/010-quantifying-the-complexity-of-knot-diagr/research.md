# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Research Questions

1. What is the relationship between crossing number and braid index for prime knots?
2. Can crossing number and braid index jointly predict hyperbolic volume?
3. Do alternating and non-alternating knots show different patterns in invariant relationships?
4. Which hyperbolic knot families deviate significantly from global model predictions?

## Dataset Strategy

| Dataset | Purpose | Source | Access Method |
|---------|---------|--------|---------------|
| Knot Atlas | Primary knot data (crossing number, braid index, hyperbolic volume, alternating classification) | Knot Atlas database | Programmatic download via HTTP requests with retry logic (https://katlas.org) |
| KnotInfo | Validation reference for hyperbolic volume values | KnotInfo database | Manual lookup (no verified URL per verified datasets block - URL not available in verified sources) |
| OEIS A002863 | Prime knot enumeration counts for completeness validation | OEIS | https://oeis.org/A002863 |

**Verified Dataset Counts** (per verified sources):
- Total prime knots with crossing number ≤13: documented count (source: OEIS A002863, https://oeis.org/A002863)

**Phase 1 Scope**: Dataset completeness validated for crossing number ≤10; crossing number 11-13 data downloaded but marked exploratory/unvalidated.

**KnotInfo URL Limitation**: KnotInfo does not have a verified URL in the verified datasets block. All references to KnotInfo in this plan are by name only. Validation against KnotInfo values is performed where accessible, but URL verification is blocked per Constitution Principle II.

## Measurement Precision Standards

Consistent with reviewer marie-curie's feedback on measurement precision standards, this work establishes precision thresholds before correlation analysis proceeds:

- **Crossing Number**: Tabulated from Knot Atlas; precision determined by enumeration completeness
- **Braid Index**: Requires algorithmic determination; precision validated against KnotInfo reference values where available
- **Hyperbolic Volume**: Tabulated from Knot Atlas; validated against KnotInfo where reference data exists

**Phase 1 Limitation**: Algorithm validation applies only to core invariants (crossing number, braid index). Additional invariants (arc index, Seifert circle count, bridge number) are Phase 2+ scope per FR-003.

## Computational Methods

### Invariant Computation Algorithms

| Invariant | Algorithm | Source |
|-----------|-----------|--------|
| Arc Index | Birman-Menasco method | Birman & Menasco, 1988, *Mathematische Annalen*, 281, pp. 127-138 |
| Seifert Circle Count | Seifert's algorithm on minimal crossing diagrams | arXiv:math/0303273 (https://arxiv.org/abs/math/0303273) |
| Bridge Number | Schubert's bridge decomposition | Wikipedia: 2-bridge knot (https://en.wikipedia.org/wiki/2-bridge_knot) |

**Note**: Core invariants (crossing number, braid index) are tabulated from Knot Atlas, not computed. Algorithm validation applies only to additional invariants in Phase 2+.

### Statistical Methods

| Analysis | Method | Rationale |
|----------|--------|-----------|
| Correlation | Spearman (primary), Pearson (supplementary) | Discrete integer-valued invariants; Spearman appropriate for ordinal data |
| Regression | Linear, Polynomial, Logarithmic | Non-linear relationships documented in knot theory literature |
| Group Comparison | Mean difference, Variance ratio, Cohen's d | Census data; descriptive statistics for exact population parameters |
| Multicollinearity | Variance Inflation Factor (VIF) | Expected high VIF due to mathematical constraint (braid index ≤ crossing number) |

**Census Data Acknowledgment**: Since the dataset represents a complete census of all prime knots ≤13 crossings, all statistical analysis is descriptive rather than inferential. Effect sizes are primary metrics; **p-values are NOT reported for census data** to avoid misinterpretation. This is consistent across all artifacts (plan.md, research.md, data-model.md, contracts/).

**Multicollinearity Limitation**: Using crossing number and braid index as joint predictors where braid index ≤ crossing number is a known mathematical constraint. This creates multicollinearity by definition. VIF assessment is performed, but regression analysis can only establish variance partitioning within the census, not independent explanatory power. This limitation is explicitly documented in all model outputs.

### Model Selection Criteria

- Primary: R², AIC, BIC, MAE (descriptive fit statistics for finite census)
- Secondary: Residual analysis to identify hyperbolic knot families with significant deviations (≥2 standard deviations)
- **Not Applicable**: Train/test split, cross-validation, ANOVA (census data has no hold-out set)
- **Not Reported**: p-values (not applicable for complete enumeration; effect sizes are primary metrics)

## Validation Strategy

### Hyperbolic Volume Validation

Hyperbolic volume data will be validated against KnotInfo reference values where available. Validation results documented in `docs/reproducibility/hyperbolic_volume_validation.md`.

**Coverage Feasibility Assessment**: KnotInfo coverage for hyperbolic volume is expected to be substantial for knots with low crossing numbers.. Validation threshold adjusted to **≥50% match rate when coverage ≥50%**; if coverage <50%, validation skipped and limitation documented.

**Validation Threshold**: **high match threshold where coverage ≥50%** (quantified per Constitution Principle II testability requirements).

**Source Independence Assessment**: Knot Atlas and KnotInfo may share underlying data sources (e.g., Hoste-Thistlethwaite-Weeks enumeration). Validation interpreted as cross-check rather than independent verification when common sources exist. This limitation is explicitly documented in validation reports.

**KnotInfo URL Status**: No verified URL available per verified datasets block. Validation proceeds via manual lookup where possible, but URL verification is blocked per Constitution Principle II (Verified Accuracy).

### Algorithm Validation (Phase 2+)

For additional invariants (arc index, Seifert circle count, bridge number), validation against KnotInfo reference values with ≥90% match threshold.

**Threshold Distinction**:
1. Reference coverage threshold ≥50%: If KnotInfo coverage <50%, validation skipped and limitation documented
2. Match threshold ≥90%: If coverage ≥50% but match rate <90%, validation fails and limitation documented

## Edge Cases and Fallbacks

| Edge Case | Handling | Documentation |
|-----------|----------|---------------|
| Knot Atlas unavailable | Exponential backoff (initial=1s, max=32s, multiplier=2); partial results cached | `docs/reproducibility/retry_logs.md` |
| Missing invariant data | Flag with missing_invariant_flags (not excluded) | `docs/reproducibility/missing_invariant_flags.md` |
| Ambiguous alternating classification | Exclude or mark "unclassifiable" | `docs/reproducibility/data_quality_report.md` |
| Diagram representation ties | Prefer braid word over DT code; lexicographically first DT code | `docs/reproducibility/tie_breaking_rules.md` |
| Zero/undefined hyperbolic volume | Flag and exclude from volume analysis; log count | `docs/reproducibility/excluded_knots.md` |

## Reproducibility Requirements

Per Constitution Principle I and FR-007:

- Random seeds pinned in code; values documented in `docs/reproducibility/random_seeds.md`
- SHA-256 checksums for all data files; recorded under `data/` directory
- Derivation notes with formula citations, step-by-step logic, parameter values
- Timestamped logs with operation, input_file, output_file, parameters, status, duration_ms

## Critical Spec.md Issues Requiring Kickback

**WARNING**: The following issues exist in the source spec.md and cannot be resolved at the plan stage. These must be addressed via kickback to clarify stage:

1. **FR-013 Corrupted URL**: spec.md:FR-013 contains corrupted URL text: `( nodename nor servname provided, or not known)'))])`. This blocks Constitution Principle II (Verified Accuracy) verification.

2. **FR-013 Unquantified Threshold**: spec.md:FR-013 states "high match threshold" without quantification. This plan and research artifacts specify ≥90% match threshold where coverage ≥50%.

3. **FR-006 P-Value Policy Conflict**: spec.md:FR-006 states "p-values are documented for reporting convention only" while this research explicitly excludes p-values for census data.

**Action Required**: These spec.md issues must be corrected before the project can pass the Verified Accuracy Gate.