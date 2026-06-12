# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research investigates the relationship between topological invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) for prime knots. The analysis is exploratory and descriptive, treating the dataset as a complete census rather than a sample from a larger population.

## Dataset Strategy

### Primary Data Source: Knot Atlas

**Requirement**: FR-001 specifies downloading knot data from Knot Atlas (https://katlas.org) including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤13.

**Verified Source Status**: NO verified source found for Knot Atlas dataset (per verified datasets block). The spec references Knot Atlas as the primary data source, but this dataset does not appear in the verified datasets block with a reachability/format-verified URL.

**Implementation Strategy**: 
- Download from https://katlas.org as specified in FR-001
- Document this limitation explicitly in docs/reproducibility/validation_scope.md
- If Knot Atlas becomes unavailable, implement retry logic with exponential backoff (per FR-008)
- Cache partial results to disk after 3 consecutive failures
- Flag records with missing invariant data rather than silent exclusion (per FR-009)

### Dataset Scope and Validation

**Crossing Number Range**: ≤13 for data availability, ≤10 for validated completeness (Phase 1 scope boundary)

**Total Prime Knots**: 9,988 prime knots with crossing number ≤13 (source: OEIS A002863, https://oeis.org/A002863)

**Validation Benchmark**: Dataset completeness validated against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration for prime knot counts at each crossing number within standard enumeration bounds.

**Data Quality Requirements** (per FR-002):
- Null percentage <5% in required invariant fields (crossing number, braid index, hyperbolic volume)
- Format validation passes for all records (valid DT code format, valid braid word format)
- Zero duplicates in output dataset

### Phase 1 vs Phase 2+ Data Scope

| Invariant | Phase 1 Status | Phase 2+ Status |
|-----------|---------------|-----------------|
| Crossing Number | Core (tabulated from Knot Atlas) | Core (tabulated from Knot Atlas) |
| Braid Index | Core (tabulated from Knot Atlas) | Core (tabulated from Knot Atlas) |
| Hyperbolic Volume | Core (tabulated from Knot Atlas) | Core (tabulated from Knot Atlas) |
| Arc Index | Deferred | Exploratory (Birman-Menasco algorithm) |
| Seifert Circle Count | Deferred | Exploratory (Seifert's algorithm) |
| Bridge Number | Deferred | Exploratory (Schubert's bridge decomposition) |

**Algorithm Validation** (per FR-003):
- Core invariants: Tabulated, not computed (algorithm validation not applicable)
- Additional invariants (Phase 2+): Validate against KnotInfo reference values with ≥90% match threshold
- If KnotInfo reference coverage <90%, validation skipped and limitation documented

### Selection Bias Acknowledgment

**Filtering to Hyperbolic Knots** (per FR-012):
- System MUST filter dataset to include only prime knots with hyperbolic volume >0
- Excludes torus and satellite knots where volume is zero or undefined
- Excluded records documented in docs/reproducibility/excluded_knots.md
- **Critical Limitation**: This filtering means conclusions apply only to hyperbolic prime knots, not all prime knots. All final reports MUST acknowledge this selection bias.

## Computational Task Ordering

Per the computational task ordering rule, phases must be ordered so:

1. **Data Download** → Before any task that consumes knot data
2. **Data Parsing & Cleaning** → Before exploratory analysis
3. **Exploratory Analysis** → Before regression model fitting
4. **Regression Model Fitting** → Before residual analysis
5. **Residual Analysis** → Before final report generation

**Phase Sequence**:
1. Download knot data from Knot Atlas (FR-001, FR-008)
2. Parse and clean dataset (FR-002)
3. Flag records with missing invariants (FR-009)
4. Filter to hyperbolic knots (FR-012)
5. Generate exploratory plots (FR-004)
6. Fit regression models (FR-005)
7. Perform residual analysis (FR-005, SC-011)
8. Document reproducibility artifacts (FR-007)

## Methodology

### Core Invariants

**Crossing Number**: Tabulated from Knot Atlas for all prime knots. Well-defined topological invariant representing minimum number of crossings in any diagram representation.

**Braid Index**: Tabulated from Knot Atlas. Represents minimum number of strands in any braid representation of the knot.

**Mathematical Constraint Acknowledgment**: Braid index ≤ crossing number is a known mathematical constraint, not an empirical finding. This creates a definitional relationship that must be acknowledged in all analysis. Joint regression answers a variance partitioning question rather than independent explanatory power.

### Regression Model Types (per FR-005)

| Model Type | Mathematical Form | Use Case |
|-----------|------------------|----------|
| Linear | Volume = β₀ + β₁×Crossing + β₂×Braid + ε | Baseline comparison |
| Polynomial | Volume = β₀ + β₁×Crossing + β₂×Braid + β₃×Crossing² + β₄×Braid² + ε | Capture non-linear relationships |
| Logarithmic | Volume = β₀ + β₁×log(Crossing) + β₂×log(Braid) + ε | Model diminishing returns |

**Model Selection Criteria** (per SC-002):
- R² (coefficient of determination)
- AIC (Akaike Information Criterion)
- BIC (Bayesian Information Criterion)
- MAE (Mean Absolute Error)

**Descriptive Interpretation**: R², AIC, and BIC are interpreted as descriptive fit statistics for finite census dataset rather than variance explained in any meaningful statistical sense.

### Statistical Tests (per FR-006)

| Test Type | Primary Method | Supplementary Method | Purpose |
|-----------|---------------|---------------------|---------|
| Correlation | Spearman (for discrete integer-valued invariants) | Pearson (for reporting completeness) | Assess significance of relationships |
| Group Comparison | Cohen's d, mean differences, variance ratios | ANOVA (not applicable for census data) | Compare alternating vs. non-alternating knots |

**Census Data Acknowledgment**: Since the dataset represents a complete census of prime knots ≤13 crossings rather than a sample from a larger population, all statistical analysis is descriptive rather than inferential. Effect sizes are the primary metrics of interest; p-values are documented for reporting convention only and must not support inferential claims.

**Discrete Data Acknowledgment**: Spearman is primary for discrete integer-valued invariants; Pearson is supplementary. Pearson assumes continuous data with normal distribution—interpretation limited by discrete nature.

### Residual Analysis (per SC-011)

**Requirement**: System MUST identify and document specific hyperbolic knot families (e.g., pretzel, hyperbolic non-alternating) that deviate significantly (≥2 standard deviations) from model predictions.

**Scope Limitation**: Since torus and satellite knots are filtered out per FR-012, residual analysis targets only hyperbolic knot families.

**Documentation**: Results documented in docs/reproducibility/residual_analysis.md with counts, specific knot identifiers, and potential explanations for deviation.

### Multicollinearity Assessment (per FR-005)

**Requirement**: System MUST compute variance inflation factor (VIF) for all joint regression models to assess multicollinearity between crossing number and braid index predictors.

**Expected Outcome**: VIF will be high by design due to mathematical constraint (braid index ≤ crossing number). Document VIF values as expected consequence of predictor structure.

**Documentation**: Multicollinearity assessment results documented in docs/reproducibility/multicollinearity_assessment.md.

## Edge Case Handling (per User Story 4)

| Edge Case | Handling Strategy | Documentation |
|-----------|------------------|---------------|
| Knot Atlas unavailable | Retry logic with exponential backoff (initial=1s, max=32s, multiplier=2); partial results cached after 3 failures | docs/reproducibility/validation_scope.md |
| Missing invariant data | Flag with missing_invariant_flags rather than silent exclusion | docs/reproducibility/data_quality_report.md |
| Ambiguous alternating classification | Exclude from stratified analysis or mark as "unclassifiable" | docs/reproducibility/validation_status.md |
| Diagram representation ties | Apply documented tie-breaking rules consistently | docs/reproducibility/tie_breaking_rules.md |
| Hyperbolic volume = 0 | Filter out, document in excluded_knots.md | docs/reproducibility/excluded_knots.md |

**Tie-Breaking Rules** (per FR-011):
1. When multiple diagram representations exist, prefer braid word representation over Dowker-Thistlethwaite code
2. When multiple Dowker-Thistlethwaite codes exist, prefer lexicographically first code

**Validation**: Validation script included in docs/reproducibility/ that automates consistency check; must return exit code 0 on success.

## Reproducibility Requirements (per FR-007)

### Random Seeds

- All stochastic operations MUST pin random seeds in code
- Seed values documented in docs/reproducibility/random_seeds.md

### Checksums

- SHA-256 checksums recorded for all data files under data/ directory
- Checksum documentation in docs/reproducibility/

### Derivation Notes

- All transformations documented with formula citations (page/section references)
- Step-by-step transformation logic with intermediate values
- All parameter values used
- Justification for non-standard choices

### Logs

- Timestamped logs with: timestamp, operation, input_file, output_file, parameters, status, duration_ms, error information
- Stored in docs/reproducibility/

## Assumptions

1. **Computational Constraints**: Analysis pipeline executes within single GitHub-Actions-class job; any stage projected to exceed budget partitioned into resumable sub-steps
2. **Internet Connectivity**: Users have stable internet for downloading data from Knot Atlas
3. **Data Format Stability**: Knot Atlas data format remains stable during analysis period
4. **Phase 1 Scope Boundary**: Phase 1 limited to core invariants and validated crossing number ≤10 data
5. **Hyperbolic Volume Availability**: Not all prime knots have computable hyperbolic volume; filtering to knots with valid volume acknowledged as selection bias
6. **Multicollinearity Acknowledgment**: Crossing number and braid index not fully independent predictors (braid index ≤ crossing number)
7. **Census Data Statistical Interpretation**: All statistical analysis descriptive rather than inferential
