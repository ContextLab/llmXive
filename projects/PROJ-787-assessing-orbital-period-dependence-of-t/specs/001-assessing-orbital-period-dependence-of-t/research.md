# Research: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Dataset Strategy

The analysis relies on three primary datasets from the Kepler Mission. As per the provided verified datasets block, **no verified URL exists for the Kepler DR25 catalog or the Input Catalog**. Therefore, the ingestion pipeline will fetch these datasets directly from the NASA MAST (Mikulski Archive for Space Telescopes) archive via `astroquery.mast`, adhering to the assumption that they are publicly accessible without special authentication.

| Dataset | Source / Loader | Variables Required | Validation Strategy |
| :--- | :--- | :--- | :--- |
| **Kepler DR25 Planet Table** | MAST Archive (`astroquery.mast`), Product ID: `kplr_dr25_planet` | `kepler_id`, `pl_radj`, `pl_radj_err1`, `pl_orbper`, `pl_orbper_err1`, `st_teff`, `st_mass`, `st_rad` | Checksum verification upon download; schema validation against `contracts/planet_record.schema.yaml`. |
| **Kepler DR25 Validation Table** | MAST Archive (`astroquery.mast`), Product ID: `kplr_dr25_validation` | `kepler_id`, `validation_efficiency` (completeness weight) | Cross-match with DR25 `kepler_id`. **Fallback**: If `validation_efficiency` is missing, pipeline defaults to unweighted analysis (weight=1.0). |
| **Kepler Input Catalog (KIC)** | MAST Archive (via DR25 cross-match or separate query) | `teff`, `mass`, `radius` (stellar) | Cross-match with DR25 `kepler_id`; exclude entries with missing stellar parameters. |

**Dataset-Variable Fit**:
The Kepler Data Release catalog contains the required planet radius and period measurements. The KIC provides the necessary stellar parameters (effective temperature, mass, radius) to refine radius estimates and compute incident flux for theoretical comparisons.
*   **Potential Mismatch**: If specific stellar parameters (e.g., `stellar_mass`) are missing for a significant portion of the sample, the analysis will proceed by excluding those planets rather than imputing, as per the spec's data hygiene requirements. This may reduce statistical power but ensures integrity.
*   **Completeness**: The analysis will apply a completeness correction using the **Kepler DR25 Validation Table** (Product ID: `kplr_dr25_validation`) via Inverse Probability Weighting (IPW) before regression, as required by the spec's assumptions. If the `validation_efficiency` column is absent, the system logs a warning and proceeds with unweighted data.

## Methodological Rationale

### 1. Gap Location Estimation (GMM vs. Synthetic Validation)
**Rationale**: The radius gap is a bimodal feature in the planet radius distribution. A simple histogram or single Gaussian fit is insufficient. A two-component Gaussian Mixture Model (GMM) is the standard robust method for identifying the valley between two overlapping populations.
*   **Initialization**: K-Means++ with multiple seeds ensures the algorithm converges to the global minimum of the likelihood function, avoiding local optima.
*   **Model Selection**: Bayesian Information Criterion (BIC) is used to compare 1-component vs. 2-component models. A BIC difference < 10 indicates the 2-component model is not significantly better, flagging the bin as "unresolved" (unimodal).
*   **Peak Separation Constraint**: Per FR-004, if the distance between the two Gaussian means is < 0.1 R_earth, the bin is flagged as "unresolved" regardless of BIC.
*   **Validation (Synthetic)**: To avoid circularity (GMM vs. KDE on same data), we implement **Synthetic Validation**. We generate synthetic bimodal datasets with *known* ground-truth gap locations. The GMM/KDE pipeline is run on these synthetic sets. The validation PASSES if the estimated gap location is within the 95% CI of the ground truth. This tests the *method's* accuracy, not just its internal consistency.

### 2. Uncertainty Quantification (Bootstrap)
**Rationale**: The gap location estimate is sensitive to the specific sample of planets in a bin.
*   **Method**: A sufficient number of bootstrap resamples (sampling with replacement) will be performed for each bin to ensure robust statistical estimation. The 2.5th and 97.5th percentiles of the resulting gap location distribution define the 95% confidence interval.
* **Feasibility**: [deferred] iterations on ~500 planets per bin is computationally trivial on a CPU-only runner.

### 3. Binning and Merging Logic
*   **Bins**: A series of log-spaced bins covering 0.7 to 2.0 log(days) (5–100 days).
*   **Merge Logic**: If a bin contains <30 planets, it is merged with the adjacent bin (left or right) that minimizes the absolute difference in log(period). The weighted mean period of the merged bin is recalculated.
*   **Power Analysis**: Before final analysis, a simulation will be run with N=30 to verify the BIC threshold's power to detect bimodality. If power is low, the threshold or bin merging strategy will be adjusted.

### 4. Slope Calculation & Theory Comparison
**Rationale**: Theoretical models (Photoevaporation vs. Core-Powered Mass Loss) predict different scaling relationships between gap radius and orbital period.
*   **Regression**: Weighted linear regression of `log(gap_radius)` vs `log(period)` (weighted by inverse variance of gap location) minimizes bias from bins with larger uncertainties.
*   **Completeness Correction**: The Kepler DR25 Validation Table (Product ID: `kplr_dr25_validation`) is used to calculate **Inverse Probability Weights (IPW)**. These weights are applied during the GMM fitting (as sample weights) and the regression to correct for Malmquist bias and detection efficiency. **Fallback**: If the column is missing, weights default to 1.0.
*   **Theoretical Distributions**: Theoretical slopes are generated via **Monte Carlo propagation of population-level stellar parameter uncertainties** (Gaussian priors based on literature means/SDs for Owen & Wu and Ginzburg et al. models). Crucially, these priors are *independent* of the specific Kepler measurements to avoid circularity (double-dipping).
*   **Hypothesis Testing**: A **z-test** is performed comparing the measured slope against the mean and standard deviation of the theoretical distribution generated via Monte Carlo propagation. The p-value is calculated based on the standard normal distribution of the z-statistic: $z = (slope_{measured} - \mu_{theory}) / \sigma_{theory}$.
*   **Multiplicity**: Since two theories are tested, a Bonferroni correction (or similar) will be applied to the p-values to control the family-wise error rate.

### 5. Collinearity Diagnostics
*   **VIF Calculation**: The Variance Inflation Factor (VIF) will be computed for predictors (log_period, stellar_mass, etc.) to detect multicollinearity. If VIF > 5, the result is flagged, and the relationship is framed as descriptive.

## Compute Feasibility Assessment

The entire pipeline is designed for a **CPU-only, 2-core, 7 GB RAM** environment:
1.  **Data Size**: The filtered Kepler dataset is < 10 MB (CSV). Loading into memory is negligible.
2.  **GMM Fitting**: `scikit-learn`'s GMM is highly optimized for CPU. Fitting 10 bins with a sufficient number of bootstraps each is well within the 6-hour limit.
3.  **No GPU**: No deep learning or large matrix operations requiring CUDA are used.
4.  **Libraries**: `pandas`, `scikit-learn`, `scipy`, `astropy`, `astroquery` are all available via CPU wheels on PyPI and do not require GPU acceleration.

## Assumptions & Limitations

- **Observational Nature**: The analysis uses observational data; correlations do not imply causation. Claims will be framed as associational.
- **Collinearity**: Orbital period and radius are treated as independent, but detection bias (Malmquist) is a confounder. The completeness correction (IPW) is the primary mitigation.
- **Power**: The 30-planet threshold per bin is a community standard but may limit power in the longest period bins. Merging adjacent bins is the fallback strategy.
- **Data Availability**: Assumes MAST archive remains accessible without rate-limiting. Retry logic with exponential backoff is implemented.
- **Theoretical Independence**: Theoretical slopes are generated from population-level priors, not specific Kepler measurements, to ensure independence.
- **Completeness Data Availability**: If the `validation_efficiency` column is missing from `kplr_dr25_validation`, the analysis proceeds unweighted. This is a known limitation that will be reported in the final results.