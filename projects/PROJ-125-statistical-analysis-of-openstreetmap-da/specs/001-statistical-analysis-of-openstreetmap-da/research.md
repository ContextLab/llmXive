# Research: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Executive Summary

This research phase validates the feasibility of using OpenStreetMap (OSM) vector data as a proxy for urban thermal characteristics and defines the statistical strategy for modeling Land Surface Temperature (LST). The primary challenge is the "dataset-variable fit": confirming that available satellite thermal data and OSM tags align with the study's requirements for 30m resolution analysis. The methodology explicitly addresses confounding, spatial autocorrelation, and memory constraints.

## Dataset Strategy

The study requires two primary data sources:
1.  **Vector Data**: OSM features (buildings, roads, vegetation) for specific city boundaries.
2.  **Raster Data**: Satellite-derived Land Surface Temperature (LST) at 30m resolution.

### Verified Datasets & Sources

Based on the project constraints and verified sources list:

| Dataset Name | Source Type | Verified URL / Loader | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **OpenStreetMap (OSM)** | Vector (API) | `overpass-api` (Programmatic) | **Verified** | Data is fetched dynamically via Overpass API (FR-001). No static URL exists; the API is the canonical source. |
| **MODIS LST** | Satellite (Raster) | AWS Open Data (Programmatic) | **Verified** | MODIS (MODA) available via AWS. Resolution ~1km. *Note: Requires aggregation/downscaling or use of Landsat.* |
| **Landsat 8/9** | Satellite (Raster) | AWS Open Data / USGS EarthExplorer | **Verified** | Landsat provides 30m thermal bands (TIRS). This is the primary source for 30m LST (FR-002). |
| **UH-I (Urban Heat Island)** | Study Data | **NO verified source found** | **Gap** | No pre-existing "UH-I" dataset URL is available. The project must *generate* this dataset from OSM + Landsat. |

**Critical Note on Dataset Fit**:
The spec requires 30m resolution. MODIS is ~1km. **Landsat 8/9 TIRS** is the required source for 30m LST.
- **Action**: The `ingest.py` module must target Landsat 8/9 thermal bands (Band 10/11) from the AWS Open Data registry.
- **Action**: OSM data will be downloaded via Overpass API for the specific city boundaries.
- **Gap**: If the spec implies a pre-packaged "UH-I" dataset, it does not exist in the verified list. The pipeline must construct the dataset from raw sources.

## Statistical Methodology

### 1. Exploratory Spatial Data Analysis (ESDA)
Before modeling, we must quantify spatial dependence.
- **Moran's I**: To test the null hypothesis of no spatial autocorrelation in LST.
  - *Method*: Global Moran's I using `pysal`.
  - *Metric*: $I$ statistic, $p$-value (permutation-based).
- **Variograms**: To characterize the range and sill of spatial dependence.
- **Correlation Matrix**: Spearman correlation between OSM covariates (building density, NDVI proxy) and LST.

### 2. Spatial Regression Models
We will fit three models as per FR-005:
1.  **Ordinary Least Squares (OLS)**: Global baseline.
    - *Assumption*: Stationarity (relationships are constant across space).
    - *Diagnostics*: Residual Moran's I, VIF (collinearity check).
2.  **Geographically Weighted Regression (GWR)**: Local parameter estimation.
    - *Mechanism*: Fits a local regression at each pixel/location using a kernel bandwidth.
    - *Bandwidth Selection*: Cross-validation (CV) or AICc minimization.
    - *Sensitivity*: FR-009 requires a sweep of bandwidth parameters to assess stability.
    - *Implementation*: `pysal`'s `GWR` module (CPU-optimized). **`mgwr` is excluded** due to memory constraints.
3.  **Spatial Lag/Error (SAR)**: Global spatial dependence modeling.
    - *Lag Model*: $y = \rho W y + X\beta + \epsilon$ (Spatial dependence in outcome).
    - *Error Model*: $y = X\beta + u, u = \lambda W u + \epsilon$ (Spatial dependence in errors).
    - *Estimation*: Maximum Likelihood Estimation (MLE) via `pysal` (`spreg`).

### 3. Validation & Inference
- **Spatial Cross-Validation**:
  - *Strategy*: Spatial blocking (5-fold). Blocks are generated using a **fixed 1km x 1km grid** over the city extent to ensure reproducibility and prevent leakage (FR-006).
  - *Metric*: RMSE, $R^2$ per fold, aggregated.
- **Multiple Comparison Correction**:
  - *Problem*: Testing significance of multiple predictors in spatial models inflates Type I error.
  - *Solution*: Apply **Effective Number of Tests (Meff)** (Li & Ji method) or **Permutation-based FDR** to account for predictor correlation.
  - *Standard Errors*: **HAC (Heteroskedasticity and Autocorrelation Consistent)** standard errors are applied to coefficients *before* p-value adjustment to ensure validity.
  - *Note*: Standard Bonferroni is **not** used as it assumes independence which is violated in spatial data.

### 4. Confounding Control & Proxy Validity (FR-010)
- **Confounding**: We will attempt to include socioeconomic proxies (e.g., population density from WorldPop if available, or OSM-based building height/complexity) as covariates to control for confounding.
  - *Limitation*: If WorldPop is unavailable, we explicitly flag this as a limitation and report the "Unexplained Variance Gap".
- **Proxy Validity (Unexplained Variance Gap)**:
  - The study acknowledges that OSM features (building density, tree cover) are incomplete proxies.
  - **Method**: Compare the observed $R^2$ of the best model against literature-derived upper bounds for OSM-only models (typically moderate).
  - **Output**: Report the "Unexplained Variance Gap" ($1 - R^2_{observed} - R^2_{literature\_max}$) to quantify the potential impact of missing factors (albedo, anthropogenic heat).
  - **Assumption Revision**: We explicitly **do not assume** OSM features are the primary drivers. The analysis tests whether they are *predictive* proxies, acknowledging that a low $R^2$ may indicate missing dominant drivers.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Addressed via Meff/Permutation FDR and HAC standard errors (FR-008).
- **Sample Size/Power**:
  - *Limitation*: Pixel-level analysis provides $N > 10,000$ per city, but spatial dependence reduces effective sample size ($N_{eff}$).
  - *Strategy*: We will report $N_{eff}$ estimates based on the variogram range. If $N_{eff}$ is low, we will acknowledge limited power for detecting weak effects.
- **Causal Inference**:
  - *Statement*: This is an **observational** study. Claims will be strictly **associational**.
  - *Identification*: No randomization. We cannot claim OSM features *cause* UHI, only that they are predictive proxies.
- **Measurement Validity**:
  - *OSM Proxies*: Building density and tree cover are standard proxies. We acknowledge they are imperfect (missing albedo, anthropogenic heat).
  - *Sensitivity*: FR-010 (Proxy Validity) and the "Unexplained Variance Gap" analysis address this.
- **Collinearity**:
  - *Risk*: Building density and impervious surface are highly correlated.
  - *Mitigation*: VIF analysis in EDA. If VIF > 5, we will report descriptive statistics rather than claiming independent effects for both.

## Model Misspecification Diagnostics

Beyond residual Moran's I, the plan includes:
1.  **Lagrange Multiplier (LM) Tests**: To distinguish between Spatial Lag and Spatial Error dependence (validating SAR choice).
2.  **Ramsey RESET Test**: To detect omitted variable bias (model misspecification).
3.  **Moran's I on Residuals**: A necessary but not sufficient condition for validity.

## Compute Feasibility Plan

- **Environment**: GitHub Actions Free Tier (multiple CPU, 7 GB RAM).
- **Strategy**:
  - **Spatial Block Sampling (Mandatory)**: Data is reduced to a maximum of **[deferred]** of spatial blocks (1km x 1km grid) for model fitting. **Random pixel sampling is strictly forbidden** as it destroys spatial structure.
  - **Memory Safety**: If $N_{samples} > 500,000$ or estimated spatial weights matrix size > 5 GB, the pipeline **automatically degrades** to OLS with HAC errors.
  - **Libraries**: Use `pysal` (CPU optimized), `scikit-learn` (CPU), `statsmodels`. Avoid deep learning frameworks.
  - **GWR**: `pysal`'s built-in GWR implementation will be used. If it fails due to memory, the pipeline degrades to OLS (no custom simplified GWR implementation).
  - **Parallelization**: Use `joblib` for spatial block cross-validation (parallelize folds across multiple cores).

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Data Volume > 7GB RAM** | Pipeline crash. | Implement **Spatial Block Sampling** (max [deferred] of blocks) for model fitting. Automatic degradation to OLS. |
| **Cloud Cover in Landsat** | Missing LST values. | Use multi-date composites (FR-002) and cloud masking algorithms. |
| **GWR Convergence Failure** | Model not fit. | Use a grid search for bandwidth with fallback to global OLS if local fit fails. |
| **Overpass API Rate Limits** | Ingestion timeout. | Retry logic with exponential backoff; cache raw OSM JSON locally. |
| **Memory Overflow in SAR/GWR** | OOM Crash. | **Automatic Fallback**: If $N > 500k$, skip SAR/GWR and run OLS only. |
| **Missing Confounds** | Spurious correlations. | FR-010 explicitly quantifies "Unexplained Variance Gap" to avoid overclaiming. |

## References

1.  **Overpass API**: https://overpass-api.de/ (Source for OSM vector data).
2.  **Landsat 8/9 on AWS**: https://registry.opendata.aws/landsat-8/ (Source for 30m Thermal data).
3.  **PySAL**: https://pysal.org/ (Spatial analysis library).
4.  **MODIS/Landsat Validation**: Cite standard remote sensing literature for LST retrieval algorithms (e.g., Jiménez-Muñoz et al., 2014).
5.  **Proxy Validity**: Literature on OSM-based UHI modeling (e.g., studies comparing OSM vs. LiDAR/Albedo data).