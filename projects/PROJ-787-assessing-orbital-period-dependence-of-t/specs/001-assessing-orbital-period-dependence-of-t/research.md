# Research: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## 1. Problem Statement
The exoplanet radius gap (a deficit of planets between approximately two Earth radii) is a key diagnostic of planet formation and evolution. Two leading theories—photoevaporation and core-powered mass loss—predict different slopes for the location of this gap as a function of orbital period. This project aims to measure this slope from Kepler data and statistically distinguish between the theories using robust, non-parametric methods.

## 2. Dataset Strategy

### 2.1 Verified Sources
The analysis relies on three primary datasets from the NASA MAST archive. Per the project constraints, these are the *only* sources used.

| Dataset | Description | Access Method | Status |
| :--- | :--- | :--- | :--- |
| **Kepler DR25 Planet Catalog** | Confirmed planet candidates with radius, period, and uncertainties. | Direct HTTPS download from MAST (canonical path). | **Available** (Assumed accessible per Spec Assumption). |
| **Kepler Input Catalog (KIC)** | Stellar parameters (radius, mass, temp) for host stars. | Direct HTTPS download from MAST. | **Available** (Assumed accessible per Spec Assumption). |
| **Kepler Completeness Map** | Detection efficiency model for completeness correction. | Direct download from MAST/Kepler archive. | **Required** (Per Spec Assumption). |

*Note: The "Verified datasets" block in the prompt contained only NLP/LLM datasets (GMM, CPU-only) which are irrelevant to exoplanet astronomy. As per the instruction "If the block says a dataset has NO verified source, describe the dataset by name but do NOT fabricate a URL", we describe the Kepler catalogs but do not invent a fake URL. The implementation will use the official MAST API or direct HTTPS links to the known archive locations.*

### 2.2 Variable Fit & Constraints
- **Required Variables**: `radius`, `radius_uncertainty`, `period`, `period_uncertainty` (from DR25); `stellar_radius`, `stellar_mass`, `stellar_temp` (from KIC).
- **Completeness Weighting**: The Kepler Completeness Map is joined to the dataset to assign a `completeness_weight` to each planet. This is mandatory to correct for Malmquist bias.
- **Fit Check**: The Kepler DR25 catalog is known to contain these variables. If specific stellar parameters are missing for a star, the corresponding planet will be **excluded** (no imputation), adhering to the spec's data hygiene requirements.
- **Dataset Mismatch**: No mismatch expected for the core variables. If the DR25 catalog lacks a specific derived variable (e.g., incident flux) required for the theoretical comparison, it will be computed from the base variables (Radius, Temp) if possible, or the bin will be flagged.

## 3. Methodological Rigor

### 3.1 Statistical Approach
1.  **Binning**: Log-spaced bins spanning a range of days. Minimum 30 planets per bin (merge if <30).
2.  **Gap Detection (GMM)**:
    -   Two-component Gaussian Mixture Model.
    -   Initialization: K-Means++ with multiple seeds; select lowest BIC.
    -   **Quality Control**: BIC difference (2-comp vs 1-comp) > 10 required. If BIC(2) < BIC(1) or GMM fails to converge, the bin is flagged as **'UNRESOLVED'** and **excluded** from the regression step to prevent noise-driven artifacts. This is a reliability gate, not a validation of the gap's existence (which is the hypothesis being tested).
    -   Uncertainty: **1000+ bootstrap resamples** for gap location uncertainty.
3.  **Validation (Synthetic Ground Truth)**:
    -   **Primary Validation**: Generate synthetic data with a *known* gap location and slope. Run the full GMM pipeline. The validation PASSES if the measured gap location matches the ground truth within the estimated 95% CI. This avoids circularity of comparing GMM to KDE on the same data.
    -   **Internal Consistency**: Compare GMM gap vs KDE gap (scaled uncertainty threshold: `|gap_gmm - gap_kde| <= 2 * sqrt(σ_gmm^2 + σ_kde^2)`). This ensures the threshold scales with the measurement precision of the specific bin.
4.  **Regression**:
    -   Weighted linear regression of Gap Radius vs Log(Period) on 'PASS' bins only.
    -   **Errors-in-Variables**: The regression accounts for uncertainty in the X-variable (period) to mitigate regression dilution bias.
    -   **Binning Bias Mitigation**: Perform a sensitivity check by re-running with varied bin widths to ensure the slope is robust to binning choices.
    -   Weights: Inverse variance of gap location estimates.
5.  **Theory Comparison**:
    -   **Monte Carlo**: Propagate stellar uncertainties AND **model parameter priors** (e.g., core mass distribution, metallicity) to generate theoretical slope distributions for Photoevaporation (Owen & Wu) and Core-Powered Mass Loss (Ginzburg et al.). This ensures the theoretical distribution reflects model uncertainty, not just measurement error.
    -   **Comparison**: Use a **Permutation Test / Overlap Integral** to compare the measured slope distribution against the theoretical distributions. This avoids the invalid assumption of a fixed null mean required by a Z-test.
    -   **Multiplicity**: Bonferroni correction applied for multiple comparisons (2 theories).

### 3.2 Compute Feasibility (CPU-Only)
-   **Constraints**: 2 CPU cores, ~7 GB RAM, ≤ 6 hours.
-   **Strategy**:
    -   **Data Flow**: Raw Kepler DR25 (large) is **streamed and filtered immediately** to <100MB *before* any GMM fitting or bootstrapping. The "expected <100MB" refers to the *cleaned* dataset. Chunking is only used during the initial stream, not for the GMM step.
    -   Use `scikit-learn` (CPU optimized) for GMM.
    -   Use `numpy` vectorized operations for bootstrapping (avoid Python loops where possible).

### 3.3 Limitations & Assumptions
-   **Observational Nature**: Findings are associational.
-   **Collinearity**: Period and Radius are treated as independent, but Malmquist bias is addressed via completeness correction (as per Spec Assumption). VIF will be computed.
-   **Power**: The 30-planet threshold is assumed sufficient for GMM stability.
-   **Circularity**: The internal KDE comparison is a consistency check. The primary validation of accuracy comes from the **Synthetic Ground Truth** validation (Phase 3).

## 4. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Exclude missing stellar params** | Imputation introduces unverified bias; exclusion ensures data integrity (Spec US-1). |
| **Merge bins < 30 planets** | Ensures statistical power for GMM; prevents overfitting on sparse data (Spec US-2). |
| **Use BIC for model selection** | BIC penalizes complexity; prevents overfitting to noise compared to AIC (Spec US-2). |
| **Bonferroni correction** | Controls family-wise error rate when testing two competing theories (Spec Assumption). |
| **Exclude 'UNRESOLVED' bins** | Prevents noise-driven artifacts from unimodal or noisy bins from biasing the regression. |
| **Permutation Test** | Methodologically valid for comparing two distributions with uncertainty; avoids Z-test pitfalls. |
| **Scaled Validation Threshold** | Ensures validation metric scales with measurement precision, avoiding arbitrary constants. |
| **Synthetic Ground Truth** | Provides independent accuracy check, avoiding circularity of internal KDE comparison. |
