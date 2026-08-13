# Research: Correlational Analysis of Climate‑Smart Agricultural Practices and Yield Stability Independent of Financial Access

## 1. Research Question & Hypothesis

**Primary Question**: To what extent is the intensity of Climate-Smart Agricultural (CSA) practice adoption correlated with yield stability (satellite-derived NDVI variability) and food security (HFIAS) in smallholder systems, independent of financial access?

**Hypothesis**: The intensity of CSA practice adoption is negatively correlated with NDVI variability (lower CV) and improved food security (lower HFIAS scores), independent of access to finance.
*Note: The outcome variable is defined as NDVI_CV (Coefficient of Variation = StdDev/Mean). A lower value indicates higher stability. Therefore, we expect a negative coefficient for CSA_Index.*

**Falsifiability**: The hypothesis is falsifiable. If the regression coefficient for `CSA_Index` is not statistically significant (after Bonferroni correction) or if the correlation is positive (indicating higher variability), the hypothesis is rejected.

**Observational Framing**: As an observational study using cross-sectional data, all claims are framed as **associational**. No causal inference is claimed without randomization or a specific identification strategy (e.g., IV), which is not available in this dataset configuration.

## 2. Dataset Strategy

### 2.1 Data Sources

The study requires two distinct data sources to ensure multi-source validation independence (Constitution Principle VI):
1.  **Survey Data (Predictors/Controls)**: World Bank Living Standards Measurement Study - Integrated Surveys on Agriculture (LSMS-ISA).
    *   **Target Countries**: Malawi or Tanzania.
    *   **Variables Needed**: CSA practice indicators (binary), extension visit frequency, financial access (binary/continuous), household demographics, land size.
    *   **Status**: **NO verified source found** in the provided dataset block. The World Bank LSMS-ISA data is typically accessed via a registration portal or specific download links that may require credentials.
    *   **Mitigation Strategy**: The implementation plan assumes the availability of the data via a direct download link provided by the user or the World Bank's public repository. If a direct, unauthenticated download is not possible within the CI environment, the pipeline will utilize the **Synthetic Data Generator** (`src/data/generators/synthetic_generator.py`) to create a statistically realistic mock dataset based on published LSMS-ISA summary statistics. This ensures the pipeline runs end-to-end for validation. For the final research run, real data must be manually injected.

2.  **Satellite Data (Outcomes)**: Sentinel-2 or Landsat 8/9 surface reflectance.
    *   **Target**: NDVI time-series for the growing season corresponding to the survey year.
    *   **Status**: **NO verified source found** in the provided dataset block. Sentinel-2 data is typically accessed via AWS Open Data, Google Earth Engine, or the Copernicus Data Space Ecosystem, often requiring API keys or complex authentication.
    *   **Mitigation Strategy**: Similar to LSMS-ISA, the pipeline will attempt to fetch data from a canonical public endpoint. If authentication is required, the pipeline will fallback to the **Synthetic Data Generator** to simulate NDVI time-series with realistic spatial autocorrelation and cloud cover patterns.

### 2.2 Data Availability & Feasibility

**Synthetic Fallback Strategy**:
To address the "Critical Feasibility Gap" where primary data lacks verified, directly-downloadable URLs, the pipeline implements a **Synthetic Data Generator**.
- **Function**: Generates a mock dataset with the same schema and statistical properties (means, variances, correlations) as the target LSMS-ISA/Sentinel-2 data.
- **Usage**: The pipeline runs automatically on CI with `--use-synthetic` flag if real data is missing.
- **Reproducibility**: The synthetic generation uses a pinned random seed, ensuring the same "mock" data is produced on every run.
- **Limitation**: Results from synthetic data are for **validation only** (testing the code pipeline). Final scientific claims must be based on real data injected manually.

### 2.3 Data Processing Plan

1.  **Ingestion**: Download raw CSV/Parquet for LSMS-ISA and GeoTIFF/NetCDF for Sentinel-2 (or generate synthetic).
2.  **Spatial Join**: 
    - Fuzz household coordinates (as per privacy protocols in LSMS-ISA) to a grid cell (e.g., 0.1 degree).
    - Match to the nearest Sentinel-2 pixel centroid.
    - **Temporal Stack**: For each household's location, extract NDVI values for the entire growing season (e.g., 12 months) to calculate the Coefficient of Variation.
    - *Clarification*: The study design is "cross-sectional" regarding the survey (one point in time per household), but the outcome metric (NDVI_CV) is derived from a **temporal stack** of satellite imagery within that single growing season.
3.  **Feature Engineering**:
    - **CSA Index**: Sum of binary indicators (e.g., conservation agriculture, agroforestry, irrigation) + extension visits.
    - **Financial Access**: Binary flag or continuous score from survey.
    - **NDVI_CV**: Calculated as $Standard Deviation(NDVI) / Mean(NDVI)$ over the growing season. **Higher values indicate lower stability.**
4.  **Cleaning**: Exclude households with missing coordinates or satellite data (cloud cover > 80%).

## 3. Statistical Methodology

### 3.1 Models

**Model 1 (Yield Stability)**:
$$ \text{NDVI\_CV}_i = \beta_0 + \beta_1 \text{CSA\_Index}_i + \beta_2 \text{Finance}_i + \sum \beta_k \text{Controls}_k + \epsilon_i $$
- **Dependent Variable**: NDVI_CV (Coefficient of Variation).
- **Independent Variables**: CSA Index, Financial Access, Controls (Land Size, Education, Rainfall Anomaly).
- **Error Structure**: **Cluster-Robust Standard Errors (CRSE)** clustered at the village level to account for spatial autocorrelation introduced by coordinate fuzzing.

**Model 2 (Food Security)**:
$$ \text{HFIAS}_i = \gamma_0 + \gamma_1 \text{CSA\_Index}_i + \gamma_2 \text{Finance}_i + \sum \gamma_k \text{Controls}_k + \epsilon_i $$
- **Dependent Variable**: HFIAS (Household Food Insecurity Access Scale).
- **Independent Variables**: Same as Model 1.
- **Error Structure**: Cluster-Robust Standard Errors (CRSE).

**Robustness Check: Propensity Score Matching (PSM)**:
To address the endogeneity risk between CSA adoption and Finance (wealthier farmers adopt more CSA and have better finance), a PSM analysis will be performed.
- **Method**: Nearest Neighbor Matching on covariates (Land Size, Education, Location).
- **Outcome**: Compare mean NDVI_CV between matched CSA adopters and non-adopters.

### 3.2 Statistical Rigor & Corrections

1.  **Multiple Hypothesis Correction**: 
    - Two primary tests (Stability, Food Security).
    - **Method**: Bonferroni correction.
    - **Threshold**: $\alpha_{adj} = 0.05 / 2 = 0.025$. (Note: Spec mentions $\approx 0.0167$ implying 3 tests; if interaction effects are tested, $\alpha = 0.05/3 \approx 0.0167$. The plan will implement the stricter threshold of 0.0167 to be safe).
2.  **Collinearity Check**:
    - **Method**: Variance Inflation Factor (VIF).
    - **Threshold**: VIF > 5 triggers a warning and annotation in the report.
    - **Note**: If `CSA_Index` and `Finance` are highly correlated, VIF will detect this. The plan will not remove variables arbitrarily but will report the limitation.
3.  **Sample Size / Power**:
    - Target $N > 1000$.
    - **Power Analysis**: If $N < 100$ (village level), the study is underpowered for multiple regression with 5+ predictors. In this case, the analysis will switch to a simple bivariate correlation, and the report will explicitly state the power limitation.
    - **Fallback**: If spatial overlap reduces $N$ significantly, the power to detect small effects will be low. This will be explicitly stated in the report.
4.  **Causal Assumptions**:
    - **Observational**: No randomization. Claims are strictly associational.
    - **Confounding**: Financial access is controlled for, but unobserved confounders (e.g., farmer skill, soil quality) may remain. PSM is used as a robustness check.

### 3.3 Sensitivity Analysis

- **Variable 1**: Cloud cover threshold for satellite data inclusion.
    - **Sweep**: $\{0.6, 0.7, 0.8\}$.
    - **Metric**: Variation in the magnitude and significance of $\beta_1$ (CSA Index coefficient).
- **Variable 2**: Spatial Fuzzing Radius.
    - **Sweep**: $\{0.1, 0.2\}$ degrees.
    - **Metric**: Variation in $\beta_1$ to quantify attenuation bias from spatial mismatch.
- **Output**: Table and plot showing coefficient stability across sweeps.

## 4. Compute Feasibility

- **Environment**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
- **Method**: Classical statistics (statsmodels) on sampled/streamed data.
- **GPU**: Not required. No deep learning models.
- **Time**: < 6 hours.
- **Data Handling**: 
    - If LSMS-ISA is large, stream or sample.
    - If Sentinel-2 is large, process tile-by-tile or use pre-processed NDVI products if available.
    - **No GPU escape hatch needed** as the methodology is CPU-tractable.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LSMS-ISA/Sentinel-2 Data Unavailable** | Fatal (no results) | Pipeline uses Synthetic Data Generator for CI validation. Real data must be manually injected for final results. |
| **Spatial Overlap < 300** | Low Power | Aggregate to village level. If N < 100, switch to bivariate correlation and report power limitation. |
| **High Collinearity** | Unstable Estimates | Report VIF; interpret coefficients with caution; use PSM as robustness check. |
| **Cloud Cover > 80%** | Data Loss | Exclude region; report exclusion count. |
| **Spatial Mismatch (Fuzzing)** | Attenuation Bias | Perform sensitivity analysis on fuzzing radius (0.1 vs 0.2 degrees) to quantify uncertainty. |