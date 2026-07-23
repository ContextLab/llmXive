# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research investigates the relationship between combinatorial invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) for the complete census of prime knots with crossing number ≤ 13. The study is purely descriptive, as the dataset represents a finite population (the set of hyperbolic prime knots) rather than a sample.

## Dataset Strategy

### Primary Dataset: Knot Atlas
- **Source**: Knot Atlas (https://katlas.org)
- **Access Method**: Direct HTTP fetch via `requests` library with **parallelization** (concurrent fetches per crossing number 1-13) and exponential backoff.
- **Data Format**: JSON (or CSV export if available via API).
- **Content**: Crossing number, braid index, hyperbolic volume, alternating/non-alternating classification, diagram representations (DT codes, braid words).
- **Scope**: All prime knots with crossing number ≤ 13 (A substantial count is observed, source: OEIS A002863).
- **Justification**: Knot Atlas is the canonical source for tabulated knot invariants and provides the necessary fields for the analysis. It is directly accessible without authentication or data-use agreements, making it feasible for automated CI execution.
- **Aggregation Logic**: The system will fetch data for each crossing number (1 through 13) individually to ensure the full census is captured, then aggregate into a single dataset.

### Reference Dataset: KnotInfo (for Validation)
- **Source**: KnotInfo (https://knotinfo.org)
- **Access Method**: Programmatic lookup or manual verification for a subset of knots (due to potential lack of bulk download API).
- **Purpose**: Validate hyperbolic volume and core invariants (crossing number, braid index) against an independent (or semi-independent) source.
- **Limitation**: KnotInfo may share underlying data sources with Knot Atlas (e.g., Hoste-Thistlethwaite-Weeks enumeration), limiting the independence of the validation. This is explicitly documented in the reproducibility reports.

### Data Availability & Feasibility
- **Feasibility**: The Knot Atlas dataset is small. and can be fully downloaded and processed on a CPU-only GitHub Actions runner within the allocated time limit.
- **Streaming**: Not required; the full dataset fits in memory.
- **Fallback**: If Knot Atlas is unavailable, the system will cache partial results and retry with exponential backoff (FR-008). No open substitute for the *exact* same dataset exists; the analysis is specific to Knot Atlas data.

## Statistical Methodology

### Census Data Acknowledgment
The dataset represents the **complete census** of hyperbolic prime knots ≤ 13 crossings (a subset of the 9,988 total prime knots). Therefore:
- **No Inferential Statistics**: P-values and confidence intervals are **not** reported for inferential claims (Constitution Principle VII exception).
- **Descriptive Metrics**: Effect sizes (Cohen's d, correlation coefficients r/r²) and goodness-of-fit metrics (R², AIC/BIC, MAE) are the primary metrics of interest.
- **Model Selection**: Based on descriptive fit metrics (R², AIC/BIC), not statistical power or cross-validation.

### Correlation Analysis
- **Primary Method**: Spearman correlation (robust to discrete integer-valued invariants).
- **Supplementary Method**: Pearson correlation (reported for completeness, with caveats about discrete data).
- **Variables**: Crossing number vs. Braid index; Crossing number vs. Hyperbolic volume; Braid index vs. Hyperbolic volume.
- **Note on Crossing Number vs. Braid Index**: The relationship between crossing number (c) and braid index (b) is constrained by the inequality b ≤ c (and often b ≈ c/2 for alternating knots). This correlation is computed **descriptively** to validate known mathematical bounds, not to discover a new empirical relationship.

### Regression Modeling
- **Model Types**: **Ridge Regression** (L2 regularization) is the primary method for joint models to handle multicollinearity. Polynomial (degree 2, 3) and Logarithmic models are supplementary.
- **Predictors**: Crossing number, Braid index (jointly and separately).
- **Outcome**: Hyperbolic volume.
- **Constraints**:
  - **Mathematical Dependency**: Braid index ≤ Crossing number (definitional constraint). Coefficients are **descriptive only** and cannot be interpreted as independent effects.
  - **Multicollinearity**: **Ridge Regression** is used to shrink coefficients and handle the extreme collinearity expected from the b ≤ c constraint. VIF will be computed as a diagnostic.
  - **Filtering**: Only hyperbolic knots (volume > 0) are included in volume prediction models (FR-012). The analysis population is the hyperbolic subset, not the full set of knots.

### Residual Analysis
- **Goal**: Identify specific hyperbolic knot families (e.g., pretzel, non-alternating) that deviate significantly from the global trend.
- **Method**: Compute residuals from the best-fit model; flag knots with large residuals using **Median Absolute Deviation (MAD)** (≥ 2 MAD) instead of standard deviation to ensure robustness against the skewed/truncated distribution of volumes.
- **Grouping**: Group flagged knots by family type if metadata available.

### Group Comparisons
- **Groups**: Alternating vs. Non-alternating knots.
- **Metrics**: Mean differences, variance ratios, Cohen's d.
- **Note**: ANOVA is not applicable for census data; descriptive statistics suffice.

## Computational Feasibility

- **CPU-First**: All methods (parsing, regression, plotting) are CPU-tractable.
- **Memory**: A moderate amount of RAM is sufficient for the ~10k record dataset..
- **Time**: Estimated < 1 hour for full pipeline on 2-core CPU (with parallel download).
- **GPU**: Not required. No transformer or diffusion models are used.

## Ethical Considerations & Limitations

- **Selection Bias**: Filtering to hyperbolic knots (volume > 0) excludes torus and satellite knots. Conclusions apply only to hyperbolic prime knots.
- **Source Independence**: Validation against KnotInfo may be limited by shared underlying data sources.
- **Mathematical Constraints**: The definitional relationship between crossing number and braid index limits the interpretability of joint regression coefficients. Ridge Regression is used to mitigate spurious variance attribution.
- **Phase 1 Scope**: Validation benchmark focuses on crossing number ≤ 10; 11-13 data is exploratory.
