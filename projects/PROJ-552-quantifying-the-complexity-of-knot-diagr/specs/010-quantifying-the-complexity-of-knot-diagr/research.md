# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research investigates the relationship between topological invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) for prime knots. The analysis focuses on establishing measurement precision standards before correlation analysis proceeds, consistent with rigorous scientific measurement standards.

**Population Scope**: Analysis covers hyperbolic prime knots only (volume > 0). Conclusions about non-hyperbolic prime knots (torus/satellite) are explicitly NOT possible due to selection bias. Research question language will be revised to match actual population analyzed.

## Dataset Strategy

### Primary Data Source

| Requirement | Dataset | Verified URL | Loader | Notes |
|-------------|---------|--------------|--------|-------|
| FR-001: Knot Atlas data (crossing number, braid index, hyperbolic volume, alternating classification) | Knot Atlas | [deferred] | Web download from https://katlas.org | Reference-Validator Agent will verify before implementation per Constitution Principle II. Data access method (bulk download vs per-knot API) will be confirmed; if per-knot API required, will implement rate-limiting (1 request/second) and pagination. |
| SC-001: Prime knot enumeration reference | OEIS A002863 | [deferred] | https://oeis.org/A002863 | Reference for prime knot counts at each crossing number; used for completeness validation. Reference-Validator Agent will verify before implementation. |
| SC-013: Data quality validation | KnotInfo | [deferred] | nodename nor servname provided, or not known)"))] | Cross-check for invariant values; source independence assessment required. Canonical URL corrected from katlas.org wiki link. |
| FR-003: Additional invariants (Phase 2+) | KnotInfo | [deferred] | nodename nor servname provided, or not known)"))] | Reference values for algorithm validation; coverage ≥90% required for validation |

**Important**: All dataset URLs marked '[deferred]' will be verified by Reference-Validator Agent before implementation per Constitution Principle II (Verified Accuracy).

### Data Completeness Validation

- **Phase 1 Scope**: Validated completeness for prime knots with crossing number ≤10
- **Data Availability**: Prime knots up to crossing number ≤ a specified threshold (total count per OEIS A002863)
- **Validation Benchmark**: Compare against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration for prime knot counts at each crossing number
- **Null Threshold**: Required invariant fields (crossing number, braid index, hyperbolic volume) must have null percentage below an acceptable threshold in validated dataset subset

### Computational Task Ordering

Per the output contract rules, computational tasks MUST be ordered so that:
1. **Data download** occurs BEFORE any task that consumes it
2. **Model fitting** occurs BEFORE any task that evaluates them
3. **Figure generation** occurs BEFORE any task that includes them in the paper

**Pipeline Sequence**:
1. Download raw data from Knot Atlas (with retry logic)
2. Parse and clean dataset (create derived files, no in-place modification)
3. Compute additional invariants (Phase 2+ only)
4. Perform exploratory data analysis (scatter plots, stratified by alternating classification)
5. Fit regression models (linear, polynomial, logarithmic)
6. Conduct residual analysis (identify hyperbolic knot families deviating ≥2 standard deviations)
7. Generate reproducibility artifacts (checksums, logs, derivation notes)

## Measurement Precision Standards

### Core Invariants (Phase 1)

| Invariant | Source | Precision Standard | Validation Method |
|-----------|--------|-------------------|-------------------|
| Crossing Number | Knot Atlas (tabulated) | Well-defined, tabulated values | Cross-check against KnotInfo |
| Braid Index | Knot Atlas (tabulated) | Algorithmic determination required | Cross-check against KnotInfo; a high match threshold |

**Validation Independence Caveat**: Knot Atlas and KnotInfo both derive braid index data from the same underlying Hoste-Thistlethwaite-Weeks enumeration. Validation is cross-checking for consistency, NOT independent verification. This limitation will be explicitly stated in all final reports.

### Additional Invariants (Phase 2+)

| Invariant | Algorithm | Reference | Validation Threshold |
|-----------|-----------|-----------|---------------------|
| Arc Index | Birman-Menasco method | Birman & Menasco (1988), *Mathematische Annalen* 281, pp. 127-138 | ≥90% match with KnotInfo where coverage ≥90% |
| Seifert Circle Count | Seifert's algorithm on minimal crossing diagrams | arXiv:math/[identifier] | ≥90% match with KnotInfo where coverage ≥90% |
| Bridge Number | Schubert's bridge decomposition | 2-bridge knot, https://en.wikipedia.org/wiki/2-bridge_knot | ≥90% match with KnotInfo where coverage ≥90% |

**Note**: Additional invariants have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies must be acknowledged in all analysis. Validation is exploratory correlation analysis, NOT independence testing. Additional invariants cannot claim independent predictive value beyond crossing number and braid index.

## Statistical Methodology

### Correlation Analysis

- **Primary Method**: Spearman correlation (for discrete integer-valued invariants)
- **Supplementary Method**: Pearson correlation (for reporting completeness)
- **Effect Size**: Cohen's d for group comparisons; r or r² for correlations
- **Census Data Acknowledgment**: Since dataset represents complete census of prime knots ≤13 crossings, all statistical analysis is descriptive rather than inferential. Effect sizes are primary metrics; p-values documented for convention only and must not support inferential claims.

### Regression Models

| Model Type | Purpose | Selection Criteria |
|------------|---------|-------------------|
| Linear Regression | Baseline relationship | R², AIC/BIC, MAE |
| Polynomial Regression | Non-linear relationships | R², AIC/BIC, MAE |
| Logarithmic Regression | Non-linear relationships | R², AIC/BIC, MAE |

**Model Selection**: Based on goodness-of-fit metrics (R², AIC/BIC, MAE), NOT on statistical power. Statistical power is property of study design; model selection uses fit metrics.

### Residual Analysis

- **Threshold**: Identify hyperbolic knot families with residuals indicating significant deviation from global trend
- **Threshold Justification**: ≥2σ is standard outlier detection convention in regression analysis ([deferred] confidence for normal residuals)
- **Sensitivity Analysis**: Will test 1.5σ, 2σ, 2.5σ thresholds to ensure robustness of identified knot families
- **Scope**: Only hyperbolic knot families (torus and satellite knots filtered out per FR-012)
- **Documentation**: Specific knot identifiers, counts, and potential explanations in `docs/reproducibility/residual_analysis.md`
- **Exploratory Clarification**: Residual analysis is exploratory pattern identification, NOT model validation. Given census data and known mathematical constraints, residual patterns may reflect structural properties rather than 'unexplained variance'.

### Alternating vs Non-Alternating Comparison (SC-009)

The following descriptive comparison metrics will be computed and documented in `docs/reproducibility/alternating_comparison.md`:
1. Mean difference between alternating and non-alternating groups
2. Variance ratio between groups
3. Cohen's d effect size

## Documentation Deliverables

### Hyperbolic Volume Validation (FR-013, SC-014)

`docs/reproducibility/hyperbolic_volume_validation.md` will explicitly document:
1. Pass/fail status (≥90% match threshold)
2. Coverage percentage (percentage of knots with valid hyperbolic volume)
3. Source independence assessment (whether Knot Atlas and KnotInfo share underlying data)

### Data Quality Report (SC-013)

`docs/reproducibility/data_quality_report.md` will explicitly document all three metrics with their specific thresholds:
1. Null percentage <5% in required invariant fields
2. Format validation pass rate meets the target threshold
3. Zero duplicates in output dataset

### Validation Scope Document (SC-012)

`docs/reproducibility/validation_scope.md` will contain all three required content items:
1. Crossing number ≤10 vs ≤13 distinction with counts
2. Justification for Phase 1 scope limitation
3. Data availability vs validated completeness table

## Assumptions and Limitations

### Selection Bias

Filtering to knots with valid hyperbolic volume (volume > 0) means the research question about 'prime knots' cannot be fully answered—only 'hyperbolic prime knots' are analyzed. This selection bias fundamentally changes the scope of conclusions. All final reports MUST acknowledge this limitation explicitly.

### Mathematical Constraints

Braid index ≤ crossing number is a known mathematical constraint, not an empirical finding. This creates a definitional relationship that must be acknowledged in all analysis. Joint regression answers a variance partitioning question rather than independent explanatory power.

### Multicollinearity

Variance Inflation Factor (VIF) will be high by design due to mathematical constraint (braid index ≤ crossing number). Document VIF values as expected consequence of predictor structure; alternative methods (ridge regression, PCA) may be considered but are not mandatory given census data context.

### Data Source Independence

Assessment required: Do Knot Atlas and KnotInfo share underlying data sources or methodologies? If both derive from common sources (e.g., Hoste-Thistlethwaite-Weeks enumeration), validation is cross-checking for consistency, NOT independent verification. This must be explicitly stated in all final reports.

### Census Data Limitations

Since dataset represents complete census of prime knots ≤13 crossings (9988 total per OEIS A002863):
- All statistical analysis is descriptive rather than inferential
- Effect sizes are primary metrics
- p-values may be documented for reporting convention but MUST NOT support inferential claims
- This acknowledgment appears in a single consolidated section to avoid redundancy