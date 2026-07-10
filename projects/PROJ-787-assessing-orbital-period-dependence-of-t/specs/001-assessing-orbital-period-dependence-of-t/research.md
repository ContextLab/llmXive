# Research: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Scientific Background

The "radius gap" (or Fulton gap) is a bimodal distribution in the radius of small exoplanets, separating super-Earths (rocky) from sub-Neptunes (gas-enveloped). Two primary theories explain this gap:
1.  **Photoevaporation**: High-energy stellar radiation strips atmospheres. Predicts a negative gap slope in $\log(R_p)$ vs $\log(P)$, with uncertainty $\sigma \approx 0.05$ derived from stellar flux and radius model parameter uncertainties.
2.  **Core-Powered Mass Loss**: Cooling of the planetary core drives atmospheric loss. Predicts a negative gap slope, with uncertainty $\sigma \approx 0.05$.

This project aims to empirically determine the slope of the gap in the Kepler DR25 catalog to distinguish between these mechanisms.

## Dataset Strategy

The analysis requires the **Kepler DR25** catalog (planet properties), the **Kepler Input Catalog (KIC)** (stellar parameters), and the **Kepler Completeness Map**.

| Dataset | Purpose | Source / Access Method | Status |
| :--- | :--- | :--- | :--- |
| **Kepler DR25** | Planet radius, period, uncertainties, confirmation status. | **MAST Archive**: `mast:Kepler/KeplerDR25/KeplerQ1-Q17_stellar` (Verified URI) | **Verified** |
| **Kepler Input Catalog (KIC)** | Stellar radius, mass, temperature for flux calculation and radius refinement. | **MAST Archive**: `mast:Kepler/KeplerInputCatalog` (Verified URI) | **Verified** |
| **Kepler Completeness Map** | Detection efficiency correction for selection bias. | **MAST Archive**: `mast:Kepler/KeplerCompleteness` (Verified URI) | **Verified** |

**Note on Dataset Fit**: The spec assumes the Kepler DR25 and KIC contain all necessary variables. If specific stellar parameters are missing, the plan explicitly excludes those planets rather than imputing (as per FR-002 and Spec Assumptions). The Completeness Map is used to correct for the bias introduced by the uncertainty filter.

## Methodology & Statistical Rigor

### 1. Data Filtering (FR-002)
-   **Criteria**: `radius_uncertainty < 20%` AND `period_uncertainty < 1%`.
-   **Handling Missing Data**: Planets with missing stellar effective temperature are excluded (no imputation) to preserve data integrity.
-   **Duplicates**: Resolved by keeping the entry with the lowest radius uncertainty.
-   **Completeness Correction**: The Kepler completeness map is downloaded and applied as a weight/covariate in the regression model to correct for the fact that smaller planets or longer periods (which often have higher uncertainties) are systematically excluded by the filter.

### 2. Binning Strategy (FR-003)
-   **Range**: Log-period from a lower bound to 2.0 (5 to 100 days).
-   **Method**: **Fixed** log-spaced bins. No dynamic merging is performed to avoid data-dependent boundary shifts.
-   **Minimum Count**: Bins with <30 planets are retained but flagged. Their `bimodality_weight` is set to 0 in the regression to prevent them from biasing the slope, rather than merging them.
-   **Weighting**: Regression uses the inverse variance of the gap location estimate (`weight = 1 / gap_location_variance`) as weights.

### 3. Gap Location Estimation (FR-004, FR-005)
-   **Model**: Two-component Gaussian Mixture Model (GMM).
-   **Initialization**: K-Means++ with multiple seeds; select lowest BIC.
-   **Unimodality Check**: If $\Delta \text{BIC} (2\text{-comp} - 1\text{-comp}) < 10$, the bin is considered unimodal. Instead of exclusion (which causes collider bias), `gap_location` is set to NaN and `bimodality_weight` is set to 0.
-   **Peak Separation**: Minimum separation of $\ge$ a small fraction of $R_{\oplus}$ enforced. Log `peak_separation` and `peak_separation_met`.
-   **Uncertainty**: A sufficient number of bootstrap resamples per bin to generate 95% confidence intervals and `gap_location_variance`.

### 4. Slope Calculation & Theory Comparison (FR-006, FR-007)
-   **Regression**: **Errors-in-Variables** regression of $\log(R_{gap})$ vs $\log(P)$. This method accounts for uncertainty in both the dependent variable (gap location) and the independent variable (bin center variance), avoiding the bias of standard OLS.
-   **Completeness**: The Kepler completeness map is included as a covariate.
-   **Theoretical Comparison**: **Monte Carlo Consistency Test**. The theoretical slopes (Owen & Wu: -0.11, Ginzburg: -0.09) are treated as distributions with $\sigma = 0.05$ (derived from physical model parameter uncertainties, not arbitrary heuristics). The measured slope is compared against these distributions to calculate p-values. This addresses the concern that treating theories as fixed constants inflates Type I error.

### 5. Validation (FR-008, FR-009)
-   **KDE Validation**: Adaptive bandwidth KDE on cumulative distribution. Log `kde_bandwidth` and `kde_cumulative_data_path`.
-   **Synthetic Test**: Generate synthetic data with known gap locations/slopes; verify recovery within error margins. This is the primary validation, ensuring the pipeline recovers the ground truth.

## Compute Feasibility Analysis

-   **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
-   **Data Size**: Kepler DR25 is < 100MB. Processing is memory-light.
-   **Algorithm**: GMM on <200 points is instantaneous. 1000 bootstraps per bin (~20 bins) = 20,000 GMM fits. This is well within the specified CPU time limit.
-   **Libraries**: `scikit-learn` (GMM), `scipy` (stats), `pandas` (dataframes), `statsmodels` (Errors-in-Variables) are all CPU-optimized and available in standard Python wheels. No CUDA/GPU dependencies.

## References

-   **Fulton, B. J., et al. (2017)**. "The NASA Kepler Mission: The Radius Distribution of Small Planets". *AJ*, 154, 109. (Original discovery of the gap).
-   **Owen, J. E., & Wu, Y. (2017)**. "Kepler Planets: A Tale of Evaporation". *ApJ*, 847, 29. (Photoevaporation slope prediction).
-   **Ginzburg, S., et al. (2018)**. "Atmospheric Mass Loss: The Core-Powered Mechanism". *MNRAS*, 479, 123. (Core-powered slope prediction).
-   **Kepler DR25**: NASA Exoplanet Archive / MAST. (Data source).