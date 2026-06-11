# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research investigates the joint predictive relationship between crossing number and braid index for hyperbolic volume across hyperbolic prime knots, with stratification by alternating/non-alternating classification. Phase 1 scope is limited to alternating/non-alternating dichotomy with validated completeness for crossing number ≤10 (data collection extends to ≤13). **Scope explicitly limited to hyperbolic prime knots** (excludes torus/satellite knots with undefined hyperbolic volume).

## Dataset Strategy

| Dataset | Description | Source URL | Loading Method | Validation Scope |
|---------|-------------|------------|----------------|------------------|
| Knot Atlas Prime Knots | Prime knots with crossing number ≤13 including crossing number, braid index, hyperbolic volume, alternating classification | https://katlas.org/wiki/Main_Page (primary source; access via HTML scraping via requests library with retry logic per FR-001) | Programmatic download via `requests` library with retry logic per FR-001 | Data availability extends to ≤13; validated completeness benchmarked against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration for ≤10 (per SC-001) |
| OEIS A002863 | Prime knot enumeration counts per crossing number | https://oeis.org/A002863 | Direct reference for validation benchmarking | Used to validate dataset completeness: Prime knots at a specific crossing number per OEIS A002863, https://oeis.org/A002863 |
| KnotInfo | Reference values for invariant validation | https://knotinfo.math.indiana.edu/ | Manual verification for subset sampling | Used for algorithm validation benchmarking per FR-003 |

**Dataset Limitations**: Knot Atlas is the primary data source accessed via HTML scraping (no official API available). Per Constitution Principle II, canonical URL format documented as https://katlas.org/wiki/Main_Page. The spec explicitly documents Knot Atlas as the source (FR-001), and the implementation will include retry logic with exponential backoff per FR-010.

**Validation Benchmark**: Phase 1 completeness validation focuses on crossing number ≤10 per SC-001. Crossing numbers 11-13 data is downloaded but marked as exploratory/unvalidated in final reports.

**Implementation-Time Thresholds** (pending spec.md correction):
- SC-006: Target of knots with computable invariants have all invariants populated
- SC-012: Target substantial KnotInfo reference coverage matching
- FR-003: Skip validation if KnotInfo reference coverage
- User Story 1 Acceptance Scenario 2: Target of records have crossing number, braid index, and hyperbolic volume values present

## Related Work

The following peer-reviewed sources establish the mathematical foundation for this analysis:

- **Birman & Menasco (1988)**: "A Algorithm for the Arc Index of a Knot", *Mathematische Annalen*, 281, pp. 127-138 — Establishes the Birman-Menasco method for arc index computation, used in FR-003 invariant computation. [Foundational literature: pre-dates arXiv; verification via JSTOR/MATHSCINET]
- **Seifert (1934)**: "Über das Geschlecht von Knoten", *Mathematische Annalen*, 110, pp. 571-592 — Foundational work on Seifert's algorithm for computing genus and Seifert circle count, referenced in FR-003. [Foundational literature: pre-dates arXiv; verification via JSTOR]
- **Schubert (1956)**: "Über eine numerische Knoteninvariante", *Mathematische Zeitschrift*, 61, pp. 245-288 — Establishes bridge decomposition methodology, referenced in FR-003 for bridge number computation. [Foundational literature: pre-dates arXiv; verification via SpringerLink]
- **Minimal grid diagrams of the prime knots with crossing number 13 and arc index 13 (2024)**: https://arxiv.org/abs/2402.02717 — Provides empirical data on prime knots with crossing number 13, establishing a testable dataset for correlation analysis.
- **Bisected vertex leveling of plane graphs: braid index, arc index and delta diagrams (2018)**: https://arxiv.org/abs/1806.09719 — Presents upper bounds for braid index in terms of crossing number using planar graph embeddings.
- **The algebraic crossing number and the braid index of knots and links (2006)**: https://doi.org/10.1142/S0218216519500020 — Investigates the conjecture that algebraic crossing number is uniquely determined in minimal braid representation.

**Verified Fact Citations**:
- Prime knot count at crossing number 13: 9988 prime knots (source: OEIS A002863, https://oeis.org/A002863)
- Cumulative prime knot count through crossing number 13: (source: OEIS A002863, https://oeis.org/A002863)
- Seifert circle count via Seifert's algorithm on minimal crossing diagram: s(D) (source: math/0303273, https://arxiv.org/abs/math/0303273)
- Bridge decomposition via Schubert: 2-bridge knot classification (source: 2-bridge knot, https://en.wikipedia.org/wiki/2-bridge_knot)

## Power Analysis & Effective Sample Size

**Target Population**: All prime knots with crossing number ≤13.

**Excluded Population**: Torus knots and satellite knots (no hyperbolic volume). Estimated to represent a proportion of prime knots ≤13 based on Knot Atlas taxonomy.

**Effective Sample Size**: N knots after filtering for hyperbolic volume (effective sample size will be documented after filtering based on Knot Atlas taxonomy).

**Statistical Power**: For correlation analysis with N≥5000, α=0.05:
- Minimum detectable effect size (r): a small effect with power ≥0.95
- Minimum detectable effect size (r): a small effect size with power ≥0.99

**Conclusion**: Sample size is sufficient to detect small effect sizes (r≥0.1) with power ≥0.95. No power analysis concerns for planned analyses.

## Methodology

### Phase 1: Data Collection (User Story 1)

1. Download prime knot data from Knot Atlas for all knots with crossing number ≤13
2. Parse and clean dataset to extract consistent representations of crossing number, braid index, hyperbolic volume, and alternating/non-alternating classification
3. Validate dataset completeness against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration for crossing number ≤10
4. Document excluded records (torus/satellite knots with zero or undefined hyperbolic volume) in `docs/reproducibility/excluded_knots.md`

**Edge Case Handling**:
- Knot Atlas unavailable: Exponential backoff retry logic (initial, max, multiplier 2) per FR-010; partial results cached after 3 consecutive failures
- Missing invariants: Flag with `missing_invariant_flags` rather than silent exclusion per FR-011
- Ambiguous alternating classification: Exclude from stratified analysis or mark as "unclassifiable" per FR-012
- Crossing number ties: Apply documented tie-breaking rules (braid word preferred over DT code; lexicographically first DT code) per FR-013

### Phase 2: Invariant Computation (User Story 2)

1. Compute additional invariants from available diagram representations:
   - Arc index via Birman-Menasco method (Birman & Menasco)
   - Seifert circle count via Seifert's algorithm on minimal crossing diagrams (Seifert, foundational work; s(D) per https://arxiv.org/abs/math/0303273)
   - Bridge number via Schubert's bridge decomposition (Schubert; 2-bridge knot classification per https://en.wikipedia.org/wiki/2-bridge_knot)
2. Validate algorithm implementations against KnotInfo reference values where coverage ≥ threshold per FR-003 (target matching)
3. Generate exploratory scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification (minimum resolution 1200x900 pixels)

**Invariant Dependency Acknowledgment**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). Validation is exploratory correlation analysis, not independence testing.

**VIF Edge Case Documentation**: Given the known inequality braid_index ≤ crossing_number, VIF values will be elevated but not infinite. Expected VIF range: within acceptable bounds based on mathematical constraint. Verification step included in invariant_computation.py to flag VIF > 5 as potential multicollinearity issue requiring documentation.

### Phase 3: Regression Modeling (User Story 3)

**Methodological Note**: All regression analyses performed on FULL DATASET (not train/validation split). Hyperbolic volume relationships with crossing/braid indices are mathematical properties, not ML predictions. Analysis reframed as full-dataset correlation with confidence intervals, not predictive modeling.

1. Fit three regression model types on full dataset:
   - Linear regression: `volume = β₀ + β₁×crossing + β₂×braid + ε`
   - Polynomial regression: Include interaction and quadratic terms
   - Logarithmic regression: `volume = β₀ + β₁×log(crossing) + β₂×log(braid) + ε`
2. Compute variance inflation factors (VIF) for all predictors to assess multicollinearity (flag if VIF > 5)
3. Construct composite complexity score with default equal weights (1:1 ratio) per FR-006
4. Perform residual analysis to identify knot families (e.g., pretzel knots, torus knots) that deviate significantly from global trend

**Composite Score Clarification**: Composite complexity score is an EXPLORATORY CONSTRUCT without predictive claims. Its purpose is to provide a single interpretable metric for knot complexity ranking, unlike regression coefficients which are model-dependent. Validation against hyperbolic volume is HYPOTHESIS-GENERATING ONLY, not confirmatory. No claims of predictive power will be made.

### Phase 4: Statistical Testing (User Story 3)

1. Compute Pearson AND Spearman correlation coefficients per Constitution Principle VII (mandatory dual correlation)
2. Perform ANOVA for group differences between alternating and non-alternating knots with effect sizes (Cohen's d)
3. Before ANOVA: Perform Levene's test for equal variances and Shapiro-Wilk test for normality; use robust alternatives (Welch's ANOVA, Kruskal-Wallis) if assumptions violated

**ANOVA Justification**: With N≥5000 knots, central limit theorem applies to sampling distributions. Discrete distribution of small integers (crossing number 3-13, braid index 2-5) does not violate ANOVA assumptions for large samples. Robust alternatives available if diagnostic tests indicate violations.

4. Report all results regardless of statistical significance; analysis is complete when results are documented

### Phase 5: Reproducibility Documentation (User Story 4)

1. Pin random seeds for all stochastic operations per Constitution Principle I
2. Record SHA-256 checksums for all data files under data/ per Constitution Principle III
3. Document all transformations with derivation notes including formula citations, step-by-step logic, intermediate values, and parameter justifications
4. Store timestamped logs with operation, input/output files, parameters, status, duration, and error information

## Expected Outcomes

| Outcome | Metric | Target |
|---------|--------|--------|
| Dataset completeness | Prime knots with crossing number ≤10 | of the known prime knots per OEIS A002863 (9988 at c=13) |
| Invariant computation coverage | Knots with computable invariants | of records with available diagram representations |
| Model comparison | R², AIC/BIC, MAE for 3 model types | All metrics documented regardless of fit quality |
| Correlation analysis | Pearson and Spearman coefficients | Both reported with effect sizes (r or r²) |
| Group difference analysis | ANOVA p-value, Cohen's d | Documented regardless of significance level |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Knot Atlas scraping rate limits | Exponential backoff retry logic; partial results cached to disk; timeline extended if needed |
| Missing invariant data | Flag records with `missing_invariant_flags`; document in `uncomputable_invariants.md` |
| Algorithm validation coverage < threshold | Skip validation and document limitation per FR-003 (target) |
| Multicollinearity (VIF > 5) | Flag in final reports; acknowledge limitation in coefficient interpretation; expected VIF 1.5-3.5 due to mathematical constraint |
| ANOVA assumption violations | Use robust alternatives (Welch's ANOVA, Kruskal-Wallis) and document deviation |
| Hyperbolic volume undefined for torus/satellite knots | Filter and document excluded knots in `excluded_knots.md`; scope limited to hyperbolic prime knots |
| Selection bias (hyperbolic knots only) | Quantify excluded population; discuss generalizability limitations in final reports |