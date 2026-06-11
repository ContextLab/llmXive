# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research investigates the joint predictive relationship between crossing number and braid index for hyperbolic volume in prime knots, with systematic comparison between alternating and non-alternating classes. Phase 1 focuses on the alternating/non-alternating dichotomy for crossing numbers ≤10 (validated) and ≤13 (downloaded).

## Dataset Strategy

| Dataset | Source | Purpose | Verified URL |
|---------|--------|---------|--------------|
| Knot Atlas Prime Knots (≤13) | Knot Atlas (katlas.org) | Primary data source for crossing number, braid index, hyperbolic volume, alternating classification | NO verified source found (per verified datasets block; specification cites https://katlas.org as canonical source) |
| KnotInfo Reference Values | KnotInfo (katlas.org/wiki/KnotInfo) | Algorithm validation for computed invariants (arc index, Seifert circle count, bridge number) | NO verified source found (per verified datasets block) |
| Hoste-Thistlethwaite-Weeks Enumeration | OEIS A002863 | Dataset completeness validation for prime knot counts at each crossing number ≤10 | https://oeis.org/A002863 |
| Minimal Grid Diagrams Study (2024) | arXiv 2402.02717 | Empirical data on prime knots with crossing number 13 | https://arxiv.org/abs/2402.02717 |
| Bisected Vertex Leveling Study (2018) | arXiv 1806.09719 | Upper bounds for braid index in terms of crossing number; polynomial regression justification | https://arxiv.org/abs/1806.09719 |

**Dataset Count Clarification**: OEIS A002863(13) represents the CUMULATIVE count of prime knots with crossing number ≤13. The exact number of prime knots at crossing number 13 specifically is known, as established by Hoste-Thistlethwaite-Weeks enumeration. This distinction is critical for dataset completeness validation (SC-001).

**CRITICAL SPEC DEFECTS FLAGGED FOR KICKBACK**:
1. **Spec Factual Error (Assumptions Section)**: The spec.md incorrectly states 'For crossing number 13, the exact count is 49 prime knots, as established in OEIS A002863'. OEIS A002863(13)=9988 is the CUMULATIVE count ≤13. The knots at a specific crossing number should be attributed to Hoste-Thistlethwaite-Weeks enumeration.
2. **Spec Placeholder SC-006**: Missing threshold percentage. Plan documents provisional default of **** (flagged for kickback correction).
3. **Spec Placeholder SC-012**: Missing threshold percentage. Plan documents provisional default of **** (flagged for kickback correction).

**Note**: Per verified datasets block constraints, Knot Atlas URL is not in the verified sources list. The specification cites https://katlas.org as the canonical source, but verification status is "NO verified source found". Implementation must handle this by implementing retry logic with exponential backoff (FR-010) and documenting the verification limitation in `docs/reproducibility/validation_scope.md`.

**Training/Validation Specification**: Regression models trained on validated c≤10 data ONLY. c=11-13 data reserved for exploratory analysis (model evaluation only, not training).

## Data Sources and Access

### Knot Atlas (Primary Source)

The Knot Atlas provides comprehensive data on prime knots including:
- Crossing number (tabulated)
- Braid index (algorithmically determined)
- Hyperbolic volume (geometric invariant)
- Alternating/non-alternating classification
- Diagram representations (Dowker-Thistlethwaite codes, braid words)

**Access Method**: HTTP API or CSV export with documented column mapping (FR-001). Retry logic with exponential backoff (initial:, max:, multiplier: 2) implemented per FR-010.

**Version Tracking**: Knot Atlas version captured from API response headers or metadata file; stored in InvariantsDataset.data_source_version field.

### Validation Against Reference Values

KnotInfo provides reference values for algorithm validation. Per FR-003, if KnotInfo reference coverage is of dataset (threshold from plan), validation is skipped and limitation documented in `docs/reproducibility/validation_scope.md`.

### Empirical Inequality Verification

Before analysis, verify known mathematical inequalities hold for dataset:
- bridge_number ≤ crossing_number
- braid_index ≤ crossing_number (for most knots)

Discrepancies documented in `data/derivation_notes.md` per Constitution Principle VI (Mathematical Invariant Consistency).

## Computational Methods

### Invariant Computation Algorithms

1. **Arc Index**: Birman-Menasco method (Birman & Menasco, 1988, "A Algorithm for the Arc Index of a Knot", *Mathematische Annalen*, 281, pp. 127-138)
2. **Seifert Circle Count**: Seifert's algorithm on minimal crossing diagrams (Seifert, 1934, "Über das Geschlecht von Knoten", *Mathematische Annalen*, 110, pp. 571-592); formula: s(D) (source: math/0303273)
3. **Bridge Number**: Schubert's bridge decomposition (Schubert, 1956, "Über eine numerische Knoteninvariante", *Mathematische Zeitschrift*, 61, pp. 245-288); 2-bridge knots (source: Wikipedia)

### Regression Modeling

Three model types compared (FR-005):
1. Linear regression: `volume ~ crossing_number + braid_index`
2. Polynomial regression: `volume ~ crossing_number + braid_index + crossing_number² + braid_index²`
3. Logarithmic regression: `volume ~ log(crossing_number) + log(braid_index)`
4. **Alternative**: Spline regression if polynomial overfitting detected

**Polynomial Justification**: Despite discrete predictors, polynomial terms capture known non-linear relationships in knot geometry (citing arXiv 1806.09719). If VIF > 5 or cross-validation error increases, spline regression used as alternative.

**Multicollinearity Assessment**: Variance Inflation Factors (VIF) computed for all predictors. VIF > 5 flagged as potential multicollinearity issue (per FR-005, citing DOI 10.1142/S0218216519500020 and arXiv 1805.04428).

### Statistical Testing

- **Correlation**: Both Pearson AND Spearman correlations reported where distribution assumptions cannot be verified a priori (Constitution Principle VII)
- **ANOVA**: For group differences between alternating and non-alternating knots, with Levene's test for equal variances and Shapiro-Wilk test for normality (FR-008)
- **Effect Sizes**: Cohen's d for group comparisons, r or r² for correlations

### Power Analysis

**Sample Size**: ~632 knots at c≤10; after filtering for hyperbolic volume (removing torus/satellite knots), a subset of knots remain.

**Filtering Logic Documentation**: The exact filtering logic for torus/satellite exclusion must be documented in `docs/reproducibility/power_analysis.md` with exact counts from the source dataset. The filtering removes knots where hyperbolic_volume is zero or undefined.

**Power Calculation**: For 2-predictor regression with α=0.05, power=0.80, minimum detectable correlation r≥0.13. This provides adequate power for hypothesis-hypothesis-generating exploratory analysis.

**Documentation**: Full power analysis documented in `docs/reproducibility/power_analysis.md`.

## Expected Findings

### Hypothesis

Crossing number and braid index jointly predict hyperbolic volume, with non-linear relationship differing between alternating and non-alternating classes.

### Validation Approach

Composite complexity score (equal-weighted crossing number + braid index) validated against exploratory validation sample using random stratified split by crossing number. Correlation coefficients and effect sizes reported regardless of magnitude (exploratory analysis, not ML prediction).

### Construct Validity Limitation

**Acknowledged**: Composite score validated against hyperbolic volume is predictive correlation, not construct validation (circular by design). Alternative validation against geometric properties (canonical longitude, twist number) where available in literature will be documented as hypothesis-generating, not confirmatory. This limitation is explicitly stated in final paper.

## Limitations

1. **Phase 1 Scope**: Conclusions explicitly limited to validated crossing number ≤10 data; crossing number 11-13 data marked as exploratory/unvalidated
2. **Invariant Dependencies**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number); validation is exploratory correlation, not independence testing
3. **Hyperbolic Volume Availability**: Torus and satellite knots have volume zero or undefined; filtered from volume prediction analysis (FR-014)
4. **Multicollinearity**: Braid index ≤ crossing number for most knots; VIF assessment quantifies impact on coefficient interpretation
5. **Discrete Data**: Pearson correlation assumes continuous data with normal distribution; interpretation limited by discrete nature of crossing number and braid index (small integers)
6. **Generalizability**: Results apply only to hyperbolic knots, not all prime knots. This selection bias is explicitly stated in final paper.
7. **Construct Validity**: Composite complexity score validated only against hyperbolic volume (predictive correlation, not construct validation). Alternative validation documented as hypothesis-generating.
8. **Unverified Data Sources**: Knot Atlas and KnotInfo sources not verified per Reference-Validator Agent; analysis proceeds with documented limitations.
9. **OEIS Count Clarification**: OEIS A002863(13)=9988 is CUMULATIVE ≤13, not 'at c=13'. The 49 knots at c=13 comes from Hoste-Thistlethwaite-Weeks enumeration.
10. **Spec Defects Pending Correction**: SC-006 (provisional) and SC-012 (provisional) thresholds flagged for kickback correction; validation checks use provisional values but cannot be marked complete until spec is amended.

## Reproducibility Requirements

- Random seeds pinned in code (Constitution Principle I)
- SHA-256 checksums for all data files recorded under `data/` (Constitution Principle III)
- Derivation notes with formula citations, step-by-step transformation logic, parameter values (FR-009)
- Timestamped logs capturing operation, input/output files, parameters, status, duration (FR-009)
- Power analysis documented in `docs/reproducibility/power_analysis.md`
- License compliance documented in `docs/reproducibility/license_compliance.md`
- **Spec Defect Tracking**: All spec defects documented in `docs/reproducibility/spec_defects.md` with kickback status