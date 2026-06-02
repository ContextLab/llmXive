# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Research Question

To what extent do crossing number and braid index jointly predict the hyperbolic volume of prime knots, and does this relationship differ systematically between alternating and non-alternating classes?

**Scope Boundary (Phase 1)**: This analysis is stratified by alternating/non-alternating classification only. Multi-class prime knot exploration (torus, satellite, hyperbolic) is deferred to Phase 2+.

## Dataset Strategy

| Dataset | Description | Source | Access Method |
|---------|-------------|--------|---------------|
| Knot Atlas Prime Knots | Prime knots with crossing number ≤13 including crossing number, braid index, hyperbolic volume, alternating classification | Knot Atlas | Programmatic download (https://katlas.org) |
| Hoste-Thistlethwaite-Weeks Enumeration | Prime knot counts by crossing number for validation | KnotInfo | Reference only (no direct URL; counts documented in literature) |
| Minimal Grid Diagrams Study | Subset of prime knots with crossing number 13 and arc index 13 | arXiv | https://arxiv.org/abs/2402.02717 |

**Data Collection Order**: Data MUST be downloaded BEFORE any invariant computation or analysis phase. This ensures computational tasks have required inputs available.

**Validation Scope (Phase 1)**: Dataset completeness validation focuses on crossing numbers ≤10 as the Phase 1 benchmarking scope. Data collection covers all knots with crossing number ≤13, but full validation across all crossing numbers ≤13 is deferred to future iterations due to computational constraints (9,988 prime knots at crossing number 13).

## Methodology

### Phase 1: Data Download and Parsing (User Story 1)

1. Download prime knot data from Knot Atlas
2. Parse and clean dataset to extract consistent representations
3. Validate completeness against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration
4. Record checksums under data/ per Constitution Principle III

### Phase 2: Invariant Computation and Exploratory Analysis (User Story 2)

1. Compute arc index via Birman-Menasco method (Birman & Menasco, 1988)
2. Compute Seifert circle count via Seifert's algorithm (Seifert, 1934)
3. Compute bridge number via Schubert's bridge decomposition (Schubert, 1956)
4. Generate scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification

### Phase 3: Regression Modeling and Validation (User Story 3)

1. Fit linear regression models
2. Fit polynomial/non-linear regression models
3. Compute variance inflation factors (VIF) to assess multicollinearity
4. Construct composite complexity score (equal weights default)
5. Validate against exploratory validation sample (20% random stratified split)
6. Perform ANOVA testing for group differences with assumption checks (Levene's test, Shapiro-Wilk test)
7. Analyze residuals to identify knot families deviating from global trend

### Phase 4: Reproducibility Documentation (User Story 4)

1. Implement retry logic with exponential backoff
2. Flag records with missing_invariant_flags rather than silent exclusion
3. Document tie-breaking rules and validate consistency
4. Record all checksums, derivation notes, random seeds, and logs

## Statistical Analysis Plan

- **Correlation Analysis**: Report BOTH Pearson AND Spearman correlation coefficients (Constitution Principle VII)
- **Regression Models**: Compare linear vs. non-linear models with R², AIC/BIC, MAE metrics
- **Group Differences**: ANOVA with effect sizes (Cohen's d); use robust alternatives if assumptions violated
- **Multicollinearity**: VIF assessment for all predictors; flag if VIF > 5
- **Validation**: Correlation coefficients and effect sizes reported regardless of magnitude

## Limitations and Assumptions

1. **Hyperbolic Volume Availability**: Torus and satellite knots have volume zero or undefined; these will be filtered with documentation in docs/reproducibility/excluded_knots.md
2. **Invariant Dependencies**: Arc index, Seifert circle count, bridge number have known mathematical constraints with crossing number and braid index; validation is exploratory correlation analysis
3. **Composite Score Theoretical Basis**: No established mathematical basis for linear combination of crossing number and braid index; equal-weight default is exploratory
4. **Discrete Data**: Pearson correlation assumes continuous data with normal distribution; interpretation limited by discrete nature of invariants (small integers)
5. **Phase 1 Scope**: Conclusions explicitly limited to alternating/non-alternating dichotomy; generalization to other knot classes requires Phase 2+ validation
