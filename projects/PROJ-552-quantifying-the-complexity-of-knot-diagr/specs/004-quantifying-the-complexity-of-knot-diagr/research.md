# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Research Question (Phase 1)

To what extent do crossing number and braid index jointly predict the hyperbolic volume of prime knots, and does this relationship differ systematically between alternating and non-alternating classes?

## Dataset Strategy

| Dataset | Source URL | Coverage | Verification Status | Notes |
|---------|------------|----------|---------------------|-------|
| Knot Atlas Prime Knots (≤13 crossings) | https://katlas.org | All prime knots with crossing number ≤13 | ✅ VERIFIED | Per FR-001, data downloaded from verified Knot Atlas source |
| OEIS A002863 (Prime knot enumeration) | https://oeis.org/A002863 | Cumulative count up to crossing number 13 (9988 total) | ✅ VERIFIED | CUMULATIVE count only: total number of prime knots up to C13. Per-crossing counts come from HTW enumeration (~49-50 at C13) |
| KnotInfo (Reference values for validation) | https://knotinfo.math.indiana.edu | Subset of knots | ✅ VERIFIED | Per FR-003, used for algorithm validation where reference coverage |
| Hoste-Thistlethwaite-Weeks (HTW) enumeration | https://katlas.org/wiki/Tables | Per-crossing counts | ✅ VERIFIED | Provides per-crossing enumeration (~49-50 knots at C13) |

**Data Collection Plan**:
1. Download prime knot data from Knot Atlas (https://katlas.org) via programmatic export
2. Parse CSV/JSON export containing crossing number, braid index, hyperbolic volume, alternating/non-alternating classification
3. Validate completeness against OEIS A002863 cumulative counts (9988 up to C13) AND HTW enumeration for per-crossing counts (~49-50 at C13)
4. Flag records with missing invariants rather than silent exclusion (per FR-011)

**Phase 1 Validation Scope**: Dataset completeness validation focuses on crossing numbers ≤10 as benchmarking scope. Data collection covers all knots with crossing number ≤13, but full validation across all crossing numbers ≤13 is deferred to future iterations due to computational constraints (prime knots at crossing number 13: ~49-50 per HTW enumeration; cumulative total up to C13: 9988 per OEIS A002863).

## Invariant Computation Strategy

| Invariant | Algorithm | Reference | Validation Approach |
|-----------|-----------|-----------|---------------------|
| Arc Index | Birman-Menasco method | Birman & Menasco (1988), *Mathematische Annalen* 281, pp. 127-138 | Validate against KnotInfo reference values where coverage |
| Seifert Circle Count | Seifert's algorithm on minimal crossing diagrams | Seifert (1934), *Mathematische Annalen* 110, pp. 571-592 | Validate against KnotInfo reference values where coverage |
| Bridge Number | Schubert's bridge decomposition | Schubert (1956), *Mathematische Zeitschrift* 61, pp. 245-288 | Validate against KnotInfo reference values where coverage |

**Representation Availability Definition**: A diagram representation is considered "available" if: (1) minimal crossing diagram with non-empty DT code field, (2) braid word representation with non-empty braid word field, or (3) any combination where at least one field is non-null and non-empty.

**Algorithm Validation Requirement**: System MUST validate algorithm implementation correctness against available reference values from KnotInfo for the dataset subset. If KnotInfo reference coverage is of the dataset, validation against KnotInfo MUST be skipped and the limitation MUST be documented in `docs/reproducibility/algorithm_validation.md` with pass/fail status per invariant and per algorithm, noting the coverage constraint and the skip rationale. Pass/fail threshold: match with reference values where reference data exists.

## Statistical Analysis Plan

### Regression Models (FR-005)

| Model Type | Predictors | Outcome | Metrics |
|------------|------------|---------|---------|
| Linear Regression | Crossing number, Braid index | Hyperbolic volume | R², AIC/BIC, MAE, VIF |
| Polynomial Regression | Crossing number, Braid index, interaction terms | Hyperbolic volume | R², AIC/BIC, MAE, VIF |
| Logarithmic Regression | log(Crossing number), log(Braid index) | Hyperbolic volume | R², AIC/BIC, MAE, VIF |

### Murasugi's Theorem Constraint

For alternating knots, braid index is functionally dependent on crossing number (deterministic relationship per Murasugi's theorem: braid index equals crossing number plus a constant for alternating knots). This creates perfect multicollinearity for the alternating subgroup. Regression analysis will be stratified:

- **Alternating knots**: Excluded from joint regression analysis (braid index is deterministic function of crossing number)
- **Non-alternating knots**: Only non-alternating knots will be used for joint predictor modeling

**VIF Assessment**: Compute variance inflation factors (VIF) for all predictors in non-alternating subgroup. If VIF > 5, flag in final reports as potential multicollinearity issue affecting coefficient interpretation.

**Mathematical Constraint Acknowledgment**: Even in non-alternating knots, braid index is bounded by crossing number (braid index ≤ crossing number). This creates inherent correlation structure. VIF > 5 threshold may be insufficient for this regime where predictors are bounded by mathematical constraints. **Recommendation**: Report partial correlation coefficients controlling for crossing number to isolate braid index's independent contribution to hyperbolic volume prediction.

### Correlation Analysis (FR-008)

| Test | Purpose | Reporting Requirements |
|------|---------|------------------------|
| Pearson Correlation | Linear relationship strength | Report alongside Spearman; acknowledge discrete data limitation |
| Spearman Correlation | Monotonic relationship strength | Primary correlation measure for discrete invariants |
| ANOVA / Welch's ANOVA | Group differences (alternating vs non-alternating) | Report p-values, Cohen's d effect sizes; perform Levene's test and Shapiro-Wilk test before ANOVA |
| Kruskal-Wallis | Non-parametric group comparison | Use if ANOVA assumptions violated |

**Mandatory Dual Correlation**: Per Constitution Principle VII, BOTH Pearson AND Spearman correlations MUST be reported when distribution assumptions cannot be verified a priori—this is a mandatory requirement, not conditional.

### Composite Complexity Score (FR-006)

- Default weights: 1:1 ratio between crossing number and braid index
- Configurable via `config/complexity_weights.yaml`
- Validation: Correlation with hyperbolic volume on exploratory validation sample (random stratified split by crossing number)
- **Hypothesis Nature**: No established mathematical basis exists in knot theory literature for linear combination of crossing number and braid index. The equal-weight default is exploratory and configurable. This validation is **hypothesis-generating, not hypothesis-confirming**. Results indicate empirical correlation strength only, not theoretical construct validity.
- **Theoretical Limitation Acknowledgment**: No established mathematical basis exists in knot theory literature for linear combination of crossing number and braid index. The equal-weight default is exploratory and configurable.

### Cross-Validation Strategy (Addressing methodology-27624403)

**Training/Validation Split**: Models trained on full dataset (≤13 crossings) with 5-fold stratified cross-validation and hold-out sample. Phase 1 scope limitation (≤10 crossings for benchmarking) is separate from validation methodology.

**Procedure**:
1. Split data into 5 stratified folds (by crossing number)
2. Train on 4 folds, validate on 1 fold; repeat 5 times
3. Hold-out of data for final model evaluation (not used in CV)
4. Report mean validation metrics across all folds plus hold-out performance
5. Random seed pinned for reproducibility (configurable via `config/complexity_weights.yaml`)

**Selection Bias Limitation (Addressing methodology-3e2540f9)**: Hyperbolic volume filtering excludes torus and satellite knots (FR-014, Assumptions). This introduces selection bias: the analysis will only capture relationships within hyperbolic knots, not general prime knot complexity. **Final reports MUST explicitly state this limitation to avoid overgeneralization.**

### Regression Output Schema Authority (Addressing plan_consistency-2c26dd4a)

- **CANONICAL**: `contracts/regression_output.schema.yaml` — use for code/models/*.json files
- **LEGACY**: `contracts/regression_model.schema.yaml` — retained for backward compatibility
- **DEPRECATED**: `contracts/regression_result.schema.yaml` — no longer used for new implementations

## Edge Case Handling (FR-010, FR-011, FR-012, FR-014)

| Edge Case | Handling Strategy | Documentation Location |
|-----------|-------------------|------------------------|
| Knot Atlas unavailable/rate-limited | Exponential backoff (→ → →... → max); partial results cached after 3 consecutive failures | `docs/reproducibility/retry_logs.md` |
| Missing invariant data | Flag with `missing_invariant_flags`; include in summary report | `docs/reproducibility/uncomputable_invariants.md` |
| Ambiguous alternating classification | Exclude from stratified analysis or mark as "unclassifiable" | Logged in analysis output |
| Crossing number ties | Apply documented tie-breaking rules consistently | `docs/reproducibility/tie_breaking_rules.md` |
| Zero/undefined hyperbolic volume | Filter out for volume prediction analysis; document excluded records | `docs/reproducibility/excluded_knots.md` |

**Tie-Breaking Rules**: (1) When multiple diagram representations exist for a knot, prefer braid word representation over Dowker-Thistlethwaite code; (2) When multiple Dowker-Thistlethwaite codes exist, prefer lexicographically first code.

## Computational Task Ordering

1. **Data Download** (Phase 0): Download prime knot data from Knot Atlas (≤13 crossings)
2. **Data Validation** (Phase 0): Validate completeness against OEIS A002863 (cumulative 9988) AND HTW enumeration (per-crossing ~49-50 at C13) for crossing numbers ≤10
3. **Invariant Computation** (Phase 1): Compute arc index, Seifert circle count, bridge number where diagram representations available
4. **Exploratory Analysis** (Phase 1): Generate scatter plots of crossing number vs. braid index stratified by classification
5. **Regression Modeling** (Phase 1): Fit linear, polynomial, logarithmic models with VIF assessment; stratified by alternating/non-alternating (alternating excluded from joint regression per Murasugi's theorem); report partial correlations controlling for crossing number
6. **Composite Score Validation** (Phase 1): Construct and validate composite complexity score on exploratory validation sample (hypothesis-generating, not hypothesis-confirming)
7. **Residual Analysis** (Phase 1): Identify knot families deviating from global trend
8. **Reproducibility Documentation** (Phase 1): Generate checksums, derivation notes, timestamped logs

**Phase 1 Conclusion Limitation**: All Phase 1 conclusions must be explicitly limited to validated crossing number ≤10 data; any analysis using crossing number 11-13 data must be marked as exploratory/unvalidated in final reports.

## Success Criteria Alignment

| Success Criterion | Research Action |
|-------------------|-----------------|
| SC-001: Dataset completeness high (limited crossings) | Validate against OEIS A002863 cumulative (9988) AND HTW per-crossing (~49-50 at C13) counts; document in `docs/reproducibility/validation_scope.md` |
| SC-002: Multiple regression models compared | Fit linear, polynomial, logarithmic models; document R², AIC/BIC, MAE |
| SC-003: Composite score correlation reported | Compute Pearson and Spearman correlations on exploratory validation sample |
| SC-004: Reproducible transformations | Pin random seeds; record SHA-256 checksums; write derivation notes |
| SC-005: Retry logic verified | Simulate failures; verify exponential backoff and caching |
| SC-006: substantially populated computable invariants | Document uncomputable records in `docs/reproducibility/uncomputable_invariants.md` |
| SC-007: Ambiguous classification handled | Exclude or mark as "unclassifiable"; no silent exclusions |
| SC-008: Tie-breaking rules validated | Create validation script; confirm consistency |
| SC-009: Exploratory plots generated | Save PNG files (1200x900 pixels) to `data/plots/` |
| SC-010: ≥3 additional invariants computed | Compute arc index, Seifert circle count, bridge number where available |
| SC-011: ANOVA with effect sizes | Report Cohen's d alongside p-values; perform assumption checks |
| SC-012: Algorithm validation high-accuracy match | Validate against KnotInfo where coverage; document pass/fail |
| SC-013: Scope validation documented | Document Phase 1 scope boundaries in `docs/reproducibility/validation_scope.md` |
| SC-014: Hyperbolic volume completeness at a high level | Filter and document excluded knots in `docs/reproducibility/excluded_knots.md` |