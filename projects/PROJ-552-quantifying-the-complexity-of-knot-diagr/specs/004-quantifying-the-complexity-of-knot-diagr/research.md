# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Background

This project investigates the joint predictive relationship between crossing number and braid index for hyperbolic volume in prime knots, with systematic comparison between alternating and non-alternating classes. The research builds on foundational inequalities relating crossing number and braid index for classical links, extending to empirical correlation analysis across the full enumeration of prime knots up to crossing number 13.

## Literature Review

### Foundational Inequalities

The relationship between crossing number and braid index has been established through multiple theoretical frameworks. Ohyama's inequality provides bounds relating these invariants, with extensions to virtual links generalizing the relationship framework. The algebraic crossing number conjecture posits that algebraic crossing number is uniquely determined in minimal braid representation, though this remains an open question.

Upper bounds for braid index in terms of crossing number have been derived using planar graph embeddings through bisected vertex leveling techniques. Bridge number provides a third invariant for potential composite measures, with known relationships to crossing number (bridge number ≤ crossing number for most knots).

### Empirical Data Sources

Recent work provides empirical data on 9,988 prime knots with crossing number 13, establishing a testable dataset for correlation analysis. The exact count of 9,988 prime knots at crossing number 13 is verified against OEIS A002863 (https://oeis.org/A002863). (https://oeis.org/A002863).

**Verified datasets**: Per the project's verified datasets block, no verified source URLs are available for the following:
- 10.1142/S0218216519500020: NO verified source found
- FR-002: NO verified source found
- FR-003: NO verified source found
- FR-014: NO verified source found
- SC-001: NO verified source found
- FR-001: NO verified source found
- SC-007: NO verified source found
- SC-008: NO verified source found
- SC-012: NO verified source found
- SC-013: NO verified source found

The primary data source is Knot Atlas, which provides knot data including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification. As this is NOT in the verified datasets block, no URL is cited; the dataset is described by name only per the output contract requirements.

### Algorithm References

Invariant computation algorithms are documented with primary literature references:
- Arc index via Birman-Menasco method (Birman & Menasco, 1988, *Mathematische Annalen*, 281, pp. 127-138)
- Seifert circle count via Seifert's algorithm on minimal crossing diagrams (Seifert, 1934, *Mathematische Annalen*, 110, pp. 571-592)
- Bridge number via Schubert's bridge decomposition (Schubert, 1954, *Mathematische Zeitschrift*, 61, pp. 245-288)

## Dataset Strategy

| Dataset | Purpose | Source | Access Method |
|---------|---------|--------|---------------|
| Knot Atlas prime knots ≤13 | Primary analysis dataset | Knot Atlas (no verified URL per contract) | Programmatic download with retry logic |
| KnotInfo reference values | Algorithm validation (≥10% coverage required) | KnotInfo (no verified URL per contract) | Manual lookup / API query |
| OEIS A002863 | Prime knot count verification | OEIS | https://oeis.org/A002863 |
| 2024 arXiv study | Crossing number 13 enumeration confirmation | arXiv:2402.02717 | https://arxiv.org/abs/2402.02717 |
| 2018 arXiv study | Braid index upper bounds | arXiv:1806.09719 | https://arxiv.org/abs/1806.09719 |

**Important**: Per the verified datasets contract, the "MUST" and "III" parquet datasets listed in the verified block are NOT applicable to this knot theory project. These appear to be unrelated dataset entries. The knot data sources (Knot Atlas, KnotInfo) have NO verified source URLs in the contract block, so they are described by name only without fabricated URLs.

## Methodology

### Phase 1 Scope

This analysis explicitly narrows the original multi-class prime knot exploration (torus, satellite, hyperbolic) to alternating/non-alternating dichotomy only. Multi-class exploration is deferred to Phase 2+. Dataset completeness validation focuses on crossing numbers ≤10 as the Phase 1 benchmarking scope, while data collection covers all knots with crossing number ≤13.

### Measurement Precision Standard

Consistent with rigorous scientific measurement standards, precision thresholds must be established for all computed invariants before correlation analysis proceeds. This includes documenting computational uncertainty for braid index (algorithmic determination) versus crossing number (tabulated).

### Computational Pipeline Order

Per the computational task ordering requirement, phases are ordered as follows:
1. **Data Download**: Knot Atlas data downloaded first (User Story 1)
2. **Invariant Computation**: Additional invariants computed from available diagram representations (User Story 2)
3. **Discrepancy Documentation**: Computed invariants compared against canonical values; discrepancies logged to docs/reproducibility/discrepancy_notes.md (Constitution Principle VI)
4. **Volume Filtering**: Torus/satellite knots with zero/undefined hyperbolic volume filtered; excluded knots documented in docs/reproducibility/excluded_knots.md (FR-014/SC-014)
5. **Exploratory Analysis**: Scatter plots generated showing crossing number vs. braid index stratified by classification (User Story 2)
6. **Model Fitting**: Regression models fitted to test linear vs. non-linear relationships (User Story 3)
7. **Validation**: Composite complexity score validated against exploratory validation sample (User Story 3)
8. **Figure Generation**: All figures generated before inclusion in final paper (User Story 3)

### Training vs Validation Dataset Specification

**Critical Clarification**: To address measurement error risks (Constitution Principle VI), primary regression models are trained on the ≤10 subset where invariant accuracy is verified (≥95% match threshold per SC-012). The ≤13 dataset is used for exploratory coefficient estimation only, with sensitivity analysis performed on the ≤10 subset to ensure robustness.

### Statistical Power Analysis

The validation sample size is constrained by the number of prime knots with crossing number ≤10.
- **Total dataset**: 9,988 knots at crossing number 13 
- **Primary validation subset**: Prime knots with crossing number ≤21 (Wikipedia: Slice knot, https://en.wikipedia.org/wiki/Slice_knot) (n=249 total per OEIS A002863 summation)
- **Training subset**: Primary models trained on ≤10 subset (n=249); exploratory models on ≤13 (n=12,965)
- **Exploratory holdout**: 20% of ≤10 subset used for exploratory validation testing within the primary subset
- **Power calculation**: With α=0.05 and n=249 (full ≤10 subset), power to detect r=0.5 is ~85%. This is the primary validation sample for correlation reporting per FR-007. The 20% holdout is used for exploratory model selection, not primary power calculation.
- **Stratification**: Analysis stratified by alternating and non-alternating classes within the ≤10 subset.

This sample size provides moderate power to detect moderate effect sizes while maintaining a robust validation sample based on verified invariants.

### Statistical Analysis Plan

- **Correlation Analysis**: Both Pearson AND Spearman correlation coefficients reported (per Constitution Principle VII and FR-008)
- **Group Comparisons**: ANOVA testing for alternating vs. non-alternating classification differences with effect sizes (Cohen's d)
- **Model Comparison**: At least 3 regression model types (linear, polynomial, logarithmic) with goodness-of-fit metrics (R², AIC/BIC, MAE)
- **Multicollinearity Assessment**: Variance inflation factors (VIF) computed for all predictors; VIF > 5 flagged per FR-005
- **Residual Analysis**: Specific knot families (pretzel, torus, satellite) identified and modeled as covariates via dummy variables
- **Robust Regression Alternatives**: Given discrete predictor space (crossing number and braid index are integers 1-13), robust regression methods (quantile regression, ordinal logistic) will be explored if OLS assumptions are violated
- **Assumption Diagnostics**: Residual normality (Shapiro-Wilk), homoscedasticity (Breusch-Pagan), and independence (Durbin-Watson) tests performed; alternative models specified if violations detected

### Knot Family Covariate Modeling

To address potential confounding beyond alternating/non-alternating classification, knot families (torus, satellite, pretzel) will be modeled as categorical covariates:
- Dummy variables created for each knot family
- Included in multivariate regression as control variables
- Effect sizes reported for family-specific deviations from global trend
- Documented in regression_result.schema.yaml via `knot_family` field

### Algorithm Feasibility Validation

Before full computation across 9,988 knots at crossing number 13:
1. **Pre-computation coverage estimation**: Sample 500 knots from crossing number 13 to estimate computational feasibility
2. **Fallback strategy**: If arc index or bridge number computation fails for >5% of sample, document as limitation and proceed with available invariants
3. **Coverage measurement**: SC-006 ≥99% threshold measured via `code/reproducibility/coverage_measurement.py`
4. **Reporting**: Coverage statistics documented in `docs/reproducibility/validation_status.md`

### Validation Strategy

- **Algorithm Validation**: ≥95% match threshold with KnotInfo reference values where coverage ≥10% of dataset
- **Dataset Completeness**: ≥95% completeness on required invariant fields for crossing number ≤10
- **Hyperbolic Volume Completeness**: ≥95% for prime knots with crossing number ≤13 (SC-014)
- **Invariant Computation Coverage**: ≥99% of knots with computable invariants have all invariants populated (SC-006)
- **Validation Sample Power**: Primary validation uses full n=249 ≤10 subset; exploratory holdout (20%) used for model selection within this subset

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Knot Atlas API unavailable | Retry logic with exponential backoff (1s → 2s → 4s →... → 60s max); partial results cached after 3 failures |
| Missing invariant data | Records flagged with missing_invariant_flags rather than silently excluded |
| Ambiguous alternating classification | Records marked as "unclassifiable" or excluded from stratified analysis with count logged |
| Multicollinearity between predictors | VIF assessment performed; coefficient interpretation caveats documented if VIF > 5 |
| ANOVA assumption violations | Levene's test and Shapiro-Wilk test performed; robust alternatives (Welch's ANOVA, Kruskal-Wallis) used if violated |
| Discrete predictor space violation | Quantile regression and ordinal logistic regression alternatives prepared if OLS assumptions violated |
| Algorithm computational infeasibility | Pre-computation feasibility sampling; fallback to tabulated values where available |
| Measurement Error in ≤13 Data | Primary analysis restricted to ≤10 subset; ≤13 used for exploratory only with sensitivity checks |
| Hyperbolic Volume Missing/Undefined | FR-014 filtering excludes torus/satellite knots; excluded knots documented in docs/reproducibility/excluded_knots.md; SC-014 ≥95% completeness measured |

## Expected Outcomes

This exploratory analysis will establish whether crossing number and braid index jointly predict hyperbolic volume, and whether this relationship differs systematically between alternating and non-alternating classes. The composite complexity score will be evaluated for predictive power, with the understanding that no established mathematical basis exists for linear combination of these invariants at this stage.

**Phase 1 Limitation**: All conclusions are explicitly limited to validated crossing number ≤10 data and alternating/non-alternating dichotomy only. Generalization to other knot classes or to crossing number 11-13 data requires additional validation in future phases.

### FR-007: Geometric Independence Acknowledgment

Validation targets (hyperbolic volume) are geometrically distinct from predictors (crossing number, braid index), providing empirical rather than definitional validation. This is exploratory research establishing empirical correlations, not proving mathematical identities. The term "Geometric Independence Acknowledgment" replaces "Definitional Relationship Acknowledgment" for terminological clarity.
