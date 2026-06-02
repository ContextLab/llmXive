# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research investigates the joint predictive relationship between crossing number and braid index for hyperbolic volume in prime knots, with systematic comparison between alternating and non-alternating classes. Phase 1 focuses on the alternating/non-alternating dichotomy, with validation benchmarking for crossing numbers ≤10.

## Dataset Strategy

### Primary Data Sources (Verified)

| Dataset | Description | Source | Verification Status |
|---------|-------------|--------|---------------------|
| Knot Atlas | Prime knot invariants including crossing number, braid index, hyperbolic volume, alternating classification | https://katlas.org | ✅ Verified (primary source per FR-001) |
| Hoste-Thistlethwaite-Weeks tables | Supplementary tabulated invariants for prime knots up to crossing 13 | https://arxiv.org/abs/2402.02717 | ✅ Verified (fallback source) |
| OEIS A002863 | Prime knot enumeration counts | https://oeis.org/A002863 | ✅ Verified (9,988 prime knots at crossing number 13) |
| KnotInfo | Reference values for algorithm validation (e.g., braid index tables) | NO verified source found | ⚠️ Contingency only; validation skipped if coverage <10% |

### Contingency Data Sources

If primary sources are unavailable, the pipeline falls back to:
- **Hoste-Thistlethwaite-Weeks tables (arXiv 2402.02717)**: Contains tabulated invariants for prime knots up to crossing 13, ensuring data availability even if Knot Atlas is unreachable.
- **Data format**: Parquet files with checksums recorded per Constitution Principle III.

### Data Collection Strategy

**Download Pipeline**: Implement exponential backoff retry logic (initial 1 s, max 60 s, multiplier 2) per FR-010. After 3 consecutive failures, cache partial results to disk.

**Completeness Validation**: Phase 1 validation focuses on crossing numbers ≤10 (≥99% completeness on required invariant fields, per SC-006). Data collection covers all prime knots with crossing number ≤13, but full validation for 11-13 is deferred per scope boundaries.

**Scope Limitation Acknowledgment**: With 9,988 prime knots at crossing number 13 (OEIS A002863), full validation is computationally impractical for Phase 1. All Phase 1 conclusions are explicitly limited to the validated ≤10 subset. Data for 11-13 remains for exploratory analysis only.

**KnotInfo Runtime Validation**: Coverage assessment for KnotInfo reference values occurs at runtime. If coverage <10%, validation is skipped with a logged warning per FR-003.

### Data Quality Requirements

- **Required Fields**: `crossing_number`, `braid_index`, `hyperbolic_volume`, `alternating_classification`.
- **Acceptance Threshold**: **≥99%** of records in the ≤10 subset must have all required fields populated (SC-006).
- **Missing Data Handling**: Flag records with `missing_invariant_flags` rather than silent exclusion per FR-011.
- **Classification Ambiguity**: Exclude from stratified analysis OR mark as "unclassifiable" per FR-012.

## Background Literature

### Foundational Inequalities

- Crossing number and braid index relationships established in classical knot theory literature (10.1142/S0218216519500020 — NO verified source found).
- Ohyama's inequality extended to virtual links generalizes the relationship framework.
- Algebraic crossing number conjecture: uniquely determined in minimal braid representation (2006).

### Empirical Data Sources

- Minimal grid diagrams for prime knots with crossing number 13 and arc index 13 (2024) — Provides empirical data on 9,988 prime knots at crossing number 13.
- Bridging number relationships to crossing number offer a third invariant for composite measures.
- Bisected vertex leveling of plane graphs (2018) — Presents upper bounds for braid index in terms of crossing number.

### Measurement Precision Standard

Consistent with rigorous scientific measurement standards (as emphasized in reviewer feedback from marie-curie-simulated), the analysis must establish precision thresholds for all computed invariants before correlation analysis proceeds. This includes documenting computational uncertainty for braid index (algorithmic determination) versus crossing number (tabulated).

## Research Methodology

### Phase 1 Analytical Pipeline

1. **Data Acquisition**: Download knot data from Knot Atlas with retry logic and partial caching; fallback to Hoste-Thistlethwaite-Weeks tables if needed.
2. **Invariant Computation**: Retrieve tabulated invariants where available; compute `arc_index`, `seifert_circle_count`, and `bridge_number` **only** for knots lacking these values, using established algorithms (Birman-Menasco, Seifert's algorithm, Schubert's decomposition). Flag any computation failures.
3. **Exploratory Analysis**: Generate scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification.
4. **Regression Modeling**:
 - Fit **separate** linear, polynomial, and logarithmic models for alternating and non-alternating knots.
 - Optionally fit a combined model that includes `alternating_classification` as a categorical predictor with interaction terms.
 - Primary predictors are `crossing_number` and `braid_index`; additional invariants are **not** added to avoid multicollinearity.
 - Compute VIF scores; flag any predictor with VIF > 5.
5. **Composite Score Construction**: Create a weighted combination of crossing number and braid index (default 0.5: 0.5). Report Pearson and Spearman correlations with hyperbolic volume **descriptively**; do **not** treat this as validation of the regression models.
6. **Exploratory Correlation Subset**: Randomly stratify 20% of the validated ≤10 dataset (fixed seed) to assess robustness of correlation estimates. This subset is **exploratory correlation analysis**, NOT true out-of-sample validation.
7. **Residual Analysis**: Identify knot families (pretzel, torus) that deviate significantly from global trends; report as outliers.

### Statistical Testing Protocol

- **Correlation Analysis**: Report BOTH Pearson AND Spearman coefficients (Constitution Principle VII). Include effect sizes (r, Cohen's d) and 95% confidence intervals.
- **Group Comparisons**: ANOVA for alternating vs. non-alternating with effect sizes (Cohen's d). Perform Levene's test for equal variances and Shapiro-Wilk for normality; fallback to Welch's ANOVA or Kruskal-Wallis if assumptions violated.
- **Robust Alternatives**: Use Welch's ANOVA or Kruskal-Wallis if assumptions violated.

### Known Mathematical Constraints

**Multicollinearity Acknowledgment**: Braid index ≤ crossing number for most knots [UNRESOLVED-CLAIM: c_79b6cc4f — status=not_enough_info] (known inequality). VIF > 5 flagged as potential multicollinearity issue affecting coefficient interpretation.

**Invariant Dependencies**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index. Validation is exploratory correlation analysis, not independence testing.

**Mathematical Bounds**: All correlation analyses must acknowledge known mathematical relationships:
- MFW inequality relates braid index to crossing number [UNRESOLVED-CLAIM: c_5dfe8d0c — status=not_enough_info]
- Volume ≤ c × crossing number for hyperbolic knots [UNRESOLVED-CLAIM: c_ac9aca6d — status=not_enough_info]
- Observed correlations reflect these bounds rather than free empirical discovery

**Generalizability Limitation**: Filtering to hyperbolic knots only (torus/satellite excluded) restricts conclusions to the hyperbolic subclass. Generalizability to all prime knots is explicitly NOT claimed.

## Reproducibility Requirements

- **Random Seeds**: Pinned in code per Constitution Principle I; documented in `docs/reproducibility/`.
- **Checksums**: SHA-256 for all data files recorded under `data/` per Constitution Principle III.
- **Derivation Notes**: Formula citations with page/section references, step-by-step transformation logic.
- **Timestamped Logs**: Capture `timestamp`, `operation`, `input_file`, `output_file`, `parameters`, `status`, `duration_ms`.

## Limitations and Scope Boundaries

### Phase 1 Limitations

1. **Knot Class Scope**: Alternating/non-alternating dichotomy only; torus, satellite, hyperbolic classes deferred to Phase 2+.
2. **Validation Scope**: Crossing number ≤10 validated; 11-13 data collected but not validated in Phase 1.
3. **Composite Score**: Equal weights (1:1) are exploratory; no theoretical basis for differential weighting.
4. **Hyperbolic Volume**: Torus and satellite knots have zero/undefined volume; filtered with documentation.
5. **Generalizability**: Conclusions restricted to hyperbolic knots only (selection bias acknowledged).

### Measurement Precision Standard

As emphasized in reviewer feedback, the standard of evidence must establish precision across different classes of prime knots. Crossing number is well-defined; braid index requires careful experimental determination with documented algorithm validation (≥95% match threshold per SC-012).

## Tie-Breaking Validation

A dedicated validation script `code/validation/tie_breaking_validator.py` checks that for any knot with multiple diagram representations the chosen representation follows the hierarchy (braid word > DT code; lexicographically first DT code). Results are logged in `docs/reproducibility/validation_status.md`.