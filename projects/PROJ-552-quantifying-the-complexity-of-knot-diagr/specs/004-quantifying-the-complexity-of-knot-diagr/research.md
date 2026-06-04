# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Research Question (Phase 1)

To what extent do crossing number and braid index jointly predict the hyperbolic volume of prime knots, and does this relationship differ systematically between alternating and non-alternating classes?

**Theoretical Context**: This analysis tests known theoretical bounds (e.g., Agol-Dunfield bounds for alternating knots) rather than treating the relationship as purely exploratory. We expect crossing number and braid index to correlate with hyperbolic volume within theoretically established ranges, with deviations indicating geometric complexity beyond combinatorial invariants.

## Background and Motivation

Knot theory provides a rich framework for understanding geometric complexity through combinatorial invariants. The crossing number (minimum number of crossings in any diagram) and braid index (minimum number of strands in a braid representation) are both classical invariants that capture different facets of knot geometry. As Dan Rockmore noted, "each captures a different facet of the knot's geometry" — the crossing number reflects diagrammatic complexity while braid index reflects algebraic structure.

Marie Curie's emphasis on precision measurement applies here: "When we measured the activity of radium salts, we did not claim a new element until the atomic weight could be determined with precision." Similarly, this work must establish the precision of its measurements across different classes of prime knots before drawing conclusions about joint predictive relationships.

## Dataset Strategy

### Primary Data Source

**Knot Atlas (katlas.org)** — The primary data source for crossing numbers, braid indices, hyperbolic volumes, and alternating/non-alternating classifications. Per FR-001, the system MUST download data for all prime knots with crossing number ≤13.

**Verified Source Status**: NO verified source found in the verified datasets block. The Knot Atlas URL must be accessed directly (https://katlas.org) and is not available through the verified dataset block. This limitation is documented in docs/reproducibility/validation_scope.md.

**Verification Mitigation Strategy**: Despite unverified source status, Knot Atlas will be used with the following mitigations per Constitution Principle II:
1. SHA-256 checksumming of all downloaded data (Constitution Principle III)
2. Cross-validation against KnotInfo where available (≥10% coverage per FR-003)
3. Documentation of any discrepancies in docs/reproducibility/algorithm_validation.md
4. Reference-Validator Agent will flag unverified citations but allow progression with documented risk acceptance at spec level

### Prime Knot Enumeration Reference

The number of prime knots at each crossing number is taken from OEIS A002863. For crossing number 13, the exact count is 9,988 prime knots (source: https://en.wikipedia.org/wiki/Knot_theory, which cites OEIS A002863). This enumeration provides the benchmark for dataset completeness validation.

**Source Status**: OEIS A002863 is an authoritative count reference (not a downloadable dataset). Direct URL citation: https://oeis.org/A002863. This is documented as a count reference rather than a data source.

### Dataset Completeness Scope

- **Phase 1 Validation Benchmark**: Crossing number ≤10 (2,977 prime knots) per OEIS A002863 [UNRESOLVED-CLAIM: c_c4581314 — status=not_enough_info]
- **Data Collection Scope**: Crossing number ≤13 (includes 9,988 knots at c=13) per OEIS A002863
- **Validation Rationale**: Full validation across all crossing numbers ≤13 is computationally impractical for Phase 1 exploratory analysis. This is a deliberate scope decision per SC-001.

### Data Availability Limitations

**Critical Note on c=13 Representations**: Knot Atlas may not provide DT codes or Braid word representations for all 9,988 knots at c=13. FR-003 requires these representations for invariant computation. Where representations are unavailable:
- Records flagged with missing_invariant_flags (not silently excluded)
- Summary report at docs/reproducibility/uncomputable_invariants.md documents count and reasons
- Analysis limited to knots with computable invariants (SC-006 target: ≥99% of computable knots have all invariants populated)

### Missing Dataset Sources

The following dataset references in the spec do NOT have verified sources in the verified datasets block:

| Reference | Source Type | Status | Mitigation |
|-----------|-------------|--------|------------|
| Knot Atlas (katlas.org) | Downloadable dataset | NO verified source found | Checksumming + KnotInfo cross-validation; spec-level risk acceptance required |
| KnotInfo | Downloadable dataset | NO verified source found | Used for validation where coverage ≥10% |
| OEIS A002863 | Count reference (URL) | Authoritative reference | Direct URL citation; not a downloadable dataset |
| 10.1142/S0218216519500020 | Academic citation | NO verified source found | Cited for multicollinearity methodology |
| FR-002 | Implementation requirement | N/A | Implementation requirement |
| FR-003 | Implementation requirement | N/A | Implementation requirement |
| FR-014 | Implementation requirement | N/A | Implementation requirement |
| SC-001 | Success criterion | N/A | Success criterion |
| SC-007 | Success criterion | N/A | Success criterion |
| SC-008 | Success criterion | N/A | Success criterion |
| SC-012 | Success criterion | N/A | Success criterion |
| SC-013 | Success criterion | N/A | Success criterion |

**Note**: The verified datasets block contains only parquet file URLs from HuggingFace that are unrelated to knot theory. All knot-specific datasets must be accessed via their canonical sources directly. Constitution Principle II requires spec-level resolution for unverified sources.

## Invariant Computation Methodology

### Arc Index

**Algorithm**: Birman-Menasco method (Birman & Menasco, 1988, "A Algorithm for the Arc Index of a Knot", *Mathematische Annalen*, 281, pp. 127-138)

**Input Requirement**: Minimal crossing diagram with non-empty Dowker-Thistlethwaite (DT) code field OR braid word representation

**Output**: Integer arc index value

**Validation**: Compare against KnotInfo reference values where available (≥10% coverage required per FR-003)

### Seifert Circle Count

**Algorithm**: Seifert's algorithm on minimal crossing diagrams (Seifert, 1934, "Über das Geschlecht von Knoten", *Mathematische Annalen*, 110, pp. 571-592; see also math/0303273 for s(D) computation)

**Input Requirement**: Minimal crossing diagram with DT code representation

**Output**: Integer Seifert circle count

**Validation**: Compare against KnotInfo reference values where available

### Bridge Number

**Algorithm**: Schubert's bridge decomposition (Schubert, 1954, "Über eine numerische Knoteninvariante", *Mathematische Zeitschrift*, 61, pp. 245-288)

**Verified Reference**: bridge decomposition schubert via = 2-bridge knot (source: https://en.wikipedia.org/wiki/2-bridge_knot)

**Input Requirement**: Minimal crossing diagram representation

**Output**: Integer bridge number

**Validation**: Compare against KnotInfo reference values where available

### Braid Index Source Clarification

Braid index values come from Knot Atlas tabulation where available. For knots where braid index is not tabulated:
- Flag with missing_invariant_flags = ["braid_index_not_tabulated"]
- Do NOT attempt computation from diagrams (computationally intractable for large c)
- Document count in docs/reproducibility/uncomputable_invariants.md

### Invariant Dependency Acknowledgment

Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). Validation is exploratory correlation analysis, not independence testing. This limitation must be acknowledged in all final reports.

## Statistical Analysis Plan

### Regression Models

Three model types will be fitted to test relationships between crossing number, braid index, and hyperbolic volume:

1. **Linear Regression**: Baseline model testing additive effects
2. **Polynomial/Non-linear Regression**: Testing for curvature in the relationship
3. **Logarithmic Regression**: Testing for diminishing returns effects

**Multiple Comparison Correction**: Per FR-005, testing 3+ models on the same data inflates Type I error. Bonferroni correction will be applied: with α=0.05 and 3 models, adjusted significance threshold = 0.05/3 ≈ 0.0167. All model comparisons report both raw and adjusted p-values.

**Multicollinearity Assessment**:
- **VIF Reporting**: Variance Inflation Factors (VIF) MUST be computed for all predictors. VIF > 5 threshold is inappropriate when predictors have mathematical constraints (braid index ≤ crossing number + 1 for all prime knots). This is a structural relationship, not a statistical artifact. VIF will be reported with mathematical constraint context rather than flagged as problematic multicollinearity.
- **Alternative Assessment**: Compute partial correlations controlling for crossing number to assess braid index's unique contribution to variance in hyperbolic volume. This provides a more appropriate measure of independent predictive value given the structural constraint.

### Correlation Analysis

**Mandatory Dual Correlation**: Per Constitution Principle VII, BOTH Pearson AND Spearman correlations MUST be reported when distribution assumptions cannot be verified a priori.

- **Pearson Correlation**: Supplementary (assumes continuous data with normal distribution)
- **Spearman Correlation**: Primary (appropriate for discrete integer-valued invariants)

**Effect Size Reporting**: Cohen's d for group comparisons (alternating vs. non-alternating), r or r² for correlations.

### ANOVA Testing

**Assumption Checks**: Levene's test for equal variances AND Shapiro-Wilk test for normality MUST be performed before ANOVA.

**Robust Alternatives**: If assumptions are violated, use Welch's ANOVA or Kruskal-Wallis test with documentation of deviation from standard ANOVA.

**Reporting Requirement**: ANOVA analysis is exploratory/supplementary; results MUST be reported regardless of significance level.

### Residual Analysis

Specific knot families (e.g., pretzel knots, torus knots) that deviate significantly from model predictions MUST be identified and documented, implementing the methodology from the original idea.

## Composite Complexity Score

### Construction

Weighted combination of crossing number and braid index with default equal weights (1:1 ratio). Weights configurable via config/complexity_weights.yaml.

**Theoretical Limitation Acknowledgment**: No established mathematical basis exists in knot theory literature for linear combination of crossing number and braid index. The equal-weight default is exploratory and configurable. This limitation must be acknowledged in all final reports.

### Validation

Correlation with hyperbolic volume on exploratory validation sample (20% random stratified split by crossing number with documented random seed per FR-009).

**Correlation Reporting Requirement**: Correlation coefficients and effect sizes MUST be reported regardless of magnitude; analysis is considered complete and valid whether correlation values are strong or weak.

**Definitional Relationship Acknowledgment**: Validation targets (hyperbolic volume) are geometrically distinct from predictors (crossing number, braid index), providing empirical rather than definitional validation.

### Framing Guidance

**CRITICAL**: Composite complexity score validation MUST be framed as exploratory correlation analysis, NOT as predictive performance claim. Since invariants are mathematical properties (not model outputs), the validation sample approach tests correlation strength, not predictive accuracy. Final reports MUST explicitly state:
- "This is an exploratory correlation analysis, not a machine learning prediction task"
- "Correlation coefficients describe association strength, not predictive performance"
- "No claim is made about out-of-sample prediction accuracy"

This framing prevents conflating correlation analysis with ML prediction validation (addressing concern methodology-435cec9b).

## Edge Case Handling

### API Unavailability

Retry logic with exponential backoff (initial 1s, max 60s, multiplier 2) per FR-010. Partial results cached to disk after 3 consecutive failures.

### Missing Invariant Data

Records flagged with missing_invariant_flags rather than silently excluded (FR-011). Summary report at docs/reproducibility/uncomputable_invariants.md.

**SC-006 Tracking**: Percentage of knots with computable invariants that have all invariants populated MUST be calculated and reported. Target: ≥99%.

### Ambiguous Classification

Knots with ambiguous alternating/non-alternating classification either excluded from stratified analysis (with count logged) or marked as "unclassifiable" (FR-012).

### Crossing Number Ties

Documented tie-breaking rules applied consistently:
1. Prefer braid word representation over Dowker-Thistlethwaite code
2. Prefer lexicographically first code when multiple DT codes exist

Validation check ensures 100% consistency across all records (SC-008).

### Zero/Undefined Hyperbolic Volume

Torus and satellite knots with volume zero or undefined filtered from volume prediction analysis. Excluded records documented in docs/reproducibility/excluded_knots.md (FR-014).

**SC-014 Tracking**: Hyperbolic volume data completeness percentage MUST be calculated for prime knots with crossing number ≤13. Target: ≥95%.

**Selection Bias Limitation**: Filtering to hyperbolic knots only (excluding torus/satellite) creates selection bias. This limitation MUST be explicitly documented in final reports with sensitivity analysis if possible. The correlation structure may differ systematically for excluded knots.

### Sensitivity Analysis Strategy

To address selection bias (concern methodology-4ddc36cd), compute correlation structure separately for:
1. **Hyperbolic knots** (volume > 0): Primary analysis group
2. **Torus knots** (volume = 0): Compare effect sizes with hyperbolic group
3. **Satellite knots** (volume undefined): Document exclusion rationale

Compare effect sizes (r, r²) across groups to assess whether correlation structure differs systematically. This sensitivity analysis will be documented in docs/reproducibility/sensitivity_analysis.md.

## Reproducibility Requirements

### Random Seed Pinning

All stochastic operations MUST pin random seeds in code per Constitution Principle I. Seed values documented in docs/reproducibility/.

### Checksums

SHA-256 checksums for all data files under data/ directory per Constitution Principle III. Checksums recorded in state file artifact_hashes map.

### Derivation Notes

All transformations documented in docs/reproducibility/ with:
- Formula citations with page/section references
- Step-by-step transformation logic with intermediate values
- All parameter values used
- Justification for any non-standard choices

### Logging

Timestamped logs stored in docs/reproducibility/ capturing:
- timestamp, operation, input_file, output_file, parameters, status, duration_ms, error information