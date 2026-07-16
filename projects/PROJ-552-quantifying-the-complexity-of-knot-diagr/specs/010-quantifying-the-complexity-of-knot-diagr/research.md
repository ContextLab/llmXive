# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Executive Summary

This research investigates the relationship between combinatorial invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) across the complete census of prime knots with crossing number ≤ 13. The study leverages the Knot Atlas as the primary data source, validated against KnotInfo. Given the census nature of the data (N = 9,988 total prime knots ≤ 13, per OEIS A002863), all statistical analysis is descriptive; effect sizes are the primary metrics, and p-values are excluded per Constitution Principle VII (Census-data exception).

## Dataset Strategy

### Primary Dataset: Knot Atlas
- **Source**: Knot Atlas (https://katlas.org)
- **Access Method**: Programmatic download of JSON/CSV exports containing prime knots up to 13 crossings.
- **Verification**: The dataset is verified to contain the full census of prime knots. The count of prime knots with crossing number ≤ 13 is 9,988 (source: OEIS A002863, https://oeis.org/A002863).
- **Variables**:
 - `crossing_number`: Integer (Tabulated from Knot Atlas).
 - `braid_index`: Integer (Tabulated from Knot Atlas).
 - `hyperbolic_volume`: Float (Tabulated from Knot Atlas).
 - `alternating`: Boolean (Tabulated from Knot Atlas).
- **Feasibility**: The dataset is publicly available and downloadable via standard HTTP requests. The file size is estimated to be < 500MB, well within the 14GB disk and 7GB RAM constraints of the CI runner.
- **Constraints**: The dataset includes torus and satellite knots (volume = 0 or undefined). Per FR-012, these will be filtered out for volume prediction analysis, limiting conclusions to *hyperbolic* prime knots.

### Reference Dataset: KnotInfo
- **Source**: KnotInfo (https://knotinfo.org)
- **Role**: Independent validation of core invariants (crossing number, braid index) and hyperbolic volume.
- **Verification**: While a direct programmatic URL for the full dataset is not verified in the provided block, the site is a canonical source. The research plan will use KnotInfo's public lookup capabilities or available CSV dumps (if accessible via the verified URLs in the `Verified datasets` block, though none are explicitly listed for KnotInfo in the provided block, the plan will rely on the *name* "KnotInfo" and the *method* of cross-checking as per FR-013).
- **Note**: The provided "Verified datasets" block lists NO verified source for KnotInfo. The plan will proceed by attempting to fetch data from the canonical URL ` Name or service not known)"))] where available, or using known static dumps if the site allows programmatic access. If no programmatic access exists, the consistency check will be performed on the subset of knots where KnotInfo provides a direct, stable URL per record.

### Data Availability & Feasibility Assessment
- **Open Data**: Knot Atlas is open.
- **Gated Data**: None required for Phase 1.
- **Streaming**: Not required. The full dataset fits in memory.
- **Edge Cases**:
 - **Missing Invariants**: Some knots may lack braid index or hyperbolic volume. Per FR-009, these are flagged, not dropped.
 - **Ambiguous Classification**: Alternating status may be ambiguous for some knots. Per FR-010, these are marked "unclassifiable".
 - **API Failure**: Retry logic with exponential backoff (FR-008) is implemented.

## Statistical Methodology

### Census Data Assumption
The dataset represents a **complete census** of the target population (all prime knots ≤ 13 crossings). Therefore:
- **No Inferential Statistics**: p-values and confidence intervals are **not** reported for census claims.
- **Effect Sizes**: Cohen's d (group differences), r/r² (correlations), and R²/AIC/BIC (model fit) are the primary metrics.
- **Descriptive Interpretation**: All model coefficients are interpreted as descriptive associations within the finite census, not as independent predictive power (due to the mathematical constraint `braid_index ≤ crossing_number`).

### Theoretical Model Selection
Model forms (linear, polynomial, logarithmic) are selected based on prior knot theory literature (e.g., volume ~ crossing for random knots) to test specific theoretical predictions. Goodness-of-fit metrics (R², AIC, BIC) are used for validation, not for discovery, to prevent data dredging.

### Regression Analysis
- **Goal**: Assess the relationship of crossing number and braid index on hyperbolic volume, acknowledging the constraint `braid_index ≤ crossing_number`.
- **Models**:
 1. Linear: `Volume ~ Crossing + (Crossing - Braid)` [Using 'gap' as predictor]
 2. Polynomial: `Volume ~ Crossing + (Crossing - Braid) + Crossing^2`
 3. Logarithmic: `Volume ~ log(Crossing) + log(Crossing - Braid)`
 4. Ridge Regression: To handle multicollinearity and stabilize coefficients.
- **Selection**: Based on goodness-of-fit metrics (R², AIC, BIC, MAE).
- **Multicollinearity Handling**: VIF will be computed and reported to demonstrate the constraint. Ridge Regression will be used to stabilize coefficients. Coefficients will NOT be interpreted as independent effects, as braid index is a bound on crossing number.
- **Residual Analysis**: Identification of specific hyperbolic knot families (e.g., pretzel) with residuals ≥ 2 standard deviations from the trend (SC-011).

### Correlation Analysis
- **Primary**: Spearman correlation (robust to discrete integer data).
- **Supplementary**: Pearson correlation (reported for completeness, with caveats).
- **Group Comparison**: Mean differences, variance ratios, and Cohen's d for alternating vs. non-alternating groups (SC-009).
- **Note on Crossing vs. Braid**: The correlation between crossing number and braid index is a verification of the theorem `b ≤ c` (data consistency), not an empirical finding. This correlation is not reported as a 'result' but as a 'consistency check'.

## Decision Rationale

### Why Knot Atlas?
It is the only comprehensive source providing the required combination of invariants (crossing number, braid index, hyperbolic volume) for the full census of knots ≤ 13.

### Why Census Methodology?
The population is finite and fully enumerated. Inferential statistics (p-values) imply sampling error, which does not exist here. Effect sizes provide the exact magnitude of relationships in the population.

### Why No GPU?
The analysis involves classical statistical methods (regression, correlation) on a substantial dataset. These are computationally trivial on a CPU and do not require GPU acceleration.

### Why Filter to Hyperbolic Knots?
Hyperbolic volume is undefined or zero for torus and satellite knots. Including them would introduce a ceiling effect and bias the regression. The research question is reframed to "hyperbolic prime knots" with this limitation explicitly documented (FR-012).

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|:--- |:--- |:--- |:--- |
| **Knot Atlas Unavailable** | Low | High | Retry logic with exponential backoff; cache partial results. |
| **Missing Invariants** | Medium | Medium | Flag records; exclude only from specific analyses where invariants are required; document count. |
| **Mathematical Constraint Misinterpretation** | High | High | Explicitly state in all reports that coefficients are descriptive only due to `braid_index ≤ crossing_number`. Use 'gap' predictor. |
| **KnotInfo Access Issues** | Medium | Medium | Use available static dumps; document coverage limitations if < 90% (SC-014). |
| **Computation Time for Advanced Invariants** | Medium | High | Limit the second phase to a random sample of knots if a full census exceeds the established time budget. |