# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research investigates the relationship between combinatorial invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) across the complete census of hyperbolic prime knots with crossing number ≤ 13. The study addresses a gap in systematic, census-wide analysis of joint predictive power and residual patterns among knot families.

**Methodological Correction**: In response to scientific soundness concerns regarding the definitional constraint `braid_index ≤ crossing_number`, this study explicitly avoids treating these variables as independent predictors in a joint regression model. Instead, the analysis proceeds as follows:
1.  **Baseline Model**: Fit a regression of `hyperbolic_volume` on `crossing_number` (c) alone.
2.  **Derived Metric**: Calculate `braid_efficiency` = `braid_index` / `crossing_number` (b/c).
3.  **Residual Analysis**: Analyze the residuals of the baseline model against `braid_efficiency` to identify geometric deviations.

This approach prevents tautological validation (where `b` is a subset of `c`) and focuses on how the *efficiency* of the braid representation correlates with geometric volume.

## Dataset Strategy

### Primary Dataset: Knot Atlas

**Source**: Knot Atlas (https://katlas.org)  
**Scope**: All prime knots with crossing number ≤ 13 crossings  
**Variables**:
- `crossing_number`: Integer, tabulated from Knot Atlas
- `braid_index`: Integer, tabulated from Knot Atlas
- `hyperbolic_volume`: Float, tabulated from Knot Atlas
- `alternating`: Boolean, tabulated from Knot Atlas

**Verification**: 
- Dataset completeness validated against Hoste-Thistlethwaite-Weeks enumeration and OEIS A002863 (source: https://oeis.org/A002863)
- Total prime knots ≤ 13 crossings: 9,988 (source: OEIS A002863, https://oeis.org/A002863)
- Data quality benchmark: ≥ 95% of knots with computable invariants have all required fields populated (SC-005, SC-013)

**Loading Strategy**: 
- Direct HTTP fetch from Knot Atlas with exponential backoff retry logic (FR-008)
- Caching of partial results after consecutive failures
- JSON schema validation via `knot_record.schema.yaml`

### Reference Dataset: KnotInfo

**Source**: KnotInfo (NO verified source found per verified datasets list; do NOT cite URL)  
**Purpose**: Consistency check for hyperbolic volume and core invariants (FR-013, SC-015)  
**Validation Threshold**: ≥ 90% match within absolute tolerance 1×10⁻⁶  
**Coverage Requirement**: ≥ 90% of analyzed knots must have reference data; otherwise skip validation and document limitation

**Note**: KnotInfo and Knot Atlas may share underlying data sources (e.g., Hoste-Thistlethwaite-Weeks enumeration). If so, consistency check measures internal consistency rather than independent verification (FR-013).

## Methodological Approach

### Data Acquisition & Preprocessing

1. **Download**: Fetch Knot Atlas data with retry logic (initial delay 1s, multiplier 2, max 32s) (FR-008)
2. **Parse**: Extract crossing number, braid index, hyperbolic volume, alternating classification (FR-002)
3. **Clean**: Apply tie-breaking rules (braid word > DT code, lexicographic DT) (FR-011)
4. **Validate**: Check against `knot_record.schema.yaml` (format validation ≥ 99%) (FR-002, SC-013)
5. **Filter**: Exclude knots with hyperbolic volume ≤ 0 (torus/satellite knots) (FR-012)
6. **Flag**: Mark records with missing invariants or ambiguous classifications (FR-009, FR-010)
7. **Audit**: Generate `docs/reproducibility/data_fabrication_audit.md` verifying first 100 rows for nulls and constraints (Task T091).

### Statistical Analysis

**Census Data Acknowledgment**: Since the dataset represents a complete census of hyperbolic prime knots ≤ 13 crossings, all analysis is descriptive rather than inferential. Effect sizes (Cohen's d, r, r²) are primary metrics; p-values are NOT reported (Constitution Principle VII exception).

1. **Exploratory Analysis**:
   - Scatter plots: crossing number vs. braid index, stratified by alternating/non-alternating (FR-004)
   - Resolution: 1200×900 px minimum (SC-016)
   - Descriptive statistics: mean differences, variance ratios, Cohen's d for group comparisons (FR-006, SC-009)

2. **Correlation Analysis**:
   - **Structural Correlation**: Compute correlation between `crossing_number` and `braid_index` to quantify the trivial relationship (b ≤ c). This is reported as a baseline mathematical fact, not a geometric discovery.
   - **Geometric Correlation**: Compute Spearman correlation between `braid_efficiency` (b/c) and `hyperbolic_volume`. This measures the non-trivial relationship between braid efficiency and geometric complexity.
   - **Effect Sizes**: r, r² for all correlations (FR-006).

3. **Regression Modeling**:
   - **Baseline Model**: Linear regression of `hyperbolic_volume` ~ `crossing_number` (c).
   - **Residual Analysis**: Analyze residuals of the baseline model.
   - **Efficiency Model**: Regression of `residuals` ~ `braid_efficiency` (b/c) to explain deviations from the c-only trend.
   - **Selection Criteria**: R², AIC/BIC, MAE (SC-002).
   - **Multicollinearity**: VIF assessment is NOT performed on joint (c, b) models as they are invalid. VIF is only assessed if derived features (e.g., b/c) are used in secondary models, with explicit acknowledgment of the mathematical constraint.
   - **Interpretation**: Coefficients are descriptive associations within census, NOT independent effects (FR-005, Assumptions).

4. **Residual Analysis**:
   - Identify hyperbolic knot families with residuals ≥ 2 standard deviations from the `c-only` baseline trend (FR-005, SC-011).
   - Document specific families (e.g., pretzel, hyperbolic non-alternating) and their `braid_efficiency` values to explain deviations.
   - **Baseline Validity**: The baseline is mathematically sound (c-only) and respects the definitional constraints of the invariants.

### Measurement Precision Validation

**Core Invariants** (crossing number, braid index):
- Tabulated from Knot Atlas (SC-008)
- Consistency check vs. KnotInfo reference values (≥ 90% match, tolerance 1e-6) (SC-015)
- If reference coverage < 90%, skip validation and document limitation

**Additional Invariants** (Phase 2+):
- Arc index, Seifert circle count, bridge number (FR-003)
- Computed via Birman-Menasco, Seifert's algorithm, Schubert's decomposition
- Validation against KnotInfo (≥ 90% match, tolerance 1e-6) (FR-003)
- **Excluded from Phase 1** (Assumptions)

### Edge Case Handling

- **API Unavailability**: Exponential backoff retry, partial result caching (FR-008)
- **Missing Invariants**: Flag with `missing_invariant_flags` (FR-009)
- **Ambiguous Classification**: Exclude or mark as "unclassifiable" (FR-010)
- **Diagram Ties**: Apply documented tie-breaking rules consistently (FR-011)
- **Zero/Undefined Volume**: Filter out, document in `excluded_knots.md` (FR-012)

## Statistical Rigor Considerations

### Multiple Comparisons & Family-Wise Error

Not applicable for census data. All comparisons are descriptive statistics of the complete population. No hypothesis testing requiring correction.

### Sample Size & Power

- Complete census of hyperbolic prime knots ≤ 13 crossings (source: OEIS A002863, https://oeis.org/A002863)
- Stratified analysis by alternating/non-alternating classification may yield varying subgroup sizes
- Sample size documentation provided for all groups; power analysis not applicable for census data (Assumptions)

### Causal Inference Assumptions

- Observational data; no randomization
- All claims framed as associational/descriptive, NOT causal
- Mathematical constraint acknowledged: braid index ≤ crossing number (definitional, not empirical) (Assumptions)
- **Correction**: The analysis does not claim independent effects for `braid_index` and `crossing_number`. It claims a relationship between `crossing_number` (baseline) and `braid_efficiency` (residual explanation).

### Measurement Validity

- Core invariants tabulated from Knot Atlas (established in knot theory literature)
- Hyperbolic volume from Knot Atlas; consistency check vs. KnotInfo (FR-013)
- Additional invariants (Phase 2+) validated against KnotInfo reference values (FR-003)

### Predictor Collinearity

- **Correction**: The plan no longer attempts to fit a joint model with `crossing_number` and `braid_index` as predictors, as this creates a tautological relationship (b ≤ c).
- Instead, `braid_efficiency` (b/c) is used as a derived feature.
- VIF analysis is restricted to models where derived features are used, with explicit documentation that high correlation is expected and mathematically defined.

## Decision Rationale: Compute Feasibility

All methods selected for CPU-only execution on GitHub Actions free-tier (2 CPU, 7GB RAM, 14GB disk, no GPU):

- **Data Size**: ~9,988 records (source: OEIS A002863) fits within memory limits
- **Regression Models**: Linear, polynomial, logarithmic via `scikit-learn` (CPU-tractable)
- **Plot Generation**: `matplotlib`/`seaborn` (CPU-only, no GPU acceleration)
- **No Deep Learning**: No neural networks, no large-LLM inference, no GPU training
- **Sampling**: Not required; full census fits within resource constraints

**Fallback Strategy**: If memory constraints arise during analysis, data will be processed in chunks with intermediate results written to disk. No GPU-dependent libraries (e.g., CUDA, bitsandbytes) are used.

## Assumptions & Limitations

- **Selection Bias**: Filtering to hyperbolic knots (volume > 0) means conclusions apply only to hyperbolic prime knots, not all prime knots (FR-012, Assumptions)
- **Invariant Type Distinction**: Combinatorial and geometric invariants measure fundamentally different properties; explanatory relationship may be weak by mathematical definition (Assumptions)
- **Data Source Independence**: Knot Atlas and KnotInfo may share underlying sources; consistency check measures internal consistency, not independent verification (FR-013)
- **Phase 1 Validation Staging**: Validated completeness benchmark focuses on crossing number ≤ 10; 11-13 crossings data is exploratory (Assumptions)
- **Census Data Exception**: p-values not reported for complete enumeration; effect sizes are primary metrics (Constitution Principle VII, FR-006)
- **Methodological Correction**: The analysis explicitly avoids joint regression of `crossing_number` and `braid_index` to prevent tautological validation. The `braid_efficiency` (b/c) metric is used to explain residuals from the `crossing_number` baseline.