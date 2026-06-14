# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research documents the methodological foundations, data sources, and analytical approach for quantifying knot diagram complexity through correlation analysis of crossing number, braid index, and hyperbolic volume.

## Dataset Strategy

| Dataset | Description | Source / Loader | Coverage | Validation Status |
|---------|-------------|-----------------|----------|-------------------|
| Knot Atlas | Prime knots with crossing number ≤ 13, including crossing number, braid index, hyperbolic volume, alternating classification | Knot Atlas — loaded via CSV/JSON export with programmatic fetching; URL verified at runtime | All prime knots ≤ 13 crossings (9988 total per OEIS A002863) | Phase 1 validation benchmark for ≤ 10 crossings; 11-13 crossings exploratory only |
| KnotInfo | Reference values for hyperbolic volume consistency cross-check | KnotInfo — loaded via web scraping with rate limiting; URL verified at runtime | Subset of knots where reference data available | ≥ 90% match threshold required; if coverage < 90%, cross-check skipped per FR-013 |
| OEIS A002863 | Prime knot enumeration counts by crossing number | OEIS — loaded via API; URL verified at runtime | Total prime knots at each crossing number | Used for dataset completeness validation (SC-001) |

**Note**: Datasets will be loaded via programmatic methods (Knot Atlas CSV/JSON export, KnotInfo web scraping, OEIS API) with URLs verified at runtime. The verified datasets block will be updated once runtime verification confirms URL stability and format.

## Phase 1 Scope Definition

**Data Availability**: All prime knots with crossing number ≤ 13 (9988 total knots, source: OEIS A002863)

**Validated Completeness**: Crossing number ≤ 10 crossings only (Phase 1 benchmark)

**Exploratory Data**: Crossing number 11-13 crossings (downloaded but not validated in Phase 1)

**Justification**: The large number of prime knots at higher crossing numbers makes full validation impractical within Phase 1 timeline. Validation staging preserves research scope while enabling practical execution.

## Methodological Adjustments from Original Idea

### Census Data Acknowledgment

The dataset represents a complete census of all prime knots ≤ 13 crossings rather than a sample from a larger population. This has the following implications:

| Original Method | Census Data Adjustment | Rationale |
|-----------------|----------------------|-----------|
| 80/20 train/test split | Not applicable | Complete census has no held-out samples; all data used for descriptive analysis |
| ANOVA for group comparisons | Descriptive statistics (mean differences, variance ratios, Cohen's d) | ANOVA tests population sample differences; census data has exact population parameters |
| Cross-validated R-squared | Goodness-of-fit metrics (R², AIC/BIC, MAE) | Cross-validation estimates predictive performance on held-out samples; not applicable for census |
| p-values for statistical claims | Effect sizes only (Cohen's d, r, r²) | Complete enumeration makes p-values inapplicable; effect sizes are primary metrics per Constitution Principle VII amendment |

### Mathematical Constraint Acknowledgment

**Braid Index ≤ Crossing Number**: This is a known mathematical inequality, not an empirical finding. It creates a definitional relationship that must be acknowledged in all analysis.

**Implications for Regression**:
- Joint regression coefficients represent variance partitioning within the finite census dataset, NOT independent explanatory power
- Coefficient estimates are descriptive associations within the census, not interpretable as independent effects
- Multicollinearity (VIF) will be high by design due to mathematical constraint; document VIF values as expected consequence of predictor structure
- All final reports MUST explicitly state this limitation to prevent misinterpretation

### Hyperbolic Volume Selection Bias

**Filtering**: Dataset filtered to hyperbolic prime knots only (volume > 0), excluding torus and satellite knots

**Implications**:
- Research question about "prime knots" cannot be fully answered — only "hyperbolic prime knots" are analyzed
- This selection bias fundamentally changes the scope of conclusions
- All final reports MUST acknowledge this limitation per FR-012

**Invariant Type Distinction**: Combinatorial invariants (crossing number, braid index) and geometric invariants (hyperbolic volume) measure fundamentally different properties. The explanatory relationship may be weak or non-existent by mathematical definition, not empirical finding.

## Statistical Methodology

### Correlation Analysis

| Method | Primary Use | Justification |
|--------|-------------|---------------|
| Spearman correlation | Primary for discrete integer-valued invariants | Crossing number and braid index are small integers; discrete data limitations acknowledged |
| Pearson correlation | Supplementary for reporting completeness | Assumes continuous data with normal distribution; interpretation limited by discrete nature |

### Effect Size Measures (Census Data)

| Comparison Type | Effect Size Metric | Reporting Requirement |
|-----------------|-------------------|----------------------|
| Correlation | r or r² | Report for all correlations |
| Group comparison (alternating vs. non-alternating) | Cohen's d | Report mean differences, variance ratios, AND Cohen's d |
| Model fit | R², AIC, BIC | Descriptive fit statistics for finite census dataset |

### Multicollinearity Assessment

- Compute Variance Inflation Factor (VIF) for all joint regression models
- Document VIF values as expected consequence of predictor structure (braid index ≤ crossing number)
- Alternative methods (ridge regression, PCA) may be considered but not mandatory given census data context
- Results documented in `docs/reproducibility/multicollinearity_assessment.md`

## Data Quality Requirements

### FR-002 Data Quality Definition

| Metric | Threshold | Flag Type |
|--------|-----------|-----------|
| Null percentage per field (crossing number, braid index, hyperbolic volume) | ≤ 5% | data_quality_flags |
| Format validation pass rate (DT code, braid word) | ≥ 99% | data_quality_flags |
| Duplicate records | 0 | data_quality_flags |

### Flag Distinction

| Flag Type | Trigger Condition |
|-----------|-------------------|
| data_quality_flags | General data quality issues (null values, format failures, duplicates) |
| missing_invariant_flags | Invariants cannot be computed from available diagram representations (per FR-003) |

Records may have both flag types if multiple conditions apply.

## Reproducibility Requirements (FR-007)

### Required Artifacts

| Artifact | Location | Content |
|----------|----------|---------|
| SHA-256 checksums | `data/checksums.txt` | All data files in `data/` directory |
| Derivation notes | `data/reproducibility/derivation_notes/` | Formula citations with page/section references, step-by-step transformation logic, intermediate values, parameter values, justification for non-standard choices |
| Timestamped logs | `data/reproducibility/logs/` | timestamp, operation, input_file, output_file, parameters, status, duration_ms, error information |
| Random seeds | `data/reproducibility/random_seeds.md` | All seed values used in code |

### Validation Scripts

- Tie-breaking validation script (SC-007): Verifies documented tie-breaking rules applied consistently
- Must return success exit code on consistency check
- Failure logged and reported in `docs/reproducibility/validation_status.md`

## Edge Case Handling

### API Unavailability (FR-008)

| Condition | Action |
|-----------|--------|
| Knot Atlas unavailable | Exponential backoff retry sequence (configurable initial delay, maximum duration, constant multiplier) |
| Multiple consecutive failures | Partial results cached to disk after threshold |
| Rate limiting | Respect rate limit headers; exponential backoff |

### Missing Invariant Data (FR-009)

| Condition | Action |
|-----------|--------|
| Invariant not computable from available diagram representations | Record flagged with missing_invariant_flags (not silently excluded) |
| No diagram representation available | Record retained in dataset with documentation; excluded from invariant computation |

### Ambiguous Classification (FR-010)

| Condition | Action |
|-----------|--------|
| Alternating/non-alternating classification ambiguous or missing | Exclude from stratified analysis (with count logged) OR mark as "unclassifiable" |

### Diagram Representation Ties (FR-011)

| Condition | Tie-Breaking Rule |
|-----------|-------------------|
| Multiple diagram representations | Prefer braid word over Dowker-Thistlethwaite code |
| Multiple DT codes | Prefer lexicographically first code |

Validation script required (SC-007) to confirm consistency across all records.

### Hyperbolic Volume Filtering (FR-012)

| Condition | Action |
|-----------|--------|
| Hyperbolic volume = 0 or undefined (torus/satellite knots) | Filtered from volume prediction analysis; excluded records documented in `docs/reproducibility/excluded_knots.md` |

## Data Consistency Cross-Check (FR-013)

| Aspect | Requirement |
|--------|-------------|
| Reference | KnotInfo (https://knotinfo.org) — loaded via web scraping with rate limiting |
| Threshold | ≥ 90% match against KnotInfo reference values where both available |
| Coverage | ≥ 90% coverage required; if < 90%, cross-check skipped and limitation documented |
| Source Independence Qualification | When Knot Atlas and KnotInfo share underlying data sources, high match rate reflects data lineage NOT independent accuracy confirmation. All final reports MUST explicitly state this limitation. Validation target (hyperbolic volume) and predictors (crossing number, braid index) are mathematically independent variables; shared sources imply dependent measurements, not dependent variables. |

**Important**: When databases share underlying sources, high match rate reflects data lineage, not independent accuracy confirmation. All final reports MUST explicitly state this limitation.

## References

- **Birman, J. S., & Menasco, W. W.** (1988). "An Algorithm for the Arc Index of a Knot". *Mathematische Annalen*, 281, pp. 127-138.
- **Ohyama, Y.** (1993). "On the braid index of alternating knots". *Journal of Knot Theory and Its Ramifications*, 2(2), pp. 203-211.
- **OEIS A002863**: Number of prime knots with n crossings. Source: https://oeis.org/A002863
- **arXiv math/0303273**: Birman-Menasco algorithm for arc index; Seifert's algorithm for Seifert circle count (Seifert circle count via Seifert's algorithm = s(D), source: https://arxiv.org/abs/math/0303273)
- **Schubert, H.** (1954). "Die eindeutige Zerlegbarkeit eines Knoten in Primknoten". *Sitzungsberichte der sächsischen Akademie der Wissenschaften zu Leipzig*, 100(3), pp. 57-104. (Primary source for Schubert's decomposition / bridge number)
- **2-bridge knot**: Schubert's decomposition for bridge number. Source: https://en.wikipedia.org/wiki/2-bridge_knot (secondary reference; primary literature is Schubert 1954)

**Citation Resolution Note**: The source specification (spec.md FR-003) contains unresolved citation placeholders. This research document uses the resolved citations: arXiv:math/0303273 for Seifert's algorithm and Birman-Menasco, Schubert 1954 as primary source for bridge number (with Wikipedia as secondary reference only).