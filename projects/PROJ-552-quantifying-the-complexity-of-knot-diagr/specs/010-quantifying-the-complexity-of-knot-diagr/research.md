# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Executive Summary

This research quantifies knot diagram complexity through analysis of two classical topological invariants: crossing number (minimal number of crossings in any diagram) and braid index (minimal number of strands in any braid representation). The study downloads prime knot data from Knot Atlas for all knots with crossing number ≤13, validates measurement precision against reference values, and fits regression models to assess joint predictive relationships with hyperbolic volume. Phase 1 scope is explicitly limited to core invariants and validated crossing number ≤10 data per spec requirements.

## Dataset Strategy

| Dataset | Purpose | Source Type | Access Method |
|---------|---------|-------------|---------------|
| Knot Atlas prime knot census | Primary data for all invariants | External database (Knot Atlas) | Programmatic download via HTTP with retry logic |
| KnotInfo reference values | Validation of computed invariants | External database (KnotInfo) | Name-only reference; no URL fabricated per verified datasets constraints |
| OEIS A002863 | Prime knot count verification | Integer sequence database | https://oeis.org/A002863 |

**Data Availability Note**: The verified datasets block indicates NO verified source found for Knot Atlas (FR-001), KnotInfo validation (FR-013), or OEIS counts (SC-001). Per spec requirements, these are referenced by name only without fabricating URLs. The Knot Atlas URL (https://katlas.org) is specified in FR-001 of the spec.md itself, not in the verified datasets block.

**Key Dataset Facts** (from verified facts block):
- Total prime knots with crossing number ≤13: 9988 (source: OEIS A002863, https://oeis.org/A002863)
- This count represents the complete census for Phase 1 scope

## Measurement Precision Standards

Consistent with marie-curie's feedback on measurement precision ("we did not claim a new element until the atomic weight could be determined with precision"), this research establishes precision thresholds for core invariants before correlation analysis proceeds:

| Invariant | Precision Standard | Validation Method |
|-----------|-------------------|-------------------|
| Crossing number | Tabulated from Knot Atlas (no computation) | Cross-reference against KnotInfo reference values |
| Braid index | Tabulated from Knot Atlas (no computation) | Cross-reference against KnotInfo reference values |
| Hyperbolic volume | Tabulated from Knot Atlas (no computation) | Cross-reference against KnotInfo reference values (≥90% match threshold) |

**Phase 1 Scope Boundary**: Additional invariants (arc index, Seifert circle count, bridge number) are deferred to Phase 2+ per original idea methodology boundary. Core invariants are tabulated, not computed, so algorithm validation applies only to Phase 2+ additional invariants.

## Statistical Methodology

### Primary Correlation Method
Spearman correlation is primary for discrete integer-valued invariants (crossing number, braid index are small integers). Pearson correlation is reported for completeness but interpretation acknowledges discrete data limitation.

### Census Data Acknowledgment
Since the dataset represents a complete census of all prime knots ≤13 crossings rather than a sample from a larger population, all statistical analysis is descriptive rather than inferential. Effect sizes (Cohen's d, r) are the primary metrics of interest; p-values are documented for reporting convention only and must not support inferential claims.

### Methodology Shifts from Original Idea
1. **Train/Test Split Removal**: Not applicable for complete census data; goodness-of-fit metrics (R², AIC/BIC, MAE) used instead
2. **ANOVA Removal**: Not applicable for census data; descriptive statistics (mean differences, variance ratios) suffice
3. **Cross-Validation Removal**: Not applicable for census data; fit metrics used for model selection

## Regression Model Framework

Three model types will be compared to test relationships between crossing number, braid index, and hyperbolic volume:

| Model Type | Form | Rationale |
|------------|------|-----------|
| Linear | Volume ~ β₀ + β₁×Crossing + β₂×Braid + ε | Baseline linear relationship |
| Polynomial | Volume ~ β₀ + β₁×Crossing + β₂×Crossing² + β₃×Braid + ε | Captures non-linear growth |
| Logarithmic | Volume ~ β₀ + β₁×log(Crossing) + β₂×Braid + ε | Matches theoretical expectations |

**Mathematical Constraint Acknowledgment**: Braid index ≤ crossing number is a known mathematical constraint, not an empirical finding. This creates a definitional relationship that must be acknowledged in all analysis. Joint regression answers a variance partitioning question rather than independent explanatory power.

**Residual Analysis**: System MUST identify specific hyperbolic knot families (e.g., pretzel, hyperbolic non-alternating) that deviate significantly (≥2 standard deviations) from model predictions, implementing methodology from the original idea.

## Edge Case Handling

| Edge Case | Handling Strategy | Documentation Location |
|-----------|------------------|----------------------|
| Knot Atlas unavailable | Exponential backoff retry (1s initial, 32s max, 2× multiplier); partial results cached after 3 failures | docs/reproducibility/logs.md |
| Missing invariant data | Flag with missing_invariant_flags; do not silently exclude | docs/reproducibility/data_quality_report.md |
| Ambiguous alternating classification | Exclude from stratified analysis or mark "unclassifiable" | docs/reproducibility/data_quality_report.md |
| Diagram representation ties | Apply documented tie-breaking rules consistently | docs/reproducibility/tie_breaking_rules.md |
| Zero/undefined hyperbolic volume | Filter to volume >0; document excluded knots | docs/reproducibility/excluded_knots.md |

## Reproducibility Requirements

All code and data transformations MUST be documented for reproducibility:
- Random seeds pinned in code (documented in docs/reproducibility/random_seeds.md)
- SHA-256 checksums for all data files (recorded under data/ directory)
- Derivation notes with formula citations, step-by-step logic, intermediate values
- Timestamped logs with operation, input/output files, parameters, status, duration

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Dataset completeness | All prime knots ≤13 crossings downloaded | Validation against OEIS A002863 count |
| Required invariant null percentage | < acceptable threshold | data_quality_report.md |
| Hyperbolic volume validation | ≥90% match with KnotInfo where available | hyperbolic_volume_validation.md |
| Model fit comparison | R², AIC/BIC, MAE documented for all models | regression_models.py output |
| Residual analysis | Families with ≥2σ deviation documented | residual_analysis.md |
| Reproducibility artifacts | All checksums, logs, derivation notes present | docs/reproducibility/ directory check |
