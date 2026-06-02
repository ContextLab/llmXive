# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31

## Research Question (Phase 1)

To what extent do crossing number and braid index jointly predict the hyperbolic volume of prime knots, and does this relationship differ systematically between alternating and non-alternating classes?

## Background and Motivation

Knot theory provides a rich framework for understanding geometric complexity through topological invariants. The crossing number (minimum number of crossings in any diagram) and braid index (minimum number of strands in any braid representation) are both classical invariants that capture different facets of a knot's geometry. While individually well-studied, their joint predictive relationship with hyperbolic volume—a geometric measure of the knot complement's complexity—remains underexplored.

This research formalizes the intuition that these invariants together may form a richer descriptor of knot complexity than either alone. As noted in related work, inequalities relating crossing number and braid index have been established (e.g., braid index ≤ crossing number for most knots), suggesting potential multicollinearity that must be assessed in regression modeling.

## Dataset Strategy

### Primary Data Source: Knot Atlas

**Dataset Name**: Knot Atlas prime knot database  
**Scope**: All prime knots with crossing number ≤13  
**Fields Required**: crossing number, braid index, hyperbolic volume, alternating/non-alternating classification, diagram representations (Dowker-Thistlethwaite codes, braid words)  
**Access Method**: HTTP download from Knot Atlas website with retry logic (FR-001, FR-010)  
**Validation**: Cross-reference against KnotInfo and Hoste-Thistlethwaita-Weeks enumeration for prime knot counts at each crossing number ≤10 (SC-001)

**Note**: The Knot Atlas URL is not in the verified datasets block. Per research.md rules, I describe the dataset by name but do NOT fabricate a URL. The implementation will use the canonical Knot Atlas source (https://katlas.org) as specified in FR-001.

### Verification Against Reference Data

**Dataset Name**: KnotInfo reference values  
**Purpose**: Algorithm validation for computed invariants (arc index, Seifert circle count, bridge number)  
**Validation Threshold**: ≥95% match with reference values where reference data exists (SC-012)  
**Coverage Constraint**: If KnotInfo reference coverage <10% of dataset, validation is skipped and limitation documented (FR-003)

**Note**: The KnotInfo URL is not in the verified datasets block. I describe the dataset by name but do NOT fabricate a URL.

### Prime Knot Enumeration Reference

**Source**: OEIS A002863 (https://oeis.org/A002863)  
**Verified Value**: 9,988 prime knots at crossing number 13  
**Purpose**: Validate dataset completeness for crossing number 13 enumeration

### Dataset Completeness Validation Scope

| Crossing Number | Prime Knot Count | Validation Status (Phase 1) |
|-----------------|------------------|-----------------------------|
| ≤10 | ~1,600 (cumulative) | **Validated** (≥95% completeness benchmark) |
| 11-13 | ~9,000+ (cumulative) | **Data collected, not validated** (exploratory only) |

**Rationale**: With 9,988 prime knots at crossing number 13 alone, full validation across all crossing numbers ≤13 is computationally impractical for Phase 1 exploratory analysis. This is a deliberate scope decision (see spec.md Scope Boundaries).

### Data Quality Requirements

- **Required Fields Completeness**: ≥95% of records have crossing number, braid index, and hyperbolic volume values present (SC-001)
- **Invariant Computability**: ≥99% of knots with computable invariants have all invariants populated (SC-006)
- **Hyperbolic Volume Completeness**: ≥95% for prime knots with crossing number ≤13 (SC-014)
- **Missing Data Handling**: Records flagged with `missing_invariant_flags` rather than silently excluded (FR-011)

### Known Dataset Limitations

1. **Hyperbolic Volume Availability**: Not all prime knots have computable hyperbolic volume (torus and satellite knots have volume zero or undefined). These will be filtered for volume prediction analysis with excluded records documented in `docs/reproducibility/excluded_knots.md` (FR-014).

2. **Alternating Classification Ambiguity**: Some knots may have ambiguous or missing alternating/non-alternating classification. These will be either excluded from stratified analysis (with count logged) or marked as "unclassifiable" (FR-012, SC-007).

3. **Diagram Representation Availability**: Not all knots will have available diagram representations (DT codes or braid words) for invariant computation. Records without available representations will be flagged in `docs/reproducibility/uncomputable_invariants.md` (FR-003).

## Computational Methods

### Invariant Computation Algorithms

| Invariant | Algorithm | Reference | Validation Method |
|-----------|-----------|-----------|-------------------|
| Arc Index | Birman-Menasco method | Birman & Menasco, 1988, *Mathematische Annalen* 281, pp. 127-138 | Compare against KnotInfo where available |
| Seifert Circle Count | Seifert's algorithm on minimal crossing diagrams | Seifert, 1934, *Mathematische Annalen* 110, pp. 571-592 | Compare against KnotInfo where available |
| Bridge Number | Schubert's bridge decomposition | Schubert, 1956, *Über eine numerische Knoteninvariante*, *Mathematische Zeitschrift* 61, pp. 245-288 | Compare against KnotInfo where available |

**Algorithm Validation Requirement**: System MUST validate algorithm implementation correctness against available reference values from KnotInfo for the dataset subset. If KnotInfo reference coverage <10% of the dataset, validation against KnotInfo MUST be skipped and the limitation MUST be documented in `docs/reproducibility/algorithm_validation.md` with pass/fail status per invariant and per algorithm, noting the coverage constraint and the skip rationale. Pass/fail threshold: ≥95% match with reference values where reference data exists (FR-003, SC-012).

### Regression Modeling Approach

| Model Type | Purpose | Metrics |
|------------|---------|---------|
| Linear Regression | Baseline linear relationship | R², AIC/BIC, MAE, VIF |
| Polynomial Regression | Test non-linear relationships | R², AIC/BIC, MAE, VIF |
| Logarithmic Regression | Test logarithmic scaling | R², AIC/BIC, MAE, VIF |

**Multicollinearity Assessment**: System MUST compute variance inflation factors (VIF) for all predictors. If VIF > 5 for any predictor, this MUST be flagged in final reports as a potential multicollinearity issue affecting coefficient interpretation (FR-005).

**Residual Analysis**: System MUST identify and document specific knot families (e.g., pretzel knots, torus knots) that deviate significantly from model predictions based on residual analysis (FR-005).

### Statistical Testing Framework

| Test | Purpose | Assumption Checks | Robust Alternatives |
|------|---------|-------------------|---------------------|
| Pearson Correlation | Linear association | Normality (Shapiro-Wilk) | Spearman (primary) |
| Spearman Correlation | Monotonic association | None required | N/A |
| ANOVA | Group differences (alternating vs. non-alternating) | Equal variances (Levene's), Normality (Shapiro-Wilk) | Welch's ANOVA, Kruskal-Wallis |

**Mandatory Dual Correlation**: Per Constitution Principle VII, BOTH Pearson AND Spearman correlations MUST be reported when distribution assumptions cannot be verified a priori—this is a mandatory requirement, not conditional (FR-008).

**ANOVA Assumption Checks**: Before ANOVA testing, system MUST perform Levene's test for equal variances and Shapiro-Wilk test for normality. If assumptions are violated, system MUST use robust alternatives (e.g., Welch's ANOVA, Kruskal-Wallis test) and document the deviation from standard ANOVA (FR-008).

**Effect Size Reporting**: All statistical tests MUST report effect size measures (Cohen's d for group comparisons, r or r² for correlations) alongside all p-values (FR-008, SC-011).

## Composite Complexity Score

### Construction

The composite complexity score is constructed as a weighted combination of crossing number and braid index:

```
Complexity Score = w₁ × Crossing Number + w₂ × Braid Index
```

**Default Configuration**: Equal weights (w₁ = w₂ = 0.5, 1:1 ratio)  
**Justification**: No established mathematical basis exists in knot theory literature for linear combination of crossing number and braid index. The equal-weight default is exploratory and configurable (FR-006).  
**Configuration**: Weights configurable via `config/complexity_weights.yaml` (FR-006)

### Validation Approach

- **Validation Sample**: 20% random stratified split by crossing number (Assumptions)
- **Metrics**: Pearson and Spearman correlation with hyperbolic volume, effect sizes (r, r²)
- **Reporting**: Correlation coefficients and effect sizes reported regardless of magnitude; analysis is considered complete and valid whether correlation values are strong or weak (FR-007, SC-003)

**Terminology Consistency**: "Exploratory validation sample" is used consistently throughout the spec (not "held-out test set") to acknowledge this is correlation analysis, not ML prediction validation (FR-007).

## Phase 1 Scope Limitations

### Crossing Number Validation Scope

- **Data Collection**: All prime knots with crossing number ≤13
- **Validation Benchmark**: Crossing numbers ≤10 only (≥95% completeness on required invariant fields)
- **Phase 1 Conclusions**: Explicitly limited to validated crossing number ≤10 data
- **Exploratory Data**: Crossing numbers 11-13 data is downloaded but marked as exploratory/unvalidated in final reports

**Documentation**: Dataset completeness and scope validation documented in `docs/reproducibility/validation_scope.md` (SC-013).

### Alternating/Non-Alternating Dichotomy

- **Phase 1 Focus**: Alternating/non-alternating dichotomy only
- **Multi-Class Exploration**: Torus, satellite, hyperbolic classes deferred to Phase 2+
- **Rationale**: Foundational analysis on dichotomy as tractable first step (Scope Boundaries)

### Precision Standards

Consistent with rigorous scientific measurement standards (per marie-curie-simulated reviewer feedback), the analysis must establish precision thresholds for all computed invariants before correlation analysis proceeds. This includes documenting computational uncertainty for braid index (which requires algorithmic determination) versus crossing number (which is tabulated). This standard is implemented through FR-003 algorithm validation and SC-012 validation against reference values.

## Reproducibility Requirements

### Random Seed Pinning

All stochastic operations MUST pin random seeds in code:
- Data splitting: `random.seed(42)` (configurable)
- Any Monte Carlo operations: documented seed values

### Checksums

SHA-256 checksums for all files under `data/` recorded in `data/checksums.txt` and documented in `docs/reproducibility/checksums.md` (FR-009, Constitution Principle III).

### Derivation Notes

All data transformations documented in `docs/reproducibility/derivation_notes.md` including:
- Formula citations with page/section references
- Step-by-step transformation logic with intermediate values
- All parameter values used
- Justification for any non-standard choices (FR-009)

### Execution Logs

Timestamped logs stored in `docs/reproducibility/logs/` capturing:
- `timestamp`, `operation`, `input_file`, `output_file`, `parameters`, `status`, `duration_ms`, error information (FR-009)

### Tie-Breaking Rules

Documented in `docs/reproducibility/tie_breaking_rules.md`:
1. When multiple diagram representations exist for a knot, prefer braid word representation over Dowker-Thistlethwaite code
2. When multiple Dowker-Thistlethwaite codes exist, prefer lexicographically first code

Validation script included in `docs/reproducibility/` that automates consistency check (FR-013, SC-008).

## Related Work

- **Crossing Number and Braid Index Inequalities**: Establishes foundational inequalities relating crossing number and braid index for classical links (10.1142/S0218216519500020 - NO verified source found, do NOT cite URL per research.md rules)
- **Virtual Links Extension**: Extends Ohyama's inequality to virtual links and generalizes the relationship framework (NO verified source found, do NOT cite URL)
- **Algebraic Crossing Number**: Investigates the conjecture that algebraic crossing number is uniquely determined in minimal braid representation (NO verified source found, do NOT cite URL)
- **Prime Knots with Crossing Number 13**: Provides empirical data on 9,988 prime knots with crossing number 13, establishing a testable dataset for correlation analysis (https://arxiv.org/abs/2402.02717)
- **Crossing Number and Bridge Number**: Relates crossing number to bridge number, offering a third invariant for potential composite measures (NO verified source found, do NOT cite URL)
- **Braid Index Upper Bounds**: Presents upper bounds for braid index in terms of crossing number using planar graph embeddings (https://arxiv.org/abs/1806.09719)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Knot Atlas API unavailability | Medium | High | Retry logic with exponential backoff (1s → 2s → 4s → ... → 60s max); partial results cached after 3 consecutive failures (FR-010, SC-005) |
| Missing invariant data | Medium | Medium | Flag records with `missing_invariant_flags` rather than silent exclusion (FR-011); document in `docs/reproducibility/uncomputable_invariants.md` |
| Ambiguous alternating classification | Low | Medium | Exclude from stratified analysis or mark as "unclassifiable" (FR-012, SC-007) |
| Multicollinearity (braid index ≤ crossing number) | High | Medium | Compute VIF for all predictors; flag if VIF > 5 (FR-005) |
| ANOVA assumption violations | Medium | Medium | Perform Levene's and Shapiro-Wilk tests; use robust alternatives if violated (FR-008) |

## Success Criteria Summary

| Criterion | Target | Verification Method |
|-----------|--------|---------------------|
| SC-001: Dataset completeness (≤10) | ≥95% completeness on required invariant fields | Validation against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration |
| SC-002: Regression models | ≥3 model types with documented metrics | Compare R², AIC/BIC, MAE for linear, polynomial, logarithmic |
| SC-003: Composite score validation | Correlation coefficients and effect sizes reported | Pearson and Spearman correlations on exploratory validation sample |
| SC-004: Reproducibility documentation | Complete derivation notes, checksums, logs | Verify all artifacts present in `docs/reproducibility/` |
| SC-005: Retry logic verification | Exponential backoff executed on simulated failures | Unit test with simulated API failures |
| SC-006: Invariant computability | ≥99% of computable invariants populated | Check `docs/reproducibility/uncomputable_invariants.md` |
| SC-007: Classification handling | No silent exclusions; count logged | Verify all ambiguous records flagged or excluded with documentation |
| SC-008: Tie-breaking consistency | 100% consistency across invariant computations | Run validation script in `docs/reproducibility/` |
| SC-009: Exploratory plots | PNG files ≥1200x900 pixels in `data/plots/` | Verify file existence and resolution |
| SC-010: Additional invariants | ≥3 invariants computed per knot where available | Check invariant coverage in dataset |
| SC-011: Statistical tests | ANOVA with effect sizes reported | Verify effect sizes in statistical test output |
| SC-012: Algorithm validation | ≥95% match with reference values where coverage ≥10% | Check `docs/reproducibility/algorithm_validation.md` |
| SC-013: Scope validation | Phase 1 scope boundaries documented | Verify `docs/reproducibility/validation_scope.md` |
| SC-014: Volume data completeness | ≥95% for prime knots with crossing number ≤13 | Check `docs/reproducibility/excluded_knots.md` |
