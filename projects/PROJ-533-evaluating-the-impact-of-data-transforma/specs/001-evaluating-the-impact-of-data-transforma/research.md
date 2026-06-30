# Research: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Background

Data transformations are commonly applied to satisfy the normality assumption of parametric tests like the t-test and ANOVA. However, the impact of these transformations on Type I error rates (false positives) and statistical power (true positive detection) is not uniformly understood, especially across diverse real-world distributions. This research evaluates three transformations: Box-Cox (requires positive values), Yeo-Johnson (handles zeros/negatives), and rank-based inverse normal transformation (INT).

## Dataset Strategy

### Verified Datasets
Per the project's verified dataset constraints, the following sources are available for download and filtering. **Note**: The verified list below provides tabular datasets with continuous variables and categorical group labels suitable for t-test/ANOVA. The remaining datasets will be sourced from OpenML programmatic loaders where URLs are documented in `data/datasets.csv`.

| Source | Type | Verified URL | Notes |
|--------|------|--------------|-------|
| OpenML Credit Card Fraud | CSV | | Continuous features, binary group label (fraud/non-fraud), highly imbalanced |
| OpenML Bank Marketing | CSV | | Continuous features, binary group label (subscription), non-normal distributions |
| UCI Wine Quality | CSV | https://archive.ics.uci.edu/ml/datasets/wine+quality | Continuous features, ordinal group labels (quality score), skewed distributions |
| UCI Concrete Strength | CSV | https://archive.ics.uci.edu/ml/datasets/concrete+compressive+strength | Continuous features, continuous target (binned for group analysis), heavy-tailed |

**Note**: The spec requires multiple datasets. The verified list above provides a set of explicitly verified sources. The remaining datasets must be sourced from UCI/OpenML via programmatic loaders (e.g., `openml.datasets.get_dataset`) or direct HTTP downloads where URLs are documented in `data/datasets.csv`. **No fabricated URLs will be used.** If a dataset lacks a verified source in the block, it will be described by name and source but not cited with a URL.

### Filtering Criteria (FR-002)
- **Normality**: Shapiro-Wilk test p < 0.05 (non-normal) **AND** absolute skewness > 0.5 or absolute kurtosis > 3.5 (to ensure meaningful non-normality).
- **Sample Size**: N ≥ 30
- **Variables**: At least one continuous variable and one categorical group label with ≥2 levels
- **Missing Data**: Datasets with >10% missing values are excluded; others imputed via mean/median
- **Stratification**: Datasets are categorized into "Mild" (0.5 < |skew| < 1.5) and "Severe" (|skew| ≥ 1.5 or kurtosis ≥ 5) non-normality groups to ensure coverage of distribution types.

### Dataset Fit Assessment
- **Required Variables**: Continuous predictors (for transformation), categorical group labels (for t-test/ANOVA)
- **Fit Confirmation**: All verified datasets contain continuous variables and group labels. However, true effect sizes are unknown in real-world data—power estimation requires simulated data (US-4).
- **Gap Handling**: If a dataset lacks group labels or continuous variables, it is excluded with logging (FR-002).

## Methodology

### Type I Error Estimation (FR-004)
1. **Null Simulation**: For each dataset, shuffle group labels multiple times with fixed seed (42).
2. **Transformation**: Apply Box-Cox, Yeo-Johnson, and rank-based INT to continuous variables.
3. **Test**: Run t-test (2 groups) or ANOVA (>2 groups) on transformed data.
4. **Metric**: **Raw** proportion of p < 0.05 results across 1000 iterations = Type I error estimate. **No correction is applied to this metric** to ensure valid comparison against the nominal alpha (0.05).
5. **Correction**: Bonferroni correction is applied **only** for post-hoc pairwise comparisons in the aggregation phase (FR-008) and for power analysis multiplicity, not for the raw Type I error calculation.

### Power Estimation (FR-005, FR-006)
1. **Simulation**: Generate synthetic data from **non-normal distributions** (log-normal, t-distribution with df=3, beta distribution) with known effect sizes (Cohen's d ∈ {0.2, 0.5, 0.8}).
2. **Groups**: 2 or more groups with known mean differences.
3. **Transformation**: Apply same three transformations.
4. **Test**: Run t-test/ANOVA.
5. **Metric**: Proportion of p < 0.05 results = power estimate.
6. **Validation**: Bootstrap CI half-width target ±0.02.

### Aggregation & Analysis (FR-007, FR-008)
- **Aggregation**: Mean Type I error and power across 50+ datasets per transformation-test combination.
- **Confidence Intervals**: Bootstrap confidence intervals (1000 resamples).
- **Statistical Test**: **Generalized Linear Mixed Model (GLMM)** with binomial link function to assess the effect of transformations on error rates. The model treats the error rate as a proportion (successes/1000) with the number of iterations as the denominator, including dataset as a random effect to account for varying precision.
- **Post-hoc**: Pairwise comparisons of transformation effects with Bonferroni correction for family-wise error rate.
- **Sensitivity**: Sweep α ∈ {, 0.05, 0.1} and report false-positive rates.

## Statistical Rigor Considerations

- **Multiple Comparisons**: Bonferroni correction applied for post-hoc tests; family-wise error rate controlled. Raw Type I error rates are reported uncorrected.
- **Power Limitations**: Sample size per condition is [deferred] pending dataset availability; power limitations acknowledged in final report.
- **Causal Framing**: All findings framed as associational (observational design); no causal claims.
- **Measurement Validity**: Public datasets with documented variable definitions; no instruments used.
- **Collinearity**: Transformations are mutually exclusive per variable; no collinearity diagnostics required.
- **Non-Normality Definition**: Non-normality is defined via distributional parameters (skewness/kurtosis) to avoid circular dependency on the Shapiro-Wilk test used for selection.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (limited CPU, ~7 GB RAM, 14 GB disk, NO GPU).
- **Optimization**:
 - Data subset to fit memory (~7 GB RAM).
 - Parallel processing limited to cores (CPU-bound).
 - Checkpointing after each dataset to allow resumption.
 - No GPU/CUDA; all libraries CPU-compatible (`scikit-learn`, `scipy`, `statsmodels`).
- **Runtime**: Target ≤6 hours for full pipeline; estimated per-dataset time [deferred].

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Use `scikit-learn` for transformations | CPU-tractable, well-tested, supports Box-Cox, Yeo-Johnson, and rank-based INT |
| Use `scipy.stats` for statistical tests | Native support for t-test, ANOVA, Shapiro-Wilk |
| Use `statsmodels` for GLMM | Robust implementation of binomial GLMM with random effects for proportion data |
| Simulate power with non-normal data | Real-world data is non-normal; simulation must match this to test transformation efficacy |
| Bootstrap CI for aggregation | Non-parametric, robust to distributional assumptions, fits memory constraints |
| Checkpointing after each dataset | Ensures progress is saved if 6-hour limit is approached; enables resumption |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Insufficient datasets (fewer than 50) | Expand search to OpenML programmatic loader; document all sources in `data/datasets.csv` |
| Transformation failure (e.g., Box-Cox on negative values) | Apply log-shift to make values positive; log intervention per variable |
| Missing data >10% | Exclude dataset; log exclusion reason |
| Runtime exceeds 6 hours | Implement checkpointing; reduce iterations if necessary (document trade-off) |
| Memory overflow | Stream data; process one dataset at a time; avoid loading all datasets simultaneously |