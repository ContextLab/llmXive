# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Background

Knot theory provides a rich mathematical framework for understanding topological complexity through classical invariants. The crossing number (minimum number of crossings in any diagram) and braid index (minimum number of strands in any braid representation) are both fundamental measures that capture different facets of a knot's geometric structure. This research investigates whether these two invariants jointly predict the hyperbolic volume—a geometric invariant that measures the "size" of the knot complement in hyperbolic 3-space.

## Research Question (Phase 1)

To what extent do crossing number and braid index jointly correlate with the hyperbolic volume of prime knots, and does this relationship differ systematically between alternating and non-alternating classes?

**Phase 1 Scope Limitation**: This analysis is explicitly limited to the alternating/non-alternating dichotomy. Multi-class exploration (torus, satellite, hyperbolic knots) is deferred to Phase 2+. All conclusions must be qualified as limited to validated crossing number ≤10 data per SC-001.

## Dataset Strategy

### Primary Data Source

The primary dataset will be obtained from Knot Atlas (https://katlas.org), which provides comprehensive tables of prime knots with computed invariants. **IMPORTANT URL STABILITY DISCLAIMER**: Knot Atlas URL stability is not independently verified per Constitution Principle II. This creates a reproducibility risk. Mitigation strategies:

- **Primary**: Download from https://katlas.org with exponential backoff retry logic (FR-010)
- **Fallback**: Use checksummed mirror if primary URL becomes unavailable (documented in docs/reproducibility/url_fallback.md)
- **Verification**: All downloaded files are checksummed (SHA-256) and recorded in data/checksums.txt per Constitution Principle III

**KnotInfo**: Described by name only for validation comparison; no URL cited in final reports.  
**OEIS A002863**: Described by name only for prime knot count reference (verified count: the total number of prime knots with crossing number ≤13); URL cited only for count verification.

### Data Completeness Validation

**Phase 1 Validation Scope**: Dataset completeness is validated against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration for prime knot counts at each crossing number within the study scope.. Crossing numbers 11-13 data is downloaded but NOT validated in Phase 1. This scope limitation is documented in docs/reproducibility/validation_scope.md.

**Expected Dataset Size**: 
- Total prime knots with crossing number ≤13: the documented total (OEIS sequence)
- Phase 1 validation benchmark: crossing numbers ≤10 only
- Data availability extends to ≤13; validated completeness limited to ≤10

### Data Fields Required

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| crossing_number | Integer | Knot Atlas | Tabulated; well-defined |
| braid_index | Integer | Knot Atlas | Requires algorithmic determination |
| hyperbolic_volume | Float | Knot Atlas | Zero/undefined for torus/satellite knots |
| alternating_classification | Boolean | Knot Atlas | Alternating vs. non-alternating |
| dt_code | String | Knot Atlas | Dowker-Thistlethwaite representation |
| braid_word | String | Knot Atlas | Braid representation |

### Data Quality Requirements

- **Missing Data Handling**: Records with missing invariant data are flagged with missing_invariant_flags (FR-011) rather than silently excluded
- **Ambiguous Classification**: Knots with ambiguous alternating/non-alternating classification are either excluded from stratified analysis or marked as "unclassifiable" (FR-012)
- **Volume Filtering**: Only prime knots with complete hyperbolic volume data are included in volume correlation analysis; excluded knots documented in docs/reproducibility/excluded_knots.md (FR-014)

## Methodology

### Phase 1: Data Download and Parsing

**Objective**: Download and parse knot data from Knot Atlas for all prime knots with crossing number ≤13.

**Implementation**:
- Retry logic with exponential backoff (initial 2s, multiplier 2, max [deferred]) per FR-010
- Partial results cached to disk after 3 consecutive failures
- Checksums (SHA-256) recorded for all downloaded files per Constitution Principle III

**Validation**: Dataset completeness validated against KnotInfo and HTW enumeration for crossing numbers ≤10 (SC-001).

### Phase 2: Invariant Computation

**Objective**: Compute additional invariants from available diagram representations.

**Algorithms**:
1. **Arc Index**: Birman-Menasco method (Birman & Menasco, 1988, *Mathematische Annalen* 281, pp. 127-138)
2. **Seifert Circle Count**: Seifert's algorithm on minimal crossing diagrams (Seifert, 1934, *Mathematische Annalen* 110, pp. 571-592); formula: s(D) per arXiv preprint https://arxiv.org/abs/math/0303273
3. **Bridge Number**: Schubert's bridge decomposition (Schubert, 1956, *Mathematische Zeitschrift* 61, pp. 245-288); 2-bridge knot reference per Wikipedia (https://en.wikipedia.org/wiki/2-bridge_knot)

**Representation Availability Definition**: A diagram representation is "available" if the corresponding field in the Knot Atlas record is non-null and non-empty (non-empty DT code OR non-empty braid word).

**Validation**: Algorithm implementation validated against KnotInfo reference values where coverage permits (SC-012). If coverage is insufficient, validation is skipped and limitation documented per FR-003.

**Invariant Dependency Note**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). Validation is exploratory correlation analysis, not independence testing.

### Phase 3: Exploratory Analysis

**Objective**: Perform exploratory data analysis to identify correlation patterns.

**Deliverables**:
- Scatter plots of crossing number vs. braid index, stratified by alternating/non-alternating classification (FR-004)
- Output: PNG files with minimum resolution 1200x900 pixels in data/plots/
- Summary statistics for all computed invariants

**Visualization Requirements**:
- Distinct stratification for alternating and non-alternating prime knots (SC-009)
- At least 3 additional invariants computed per knot where diagram representations are available (SC-010)

### Phase 4: Regression Modeling

**Objective**: Fit multiple regression models to test linear vs. non-linear relationships.

**Model Types**:
1. Linear regression
2. Polynomial regression (degree 2-3)
3. Logarithmic regression

**Multicollinearity Assessment**: Variance inflation factors (VIF) computed for all predictors given known inequality braid index ≤ crossing number. VIF > 5 is documented as exploratory context in final reports, NOT as a multicollinearity problem requiring correction (per FR-005 update). This reflects the fundamental mathematical dependency between predictors.

**Goodness-of-Fit Metrics**: R², AIC/BIC, MAE documented for each model (SC-002).

**Residual Analysis**: Specific knot families (pretzel knots, torus knots) that deviate significantly from global trend identified and documented (FR-005).

### Phase 5: Composite Complexity Score

**Objective**: Construct and validate composite complexity score.

**Formula**: Composite score = w₁ × crossing_number + w₂ × braid_index, with default equal weights (1:1 ratio) per FR-006.

**Theoretical Limitation**: No established mathematical basis in knot theory literature for linear combination of crossing number and braid index. Equal-weight default is exploratory and configurable via config/complexity_weights.yaml.

**Sensitivity Analysis Requirement**: Grid search across weight space (w₁, w₂ from 0 to 1 in 0.1 increments) to assess robustness of correlation findings to weight configuration (per methodology-351c4394 concern).

**Validation**: Correlation with hyperbolic volume computed on correlation sample using random stratified split by crossing number (FR-007). Both Pearson AND Spearman correlation coefficients reported per Constitution Principle VII and FR-008.

**Internal Correlation Assessment Note**: For finite census (High speeds at ≤13 crossings), stratified sample split is for model comparison only, NOT for statistical prediction validation. Terminology reflects internal correlation assessment, not out-of-sample prediction (per methodology-ba806f11 concern).

**Effect Size Reporting**: Cohen's d for group comparisons, r or r² for correlations documented alongside all p-values (FR-008).

### Phase 6: Statistical Testing

**Objective**: Assess significance of findings with appropriate statistical tests.

**Tests**:
- Pearson correlation (supplementary, assumes continuous normal distribution)
- Spearman correlation (primary, for discrete integer-valued invariants)
- ANOVA for group differences between alternating and non-alternating knots

**Assumption Checks**:
- Levene's test for equal variances before ANOVA
- Shapiro-Wilk test for normality before ANOVA
- If assumptions violated, robust alternatives used (Welch's ANOVA, Kruskal-Wallis) with deviation documented (FR-008)

**Reporting**: Both Pearson AND Spearman correlations reported where distribution assumptions cannot be verified a priori (Constitution Principle VII). Effect sizes (Cohen's d, r) documented alongside p-values (SC-011).

**Finite Population Note**: For complete enumeration of mathematical objects (prime knots ≤13), inferential claims (p-values, confidence intervals) are mathematically unsound. Results are framed as descriptive model fit (R², MAE) rather than statistical significance. P-values reported only with explicit 'exploratory/discovery' disclaimer (per scientific_soundness-8b6cb107 concern).

## Edge Case Handling

| Edge Case | Handling Strategy |
|-----------|-------------------|
| Knot Atlas unavailable/rate-limited | Exponential backoff retry (2s → [deferred] → [deferred] → [deferred] → [deferred]); partial results cached after 3 failures (FR-010); checksummed mirror fallback documented |
| Missing invariant data | Records flagged with missing_invariant_flags; logged in docs/reproducibility/uncomputable_invariants.md (FR-011) |
| Ambiguous alternating classification | Excluded from stratified analysis or marked "unclassifiable"; count logged (FR-012) |
| Crossing number ties | Tie-breaking rules applied: (1) prefer braid word over DT code; (2) prefer lexicographically first DT code (FR-013) |
| Hyperbolic volume zero/undefined | Records flagged and excluded from volume correlation analysis; count logged in docs/reproducibility/excluded_knots.md (FR-014) |

## Measurement Precision Estimates

**Crossing Number**: Tabulated values from Knot Atlas; computational uncertainty = 0 (exact integer).  
**Braid Index**: Algorithmic determination; computational uncertainty estimated within a small range of computational steps depending on algorithm convergence (per methodology-fabd1948 concern). Precision threshold: ±1-2 steps documented for correlation analysis uncertainty propagation.  
**Hyperbolic Volume**: Numerical approximation; uncertainty documented per source (typically within a sufficiently small threshold for hyperbolic knots).

All correlation analyses account for these precision estimates in uncertainty propagation where applicable.

## Reproducibility Requirements

All code and data transformations must be documented for reproducibility per Constitution Principle I and FR-009:

- **Random Seeds**: Pinned in code via config/seeds.yaml (default: 42)
- **Checksums**: SHA-256 for all data files recorded under data/checksums.txt
- **Derivation Notes**: Formula citations with page/section references, step-by-step transformation logic, all parameter values, justification for non-standard choices in docs/reproducibility/
- **Logs**: Timestamped logs capturing timestamp, operation, input_file, output_file, parameters, status, duration_ms, error information

## Limitations and Scope Boundaries

### Phase 1 Limitations

1. **Scope**: Limited to alternating/non-alternating dichotomy; multi-class exploration deferred to Phase 2+
2. **Validation**: Completeness validated only for crossing numbers ≤10; data available for ≤13 but not validated
3. **Composite Score**: Equal-weight default has no theoretical basis; configurable for future iterations with sensitivity analysis
4. **Invariant Dependencies**: Additional invariants have known mathematical constraints with crossing number and braid index; validation is exploratory correlation, not independence testing
5. **Discrete Data**: Pearson correlation assumes continuous normal distribution; interpretation limited by discrete integer-valued invariants
6. **URL Stability**: Knot Atlas URL not independently verified; checksummed mirror fallback available
7. **Selection Bias**: Analysis limited to hyperbolic knots only; invariants exist for all prime knots but generalizability limited to hyperbolic class (per methodology-ba91ea97 concern)
8. **Statistical Power**: Non-alternating knots are rare at low crossing numbers (e.g., only a few instances at c8 and c9); statistical power for ANOVA/t-tests may be insufficient (per methodology-d78e7ba3 concern)

### Assumptions

1. Users have stable internet connectivity for Knot Atlas download
2. Knot Atlas data format remains stable during analysis period
3. Statistical significance threshold of p < 0.05 is appropriate for exploratory analysis (with explicit disclaimer for finite census)
4. Random stratified split by crossing number ensures balanced representation across complexity levels
5. Prime knot enumeration follows OEIS A002863 (9,988 knots with crossing number ≤13)
6. Computational uncertainty for braid index (±1-2 steps) is negligible relative to observed effect sizes

## Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| SC-001 | Dataset completeness for ≤10 validated | KnotInfo/HTW enumeration comparison |
| SC-002 | 3 regression model types compared | R², AIC/BIC, MAE documented |
| SC-003 | Composite score correlation reported | Both Pearson AND Spearman coefficients |
| SC-004 | Reproducibility documentation complete | Checksums, seeds, derivation notes present |
| SC-005 | Retry logic verified | Simulated failures with exponential backoff |
| SC-009 | Exploratory plots generated | PNG files 1200x900+ in data/plots/ |
| SC-010 | 3+ additional invariants computed | Coverage documented for uncomputable records |
| SC-011 | ANOVA with effect sizes reported | Cohen's d alongside p-values |
| SC-012 | Algorithm validation documented | Pass/fail status in algorithm_validation.md |
| SC-013 | Scope validation documented | validation_scope.md with Phase 1 boundaries |