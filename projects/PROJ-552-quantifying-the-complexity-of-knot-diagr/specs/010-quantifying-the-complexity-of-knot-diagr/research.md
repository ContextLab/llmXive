# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12

## Research Question

How do combinatorial invariants (crossing number, braid index) jointly describe the geometric complexity of hyperbolic prime knots as measured by hyperbolic volume?

## Background and Motivation

Knot theory provides a rich framework for understanding entanglement through mathematical invariants. The crossing number (minimum number of crossings in any diagram) and braid index (minimum number of strands in any braid representation) are classical combinatorial invariants that capture different facets of knot geometry. Hyperbolic volume, a geometric invariant, measures the volume of the knot complement in hyperbolic 3-space.

This research investigates whether the joint relationship between crossing number and braid index can predict hyperbolic volume across the census of prime knots with crossing number ≤ 13. The analysis acknowledges that braid index ≤ crossing number is a known mathematical constraint (Birman-Menasco inequality), meaning regression coefficients describe variance partitioning within the finite census rather than independent explanatory power.

## Dataset Strategy

| Dataset | Purpose | Source | Access Method | Notes |
|---------|---------|--------|---------------|-------|
| Prime knots ≤ 13 crossings | Core analysis data | Knot Atlas | Programmatic download (FR-001) | NO verified source found; cite by name only per verified datasets block |
| OEIS A002863 | Prime knot count reference | OEIS | https://oeis.org/A002863 | Verified: 9988 prime knots ≤ 13 crossings |
| KnotInfo | Validation reference | KnotInfo | https://knotinfo.org/ | Used for hyperbolic volume cross-check (FR-013) |

**Important**: Per the verified datasets block, NO URL is cited for Knot Atlas data. The dataset is referenced by name only. The implementation will attempt programmatic download from https://katlas.org, with retry logic (FR-008) and partial caching on failure.

**Dataset Completeness**: The analysis targets all 9988 prime knots with crossing number ≤ 13 (source: OEIS A002863, https://oeis.org/A002863). Phase 1 validation benchmarks completeness for crossing number ≤ 10 crossings; crossing number 11-13 data is downloaded for exploratory analysis but marked as unvalidated in reports (Assumptions section of spec.md).

## Computational Approach

### Phase Ordering (Mandatory per Rules)

1. **Data Download** (FR-001, FR-008): Download Knot Atlas data with exponential backoff retry logic. Cache partial results on consecutive failures.
2. **Data Cleaning** (FR-002, FR-009): Parse, validate, and flag records. Generate checksums (FR-007).
3. **Exploratory Analysis** (FR-004): Generate scatter plots of crossing number vs. braid index, stratified by alternating/non-alternating classification.
4. **Model Fitting** (FR-005): Fit linear, polynomial, and logarithmic regression models. Compute VIF for multicollinearity assessment.
5. **Residual Analysis** (SC-011): Identify hyperbolic knot families deviating ≥ 2 standard deviations from fitted trend.
6. **Statistical Analysis** (FR-006): Compute Spearman and Pearson correlations, effect sizes (Cohen's d, r).
7. **Reproducibility Documentation** (FR-007, SC-003): Generate checksums, derivation notes, logs, and validation reports.

### Measurement Precision (Per marie-curie feedback)

**Core Invariants**:
- Crossing number: Tabulated from Knot Atlas (well-defined, no computation uncertainty)
- Braid index: Tabulated from Knot Atlas (algorithmic determination; precision established through reference validation)

**Precision Validation**: Phase 1 establishes precision thresholds for core invariants (crossing number, braid index) through reference validation against KnotInfo where available (FR-013). Additional invariants (arc index, Seifert circle count, bridge number) are deferred to Phase 2+ per spec.md FR-003.

### Statistical Methodology

**Census Data Exception**: This analysis covers a complete census of hyperbolic prime knots (volume > 0) with crossing number ≤ 13. Per Constitution Principle VII (census-data exception), p-values are not applicable; effect sizes are the primary metrics.

**Correlation Analysis** (FR-006):
- Primary: Spearman correlation (appropriate for discrete integer-valued invariants)
- Supplementary: Pearson correlation (reported for completeness; interpretation acknowledges discrete data limitation)
- Effect sizes: r or r² for correlations; Cohen's d for group comparisons

**Regression Analysis** (FR-005):
- Model types: Linear, polynomial, logarithmic
- Metrics: R², AIC/BIC, MAE (descriptive fit statistics for finite census)
- Multicollinearity: VIF computed and documented (expected to be high due to braid index ≤ crossing number constraint)
- Train/test split: NOT applicable (census data; no hold-out set)
- ANOVA: NOT applicable (census data; descriptive statistics suffice)

**Descriptive Comparison** (FR-006, SC-009):
- Alternating vs. non-alternating: Mean differences, variance ratios, Cohen's d
- No inferential claims; exact population parameters reported

**Residual Analysis Interpretation** (SC-011): Residual analysis identifies knot families deviating ≥ 2 standard deviations from fitted trend. Given the census data context and the known mathematical constraint (braid index ≤ crossing number), residual patterns are interpreted as **descriptive categorization of structural properties** (e.g., alternating vs. non-alternating classification effects) rather than evidence of model inadequacy. This is not model validation in the inferential sense; it is exploratory pattern identification within a finite population where all parameters are known. Residual family identification serves to categorize which knot families exhibit systematic deviation patterns, which may reflect underlying structural differences (such as alternating vs. non-alternating classification effects) rather than unexplained variance in the traditional regression sense.

## Validation Strategy

### Data Quality (SC-013)

| Metric | Threshold | Measurement |
|--------|-----------|-------------|
| Null percentage (required fields) | ≤ 5% | Count nulls / total records |
| Format validation pass rate | ≥ 99% | Valid DT code/braid word format |
| Duplicate records | 0 | Unique knot ID count |

### Hyperbolic Volume Cross-Check (FR-013, SC-014)

- Target: ≥ 90% match against KnotInfo reference values
- Coverage threshold: ≥ 90% of analyzed knots must have KnotInfo reference available
- **Important**: If Knot Atlas and KnotInfo share underlying data sources, this is cross-checking for consistency, NOT independent verification (spec.md Assumptions)

### Algorithm Validation (Phase 2+, FR-003, SC-010)

- Target: ≥ 90% match against KnotInfo for additional invariants
- Coverage threshold: ≥ 90% reference coverage required
- Invariants: Arc index (Birman-Menasco), Seifert circle count (Seifert's algorithm, source: arXiv math/, https://arxiv.org/abs/math/[arXiv ID]), bridge number (Schubert's decomposition, source: -bridge knot, https://en.wikipedia.org/wiki/-bridge_knot)

## Edge Cases and Robustness

| Edge Case | Handling (FR-008, FR-009, FR-010) |
|-----------|-----------------------------------|
| Knot Atlas unavailable | Exponential backoff retry; partial results cached to disk |
| Missing invariant data | Flag with missing_invariant_flags; do not silently exclude |
| Ambiguous alternating classification | Exclude from stratified analysis or mark as "unclassifiable" |
| Diagram representation ties | Apply documented tie-breaking rules (FR-011): prefer braid word over DT code; prefer lexicographically first DT code |
| Zero/undefined hyperbolic volume | Filter out (FR-012); document excluded knots in `docs/reproducibility/excluded_knots.md` |

## Reproducibility Requirements (FR-007, SC-003)

- Random seeds: Pinned in code; documented in `docs/reproducibility/random_seeds.md`
- Checksums: SHA-256 for all data files; recorded under `data/` per Constitution Principle III
- Derivation notes: Formula citations with page/section references; step-by-step transformation logic
- Logs: Timestamped with operation, input/output files, parameters, status, duration_ms
- Validation scripts: Automated tie-breaking validation (SC-007), schema validation (contracts/)

## Limitations and Acknowledgments

1. **Selection Bias** (FR-012): Analysis applies only to hyperbolic prime knots (volume > 0); conclusions do not extend to torus or satellite knots
2. **Mathematical Constraint** (Assumptions): Braid index ≤ crossing number is definitional; regression coefficients describe variance partitioning within census, not independent effects
3. **Invariant Type Distinction**: Combinatorial invariants (crossing number, braid index) and geometric invariants (hyperbolic volume) measure fundamentally different properties; explanatory relationship may be weak by mathematical definition
4. **Source Independence** (FR-013): If Knot Atlas and KnotInfo share underlying data sources, cross-check measures internal consistency, not independent accuracy
5. **Census Data Interpretation** (Constitution VII): All statistics are descriptive for complete enumeration; no inferential claims to larger populations
6. **Residual Analysis Purpose** (SC-011): Residual patterns are descriptive categorization, not model validation evidence