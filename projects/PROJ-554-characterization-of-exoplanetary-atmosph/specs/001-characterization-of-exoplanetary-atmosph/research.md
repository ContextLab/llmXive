# Research: Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques

## 1. Scientific Background & Rationale

The composition of exoplanetary atmospheres, particularly the abundance of water vapor, is a critical indicator of formation history and migration pathways. Theoretical models suggest a correlation between the equilibrium temperature of a planet and the atmospheric water abundance, driven by the condensation of water clouds and the chemistry of oxygen-bearing species. However, observational evidence is often complicated by the presence of clouds/hazes and the limited signal-to-noise ratio (S/N) of transmission spectra, leading to censored data (upper limits) rather than precise detections.

This project aims to quantify the correlation between water abundance and equilibrium temperature for two distinct populations: Hot Jupiters (gas giants with $T_{eq} > 1000$ K) and Temperate Super-Earths ($T_{eq} < 600$ K). By utilizing advanced retrieval techniques and robust statistical methods for censored data, we seek to determine if a universal trend exists or if population-specific mechanisms dominate.

## 2. Dataset Strategy

The primary data source is the **NASA Exoplanet Archive**, which aggregates transmission spectra and planetary parameters from peer-reviewed literature.

### 2.1 Verified Datasets

The following datasets are verified and will be used. No other external data sources will be introduced.

| Dataset Name | Description | Verified Source / Loader |
|:--- |:--- |:--- |
| **NASA Exoplanet Archive** | Transmission spectra (HST, Spitzer, JWST) and planetary parameters (mass, radius, $T_{eq}$, metallicity). | ` (API access) |

*Note: As per the project constraints, only the NASA Exoplanet Archive is used for the primary spectral data. No simulated datasets or alternative archives are substituted.*

### 2.2 Data Acquisition Plan

1. **Target Selection**: Query the archive for planets classified as "Hot Jupiter" or "Super-Earth" with available transmission spectra.
2. **Filters**:
 * Planet Type: `Hot Jupiter`, `Super Earth`.
 * Data Type: `Transmission Spectrum`.
 * Instrument: HST (WFC3, STIS), Spitzer (IRAC), or JWST (NIRSpec, NIRISS).
3. **Variables Extracted**:
 * Planet Name, Host Star Name.
 * Equilibrium Temperature ($T_{eq}$).
 * Host Star Metallicity ([Fe/H]).
 * Planet Mass.
 * Wavelength and Flux arrays (for retrieval).
4. **Sample Size**: Aim for a moderate sample of total planets. If the archive contains fewer than 30, the study will proceed with the available data, noting the power limitation.

### 2.3 Data Validity Checks

* **Variable Fit**: Confirm that the archive provides $T_{eq}$ and [Fe/H] for every planet with a spectrum. If a variable is missing, the planet is excluded from the multivariate regression (FR-005) but may be retained for bivariate analysis if $T_{eq}$ is present.
* **Spectral Quality**: Verify that downloaded spectra contain flux uncertainties. If uncertainties are missing, the retrieval will fail or be flagged.

## 3. Methodology

### 3.1 Atmospheric Retrieval

**Tool**: `petitRADTRANS` (CPU-optimized mode).
**Input**: Transmission spectra (wavelength, flux, uncertainty).
**Output**: Water vapor mixing ratio (log10), uncertainty (1-sigma), and model fit statistics.

* **Configuration**:
 * Opacity sources: Water (H2O), Methane (CH4), Carbon Monoxide (CO), etc.
 * Cloud model: Simple cloud deck or Rayleigh scattering.
 * Temperature profile: Isothermal or equilibrium chemistry.
* **Censored Data Handling**:
 * **Detection Limit Definition**: The detection limit for each spectrum is defined as the **3-sigma noise floor** derived from the flux uncertainty array in the raw data (independent of the retrieval result). This is an observation-specific value, not a global threshold.
 * **Censoring Logic**: If the retrieved water abundance is below this instrument-specific detection limit, the result is flagged as an **Upper Limit**.
 * **Tobit Threshold**: The detection limit value (not the retrieval uncertainty) is used as the fixed censoring point in the Tobit regression model for each observation to avoid circularity.

### 3.2 Statistical Analysis

**Goal**: Quantify the relationship between water abundance and $T_{eq}$.

1. **Correlation (FR-003, FR-004)**:
 * **Metric**: **Akritas-Theil-Sen estimator** (implemented via `lifelines` or equivalent survival analysis logic) for interval-censored data. This method correctly handles upper limits without bias.
 * **Stratification**: Separate analysis for Hot Jupiters and Super-Earths.
 * **Uncertainty**: 1000-iteration bootstrap resampling to derive 95% Confidence Intervals (CI).
 * **Hypothesis**: $H_0: \tau = 0$ vs $H_1: \tau \neq 0$.

2. **Regression (FR-005)**:
 * **Model**: Tobit Regression (Censored Normal Regression).
 * **Dependent Variable**: Water abundance (log10).
 * **Independent Variables**: $T_{eq}$, Planet Mass, Host Star Metallicity.
 * **Censoring Point**: The 3-sigma instrument detection limit for each planet (observation-specific).
 * **Output**: Coefficients, p-values, and model fit statistics (AIC/BIC).
 * **Collinearity Management**: Calculate Variance Inflation Factor (VIF) for predictors. If VIF > 5, switch to **Ridge Regression (L2 regularization)** to stabilize coefficients and prevent uninterpretable results due to the mass-metallicity correlation.

3. **Robustness Checks**:
 * **Retrieval Degeneracy Check**: Run retrieval with two different cloud model assumptions (clear vs. cloudy) for a subset of planets (e.g., [deferred]). The variance in water abundance estimates between these runs is reported as an additional uncertainty component to quantify the dependency of the result on retrieval assumptions.
 * **Power Analysis**: See Section 3.3.

### 3.3 Pre-study Power Analysis

The study targets a sample size of planets. However, a significant portion of exoplanet spectra are expected to be censored (upper limits) due to low signal-to-noise.
* **Assumed Censoring Rate**: Based on literature, we assume a moderate censoring rate for the target sample.
* **Effective Sample Size**: For N=40, censoring leaves an effective sample size of ~24 for correlation analysis.
* **Power Implications**:
 * With N=24, the power to detect a *moderate* correlation (|tau| ≥ 0.3) is approximately 0.65 (below the 0.8 threshold).
 * With N=24, the power to detect a *strong* correlation (|tau| ≥ 0.5) is approximately 0.85.
* **Conclusion**: The study is powered to detect strong correlations with 80% confidence. If the observed correlation is moderate (|tau| ~ 0.3), the result will be reported as "inconclusive due to limited power" rather than "no correlation". The target sample size of 30-45 is the maximum available from the NASA Exoplanet Archive for high-quality spectra; increasing the sample size to N=60 would be required to achieve [deferred] power for moderate correlations, but this is not feasible with current public data. This limitation is explicitly acknowledged in the final report.

### 3.4 Validation of Censoring

To ensure the "upper limit" flag reflects physical limits rather than retrieval artifacts:
1. **Synthetic Data**: Generate synthetic transmission spectra with known water abundances and noise levels using `synphot`.
2. **Retrieval Test**: Run the retrieval pipeline on these synthetic spectra.
3. **Verification**: Verify that the "upper limit" flag is triggered *only* when the known water abundance is below the defined 3-sigma noise floor. This validates the censoring logic before application to real data.

## 4. Statistical Rigor & Assumptions

* **Associational Claims**: The study explicitly frames results as associational. No causal claims are made regarding temperature driving water abundance, as the data is observational (no randomization).
* **Multiple Comparisons**: If testing multiple hypotheses (e.g., separate correlations for each instrument), a Bonferroni or Benjamini-Hochberg correction will be applied to the alpha level.
* **Measurement Validity**: Water abundances are derived from a standard retrieval code (`petitRADTRANS`) validated in literature. The detection limits are consistent with the instrument noise properties.
* **Sample Size Limitation**: With N ~ 30-45 and expected censoring, the power to detect weak correlations ($|\tau| < 0.3$) is low. This is acknowledged in the discussion.

## 5. Compute Feasibility

* **Hardware**: 2 CPU cores, 7 GB RAM.
* **Strategy**:
 * `petitRADTRANS` runs in single-threaded mode to prevent memory thrashing.
 * Data is loaded in chunks.
 * Bootstrapping is parallelized across multiple cores (250 iterations per core).
 * Total runtime estimated at several hours for 45 planets.

## 6. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use `petitRADTRANS` over other retrievers** | It is well-documented, has a Python API, and can be run in CPU mode. |
| **Tobit Regression over OLS** | OLS is biased for censored data; Tobit is the standard for upper limits. |
| **Bootstrap for CIs** | Asymptotic assumptions for Kendall's tau are weak with small N and censoring. |
| **Exclude planets with missing metallicity** | Required for the multivariate model; imputation would introduce unverified assumptions. |
| **Akritas-Theil-Sen for Correlation** | Standard Kendall's tau cannot handle interval-censored data; this method is statistically valid for upper limits. |
| **3-sigma Noise Floor for Censoring** | Provides a fixed, observation-specific censoring point independent of the retrieval model output. |
| **Ridge Regression Fallback** | Mitigates instability in coefficients if mass and metallicity are highly collinear (VIF > 5). |
| **Synthetic Validation** | Ensures that the censoring flag is a physical limit, not a retrieval failure. |
| **Retrieval Degeneracy Check** | Quantifies uncertainty due to model assumptions (cloud vs. clear). |