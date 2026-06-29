# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Summary

This research investigates whether combinatorial invariants (crossing number, braid index) can predict geometric complexity (hyperbolic volume) for hyperbolic prime knots with crossing number ≤ 13. Because the dataset constitutes a **complete census** of the target population, the analysis is purely descriptive: effect sizes (Cohen’s d, r, r²) and goodness‑of‑fit metrics are reported, while p‑values are omitted per Constitution Principle VII (census‑data exception).

## Dataset Strategy

| Dataset | Description | Source | Access Method | Notes |
|---------|-------------|--------|---------------|-------|
| Knot Atlas | Prime knot invariants (crossing number, braid index, hyperbolic volume, alternating classification) | Knot Atlas (canonical source) | HTTP fetch with exponential back‑off retry logic (FR‑008) | No verified URL; referenced by name only. Data format: JSON schema or CSV export with documented column mapping (FR‑001). |
| KnotInfo | Reference values for consistency checks (hyperbolic volume, core invariants) | KnotInfo | HTTP fetch for validation subset | Used for FR‑013 consistency check; ≥ 90 % match within **1e‑6** tolerance required. |
| OEIS A002863 | Prime knot enumeration counts by crossing number | Online Encyclopedia of Integer Sequences | Reference documentation | Source for total prime knot count (9988 for ≤ 13 crossings). |

### Dataset Completeness Validation

* **Phase 1 Benchmark (≤ 10 crossings)** – Full completeness documented in `docs/reproducibility/validation_scope.md` (SC‑001).  
* **Exploratory Range (11‑13 crossings)** – Data are downloaded and processed but not formally validated; results from this range will be presented in a separate **Exploratory Findings** section of the manuscript, labelled as exploratory and interpreted with caution.  
* **Null‑percentage requirement** – Any required field with > 5 % nulls aborts the pipeline (SC‑005).  
* **Format‑pass rate** – Must be ≥ 99 % (SC‑005).  
* **Duplicate check** – Zero duplicates required (SC‑[relevant standard]).  

### Required Variables

| Variable | Type | Source | Notes |
|----------|------|--------|-------|
| crossing_number | integer | Knot Atlas | Integer ≥ 3, ≤ 13 |
| braid_index | integer | Knot Atlas | Integer ≥ 2, ≤ crossing_number |
| hyperbolic_volume | float (≥ 0) | Knot Atlas | Volume > 0 for hyperbolic knots; 0 for torus/satellite (filtered per FR‑012) |
| alternating | boolean | Knot Atlas | Used for stratified descriptive analysis (FR‑004, FR‑010) |

## Measurement Precision Standards

* **Core Invariants (Phase 1)** – Braid index validated against KnotInfo; ≥ 90 % of records must match within a tolerance of **1e‑6** (FR‑013, SC‑015). If coverage falls below [deferred], a warning is logged and the results are treated as exploratory; no validated conclusions are drawn from those records.
* **Additional Invariants (Phase 2+)** – Deferred; will follow the same [deferred]/1e‑6 rule (FR‑003).

## Statistical Methodology

### Correlation Analysis (FR‑006, SC‑006)

| Metric | Method | Notes |
|--------|--------|-------|
| Primary | Spearman correlation | Discrete invariants |
| Supplementary | Pearson correlation | Reported for completeness |
| Effect Size | r or r² | Reported; no p‑values for census data |

### Regression Models (FR‑005, SC‑002)

| Model Type | Form | Selection Criterion |
|------------|------|---------------------|
| Linear | y = β₀ + β₁x₁ + β₂x₂ + ε | R², AIC/BIC, MAE |
| Polynomial (degree 2) | y = β₀ + β₁x₁ + β₂x₂ + β₃x₁² + β₄x₂² + β₅x₁x₂ + ε | R², AIC/BIC, MAE |
| Logarithmic | y = β₀ + β₁log(x₁) + β₂log(x₂) + ε | R², AIC/BIC, MAE |

*Model selection is based solely on goodness‑of‑fit metrics; no statistical power or significance testing is performed (census‑data exception).*

### Multicollinearity Assessment (FR‑005)

* VIF is computed for all joint models. High VIF values are **expected** because braid index ≤ crossing number by definition. **High VIF does not invalidate the descriptive analysis**; it merely reflects the definitional relationship.

### Residual Analysis (FR‑005, SC‑011)

* Families with residuals ≥ 2 SD are identified and reported **descriptively** as illustrations of finite‑population structure (e.g., pretzel, hyperbolic non‑alternating families). These deviations characterize the population and are **not** treated as outliers in a predictive sense.

### Group Comparison (FR‑004, SC‑009)

| Metric | Calculation | Notes |
|--------|-------------|-------|
| Mean Difference | μ_alternating − μ_non‑alternating | Descriptive |
| Variance Ratio | σ²_alternating / σ²_non‑alternating | Descriptive |
| Cohen’s d | (μ₁ − μ₂) / σ_pooled | Primary effect‑size measure |

*No inferential tests are performed; results are purely descriptive.*

## Edge‑Case Handling (FR‑008, FR‑009, FR‑010, FR‑011)

* **API Unavailability (FR‑008)** – Exponential back‑off (1 s → 2 s → 4 s … max = 32 s); after three consecutive failures partial results are cached.  
* **Missing Invariants (FR‑009)** – Records with `missing_invariant_flags` are **excluded** from any quantitative modelling and documented in `docs/reproducibility/missing_invariants.md`.  
* **Ambiguous Classification (FR‑010)** – Such records are marked “unclassifiable” and omitted from stratified analyses.  
* **Diagram Representation Ties (FR‑011)** – Resolved by the tie‑breaking hierarchy; validated by `tie_breaking_validator.py` (SC‑007).

## Source Independence Assessment (FR‑013)

* Knot Atlas and KnotInfo share underlying enumeration sources; therefore the ≥ 90 % consistency check serves as an internal **data‑quality** measure rather than an independent validation of the research hypothesis. This distinction is documented in `docs/reproducibility/hyperbolic_volume_validation.md` to avoid conflating data‑quality validation with the primary analysis.

## Assumptions & Limitations

* **Selection Bias (FR‑012)** – Only hyperbolic prime knots (volume > 0) are included in volume‑prediction analyses; torus and satellite knots are excluded and listed in `excluded_knots.md`.  
* **Invariant Type Distinction** – Crossing number and braid index are combinatorial; hyperbolic volume is geometric. Any observed relationship is descriptive, not causal.  
* **Mathematical Constraint** – Braid index ≤ crossing number is a definitional relationship; regression coefficients are therefore not interpreted as independent explanatory effects.  
* **Negative Result Definition** – A *negative result* is defined as **R² ≤ 0.05** for all fitted models, indicating that neither invariant explains a non‑trivial proportion of variance in hyperbolic volume.  

## Reporting

* Findings for ≤ 10 crossings will be presented as **validated** results.  
* Findings for 11‑13 crossings will be labelled **exploratory** and interpreted with caution.  
* All effect sizes, R², AIC/BIC, MAE, VIF, and residual‑family descriptions will be included in the final manuscript, with no p‑values reported for census data.
