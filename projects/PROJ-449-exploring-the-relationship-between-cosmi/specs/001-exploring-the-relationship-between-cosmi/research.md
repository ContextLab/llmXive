# Research: Exploring the Relationship Between Cosmic Ray Composition and Solar Activity Cycles

## Dataset Strategy

| Dataset | Purpose | Source / Verified URL | Notes |
|:--- |:--- |:--- |:--- |
| **NOAA/SWPC Sunspot Numbers** | Retrieve concurrent daily sunspot number data for temporal alignment. | [] | Verified source for daily sunspot numbers (SIDC/SILSO data). |
| **AMS-02 Cosmic Ray Flux** | Retrieve rigidity-binned differential flux data for protons, helium, and CNO/Fe nuclei. | **NO verified source for daily heavy nuclei data found.** | The AMS public repository does not currently provide daily, rigidity-binned data for heavy nuclei (CNO/Fe) for the full 2011-2024 period. The plan will use the most granular available public data (likely monthly or weekly aggregates) and explicitly flag this as a data granularity limitation affecting the daily correlation analysis. If no suitable data is found, the heavy nuclei analysis will be restricted to available time resolutions. |

> **Critical Note on Data Availability**: The specific requirement for "daily averaged, rigidity-binned differential flux data for CNO/Fe nuclei" from AMS-02 for the full 2011–2024 period is not met by currently verified public sources. The implementation will attempt to retrieve the most granular available data (e.g., monthly averages) and document the deviation from the ideal daily resolution. The analysis will proceed only if a verified source for at least one particle species with sufficient temporal resolution is found.

## Methodology & Statistical Plan

### 1. Data Retrieval & Alignment (FR-001, FR-002, FR-007)
- **Source**: NOAA/SWPC (verified URL), AMS-02 (most granular available public data).
- **Alignment**: Merge datasets on `date`.
- **Gap Handling**: **No linear interpolation**. All gaps (even < 5 days) will be excluded from the correlation analysis to preserve phase integrity. A log of excluded periods will be generated.
- **Edge Case Handling**: Zero flux events for heavy nuclei will be logged as "Below Detection Limit" and excluded from ratio calculations.

### 2. Composition Ratio Calculation (FR-003, FR-008)
- **Ratios**: Compute He/p and Fe/p ratios.
- **Control**: Compute absolute, rigidity-normalized fluxes for protons, helium, and heavy nuclei.
- **Rigidity Binning**: All analyses performed **per rigidity bin** to validate rigidity-dependence.

### 3. Correlation Analysis (FR-004, FR-008)
- **Method**: Pearson and Spearman correlation coefficients.
- **Lag Window**: ±12 months (sensitivity analysis: 6, 9, 12, 15 months).
- **Effective Degrees of Freedom**: Apply the Pyper & Peterman method to calculate effective sample size ($N_{eff}$) to correct for autocorrelation before computing p-values.
- **Output**: Correlation matrix and time-lag plots for He/p, Fe/p, and absolute fluxes against sunspot numbers, **per rigidity bin**.
- **Differential Modulation Test**: Perform a statistical test (e.g., Fisher's z-transformation) to compare the correlation coefficients or modulation amplitudes between He/p and Fe/p to test the hypothesis of species-dependent transport.

### 4. Bootstrap Resampling (FR-005)
- **Method**: **Moving Block Bootstrap (MBB)** with block length determined by the autocorrelation time, n=1000 iterations.
- **Rationale**: Standard i.i.d. bootstrap destroys temporal structure; MBB preserves autocorrelation.
- **Output**: 95% confidence intervals for maximum correlation coefficients.
- **Validation**: Test if confidence intervals include zero (null hypothesis).

### 5. Model Fitting (FR-006)
- **Modulation Amplitudes**: Derive time-varying amplitudes using **sliding-window harmonic regression** (window size ~1 year, step ~1 month) to capture the non-stationary nature of solar cycles 24 and 25.
- **Diffusion Model**: Fit a rigidity-dependent diffusion model (e.g., $D(R) \propto R^\delta$) to the observed amplitude trend.
- **Validation Target**: The fit tests the *functional form* of the rigidity dependence (exponent $\delta$) against theoretical predictions, not just the existence of modulation.
- **Output**: Fitted parameters, residual error, R² value, and comparison of $\delta$ to theoretical values.

## Statistical Rigor & Assumptions

- **Observational Nature**: The study is observational; findings will be framed as **associational** correlations, not causal effects.
- **Collinearity**: He/p and Fe/p ratios share the proton flux denominator. The analysis will not claim independent predictive effects for both simultaneously. A collinearity diagnostic (VIF) will be performed if used in a joint model. The control analysis (FR-008) is designed to deconvolve the proton flux contribution.
- **Multiple Comparisons**: Given the large number of tests (multiple lags, multiple rigidity bins, multiple species), a family-wise error correction (e.g., Bonferroni or False Discovery Rate) will be applied to p-values to control for Type I errors.
- **Power Justification**: The effective sample size ($N_{eff}$) will be calculated to determine if the study has sufficient power to detect the observed effect sizes, accounting for autocorrelation.
- **Measurement Validity**: The AMS-02 and NOAA/SWPC datasets are standard in the field. Validation evidence for the instruments will be cited in the final paper.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, ~7 GB RAM, ~14 GB disk, no GPU).
- **Methods**: All methods (pandas, scipy, scikit-learn, statsmodels) are CPU-tractable.
- **Data Volume**: [deferred] daily/weekly data points × ~10 rigidity bins × 3 species [deferred] rows. Well within memory limits.
- **Runtime**: Moving Block Bootstrap (1000 iterations) and sliding-window harmonic regression are expected to complete within 6 hours.

## Risks & Mitigations

- **Data Unavailability**: If AMS-02 or NOAA/SWPC data cannot be retrieved, the pipeline will log the error and halt. Mitigation: Use cached data if available, or document the gap in the final report.
- **Data Gaps**: Large gaps (>30 days) and small gaps (<5 days) will be excluded to avoid bias. Mitigation: Explicitly flag these periods in the output.
- **Zero Flux Events**: Excluded from ratio calculations to prevent division-by-zero. Mitigation: Log these events and report the count.
- **Data Granularity**: If daily heavy nuclei data is unavailable, the analysis will be restricted to the available time resolution (e.g., monthly), and the limitation will be explicitly stated in the results.