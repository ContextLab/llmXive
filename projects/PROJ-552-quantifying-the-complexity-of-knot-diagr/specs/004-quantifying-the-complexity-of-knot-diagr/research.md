# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Research Question

To what extent do crossing number and braid index jointly associate with the hyperbolic volume of prime knots, and does this association differ systematically between alternating and non-alternating classes?

**Note**: This analysis examines association/correlation among mathematical invariants, not prediction in the machine learning sense. All quantities are properties of the same objects—there is no true prediction relationship.

## Dataset Strategy

| Dataset | Source | Fields | Validation Status |
|---------|--------|--------|-------------------|
| Knot prime knots | KnotInfo CSV export / HTW GitHub () | crossing_number, braid_index, hyperbolic_volume, alternating_classification | Downloaded; completeness validated for ≤10, exploratory for 11-13 |
| Prime knot enumeration | OEIS sequence database (https://oeis.org/) | Cumulative count of prime knots per crossing number | Verified: the cumulative total for crossing ≤13 |
| Reference invariants | KnotInfo | Arc index, Seifert circle count, bridge number | Used for algorithm validation where coverage permits |

**Note**: Per the Verified datasets block, no external dataset URLs were verified for the DOI references in the Related Work section. The primary data source remains KnotInfo/HTW, with enumeration counts from OEIS A002863.

## Related Literature Context

The crossing number and braid index are classical knot invariants with established mathematical relationships. Ohyama's inequality relates crossing number to braid index for classical links, and this relationship has been extended to virtual links in subsequent work. The algebraic crossing number conjecture (investigated in earlier work) suggests algebraic crossing number is uniquely determined in minimal braid representation., providing theoretical grounding for our composite complexity approach.

Recent empirical work on prime knots with specific crossing numbers and arc indices (2024) provides a testable dataset framework for correlation analysis at higher crossing numbers. Upper bounds for braid index in terms of crossing number have been established using planar graph embeddings in prior work., which informs our multicollinearity assessment.

**Precision Standard**: Following rigorous scientific measurement standards, the analysis establishes precision thresholds for all computed invariants before correlation analysis proceeds. Braid index requires algorithmic determination (measuring computational uncertainty), while crossing number is tabulated (known exact values).

## Methodology

### Phase 1 Scope Boundaries

This analysis explicitly narrows the original multi-class prime knot exploration (torus, satellite, hyperbolic) to alternating/non-alternating dichotomy only. Multi-class exploration is deferred to Phase 2+.

**Validation Scope**: Dataset completeness validation focuses on crossing numbers ≤10 as the Phase 1 benchmarking scope. Data collection covers all knots with crossing number up to 13, but full validation across all crossing numbers up to that limit is deferred to future iterations.

**Phase 1 Conclusions Limitation**: All Phase 1 conclusions are explicitly limited to the alternating/non-alternating dichotomy AND validated crossing number ≤10 data. Generalization to other knot classes or to unvalidated crossing number 11-13 data requires additional validation.

**Non-Alternating Comparison Note**: The sample size of non-alternating knots at low crossing numbers is underpowered for stratified regression or ANOVA by crossing number. Non-alternating comparison is explicitly exploratory only; primary conclusions limited to overall alternating/non-alternating dichotomy, not stratified analysis by crossing number.

### Computational Task Ordering

Data phases are ordered to ensure:
1. Data is downloaded BEFORE any task that consumes it
2. Models are fitted BEFORE any task that evaluates them
3. Figures are generated BEFORE any task that includes them in the paper

### Invariant Computation

Additional invariants are computed from available diagram representations:
- **Arc index**: Birman-Menasco method (Birman & Menasco, 1988)
- **Seifert circle count**: Seifert's algorithm on minimal crossing diagrams (Seifert, 1934)
- **Bridge number**: Schubert's bridge decomposition (Schubert, 1956)

A diagram representation is "available" if the corresponding field in the KnotInfo/HTW record is non-null and non-empty.

### Statistical Analysis

- **Correlation**: Both Pearson AND Spearman coefficients reported (Constitution Principle VII)
 - **Pearson Limitation Note**: Pearson correlation assumes continuous, normally distributed data. Knot invariants are small integers (crossing numbers 1-13, braid indices similarly bounded). Pearson may have limited interpretability for discrete data with small ranges; Spearman prioritized as primary metric.
- **Regression**: Linear, polynomial (degree=2), and logarithmic (base e) models compared
- **Group differences**: ANOVA with Levene's test for equal variances and Shapiro-Wilk test for normality; robust alternatives used if assumptions violated
- **Effect sizes**: Cohen's d for group comparisons, r or r² for correlations

## Edge Case Strategy

| Edge Case | Handling |
|-----------|----------|
| KnotInfo unavailable | Retry logic with exponential backoff (2s, [deferred], [deferred]...); partial results cached after 3 failures |
| Missing invariant data | Records flagged with missing_invariant_flags; not silently excluded |
| Ambiguous classification | Excluded from stratified analysis or marked "unclassifiable"; count logged in classification_counts.md |
| Crossing number ties | Documented tie-breaking rules applied consistently (see tie_breaking_rules.md) |
| Zero/undefined hyperbolic volume | Filtered from volume association analysis; documented in excluded_knots.md |

## Validation Strategy

### Dataset Completeness

Validation against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration for prime knot counts at each crossing number ≤10. Crossing numbers 11-13 data is downloaded but not validated in Phase 1, documented in `docs/reproducibility/validation_scope.md`.

### Algorithm Validation

System validates algorithm implementation correctness against available reference values from KnotInfo for the dataset subset. If KnotInfo reference coverage is insufficient, validation is skipped and limitation documented in algorithm_validation.md.

### Multicollinearity Assessment

Variance inflation factors (VIF) computed for all predictors. VIF > 5 flagged in final reports as potential multicollinearity issue affecting coefficient interpretation.

### Selection Bias Acknowledgment

Hyperbolic volume filtering excludes torus and satellite knots (FR-014), creating selection bias. Analysis only applies to hyperbolic knots, limiting generalizability. This limitation is explicitly documented; observed relationships between invariants may differ for non-hyperbolic knot classes.

## Reproducibility Requirements

- Random seeds pinned in code
- SHA-256 checksums for all data files
- Derivation notes with formula citations and step-by-step logic
- Timestamped logs capturing operation details
- All code runnable end-to-end without manual intervention