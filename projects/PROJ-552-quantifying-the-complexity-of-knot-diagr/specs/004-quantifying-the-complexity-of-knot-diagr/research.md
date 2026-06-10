# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31

## Research Question

To what extent do crossing number and braid index jointly predict the hyperbolic volume of prime knots, and does this relationship differ systematically between alternating and non-alternating classes?

## Background

### Knot Theory Fundamentals

Knot theory studies mathematical knots—closed loops in 3-dimensional space that cannot be untangled without cutting. A central challenge is quantifying knot complexity through invariants: properties that remain unchanged under continuous deformations.

**Crossing Number**: The minimum number of crossings in any diagram of a knot. This is a fundamental but computationally difficult invariant to determine for arbitrary knots.

**Braid Index**: The minimum number of strands needed to represent a knot as a closed braid. This captures a different geometric aspect than crossing number.

**Hyperbolic Volume**: For hyperbolic knots (the majority of prime knots), the volume of the complement space equipped with its unique hyperbolic metric. This provides a geometric measure of complexity.

### Phase 1 Scope Boundary

This analysis explicitly narrows the original multi-class prime knot exploration (torus, satellite, hyperbolic) to alternating/non-alternating dichotomy only. Multi-class exploration is deferred to Phase 2+. The Phase 1 conclusions are explicitly limited to the alternating/non-alternating dichotomy AND validated crossing number ≤10 data.

## Dataset Strategy

| Dataset | Description | Source/Loader | Verified Status |
|---------|-------------|---------------|-----------------|
| Knot Atlas Prime Knots | Prime knots with crossing number ≤13, including crossing number, braid index, hyperbolic volume, alternating/non-alternating classification | Knot Atlas (https://katlas.org) | NO verified source found (describe by name only) |
| KnotInfo Reference Values | Reference values for algorithm validation (arc index, Seifert circle count, bridge number) | KnotInfo | NO verified source found (describe by name only) |
| Hoste-Thistlethwaite-Weeks Enumeration | Prime knot counts at each crossing number | OEIS A002863 (https://oeis.org/A002863) | NO verified source found (describe by name only) |

**Important Note**: Per verified datasets guidance, Knot Atlas and KnotInfo URLs are not in the verified sources list. These datasets are described by name only; no URLs are fabricated. The Hoste-Thistlethwaite-Weeks enumeration reference (OEIS A002863) is also not in the verified sources list and is described by name only.

### Data Completeness Expectations

- Prime knots at crossing number 13: 9988 (source: OEIS A002863)
- Phase 1 validation benchmark: crossing numbers ≤10 (≥95% completeness on required invariant fields)
- Phase 1 data collection: extends to crossing number ≤13 (not validated in Phase 1)

**Rationale**: Full validation across all 9988 prime knots at crossing number 13 is computationally impractical for Phase 1 exploratory analysis. This is a deliberate scope decision for practical verification purposes.

## Methodology

### Phase 1: Data Acquisition and Validation

**Task Order**: Data download MUST precede any analysis consuming the data.

1. Download prime knot data from Knot Atlas for crossing number ≤13
2. Parse and clean dataset to extract consistent representations
3. Validate dataset completeness against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration for crossing numbers ≤10
4. Document validation scope in `docs/reproducibility/validation_scope.md`

### Phase 2: Invariant Computation

**Task Order**: Invariant computation MUST precede exploratory analysis.

1. Compute arc index via Birman-Menasco method (Birman & Menasco, 1988)
2. Compute Seifert circle count via Seifert's algorithm on minimal crossing diagrams (Seifert, 1934)
3. Compute bridge number via Schubert's bridge decomposition (Schubert, 1956)
4. Validate against KnotInfo reference values (≥95% match threshold where coverage ≥10%)
5. Flag records with missing invariant data rather than silent exclusion

### Phase 3: Exploratory Analysis

**Task Order**: Exploratory analysis MUST precede regression modeling.

1. Generate scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification
2. Compute summary statistics for each knot class
3. Identify potential correlation patterns before model fitting

### Phase 4: Regression Modeling

**Task Order**: Model fitting MUST precede evaluation and residual analysis.

1. Fit linear regression model (crossing number + braid index → hyperbolic volume)
2. Fit polynomial regression model (including squared terms)
3. Fit logarithmic regression model
4. Compute variance inflation factors (VIF) to assess multicollinearity
5. Validate composite complexity score on exploratory validation sample (20% random stratified split)

### Phase 5: Statistical Validation

**Task Order**: Statistical tests MUST follow model fitting.

1. Perform ANOVA for group differences (alternating vs. non-alternating)
2. Compute Pearson and Spearman correlations (both required per Constitution Principle VII)
3. Report effect sizes (Cohen's d for group comparisons, r/r² for correlations)
4. Identify knot families with significant residual deviations

## Key Findings (Expected)

### Multicollinearity Consideration

Crossing number and braid index are not fully independent predictors (braid index ≤ crossing number for most knots per known inequality). Variance Inflation Factor (VIF) assessment will quantify multicollinearity impact on coefficient interpretation.

### Composite Score Construction

A composite complexity score uses equal weights (1:1 ratio) between crossing number and braid index as the default configuration. No established mathematical basis exists in knot theory literature for linear combination of these invariants. The equal-weight default is exploratory and configurable.

### Measurement Precision Standard

Consistent with rigorous scientific measurement standards, the analysis must establish precision thresholds for all computed invariants before correlation analysis proceeds. This includes documenting computational uncertainty for braid index (which requires algorithmic determination) versus crossing number (which is tabulated).

## Related Work

- **Ohyama's Inequality**: Establishes foundational inequalities relating crossing number and braid index for classical links.
- **Virtual Link Extensions**: Extends Ohyama's inequality to virtual links and generalizes the relationship framework.
- **Algebraic Crossing Number (2006)**: Investigates the conjecture that algebraic crossing number is uniquely determined in minimal braid representation.
- **Minimal Grid Diagrams (2024)**: Provides empirical data on 9,988 prime knots with crossing number 13, establishing a testable dataset for correlation analysis.
- **Bridge Number Relations**: Relates crossing number to bridge number, offering a third invariant for potential composite measures.
- **Bisected Vertex Leveling (2018)**: Presents upper bounds for braid index in terms of crossing number using planar graph embeddings.

## Risk Assessment

### Data Availability Risk

**Risk**: Knot Atlas may be unavailable or rate-limited during download.  
**Mitigation**: Implement retry logic with exponential backoff (initial 1s, max 60s, multiplier 2); cache partial results after 3 consecutive failures.

### Computational Complexity Risk

**Risk**: Invariant computation may be infeasible for some knots.  
**Mitigation**: Flag records with missing invariant data; document uncomputable invariants in `docs/reproducibility/uncomputable_invariants.md`.

### Statistical Assumption Risk

**Risk**: ANOVA assumptions (normality, equal variances) may be violated.  
**Mitigation**: Perform Levene's test and Shapiro-Wilk test; use robust alternatives (Welch's ANOVA, Kruskal-Wallis) if assumptions violated.

### Scope Creep Risk

**Risk**: Phase 1 analysis may be extended beyond validated crossing number ≤10 data.  
**Mitigation**: Document all findings from crossing number 11-13 data as exploratory/unvalidated; limit Phase 1 conclusions to validated ≤10 data.

## Reproducibility Requirements

- All random seeds pinned in `config/random_seeds.yaml`
- SHA-256 checksums for all data files recorded in `data/checksums.txt`
- Derivation notes with formula citations and step-by-step logic in `docs/reproducibility/derivation_notes.md`
- Timestamped logs capturing `timestamp`, `operation`, `input_file`, `output_file`, `parameters`, `status`, `duration_ms`
- Algorithm validation results in `docs/reproducibility/algorithm_validation.md`
- Excluded knots documented in `docs/reproducibility/excluded_knots.md`
- Tie-breaking rules documented in `docs/reproducibility/tie_breaking_rules.md`
