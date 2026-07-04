# Research: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Executive Summary

This research validates the feasibility of using OpenStreetMap (OSM) vector data as predictors for Land Surface Temperature (LST) in urban environments. The study focuses on New York, Chicago, and Los Angeles, utilizing a high-resolution grid. The primary challenge is the "dataset-variable fit": ensuring OSM features (buildings, roads, trees) and satellite thermal data (Landsat/MODIS) are spatially aligned and temporally consistent. The plan adopts a CPU-tractable approach using `pysal` and `mgwr` libraries, avoiding GPU dependencies, and employs **stratified sampling** to fit complex spatial models (GWR/SAR) within resource constraints.

## Dataset Strategy

The analysis relies on two primary data sources. The OSM data provides urban morphology features, while satellite data provides the target variable (LST).

| Dataset Name | Source Type | Verified URL / Access Method | Variable Fit Check |
|:--- |:--- |:--- |:--- |
| **OpenStreetMap** | Vector (API) | **Overpass API** (via `overpy` library). *Note: Direct URL references to the API endpoint are dynamic; the library handles routing. No static raw URL exists for the full dataset.* | **Valid**. Contains building footprints, road networks, and tree nodes. **Caveat**: Tree nodes are point data; must be aggregated to density/area proxy (30m raster) as per FR-001. **Correction**: Missing tree data in dense cores will be imputed using Landsat-derived NDVI (see Methodological Rigor). |
| **MODIS (MOD11A1)** | Satellite (LST) | **AWS Open Data Registry**: `s3://nasa-modis/MODIS/061/MOD11A1` (via `earthaccess` or direct S3 access). | **Valid**. Provides daily LST. Used primarily for **temporal compositing** to fill Landsat gaps. **Correction**: MODIS is at a coarse native resolution; upscaling to 30m is avoided for primary analysis, used only for gap-filling via nearest-neighbor interpolation where Landsat is missing. |
| **Landsat 8 (LC08)** | Satellite (LST) | **AWS Open Data Registry**: `s3://landsat-pds/c1/L8/` (specifically Level-2 Surface Temperature products `LC08_L2SP_*`). | **Valid**. Higher resolution (30m) LST derived from TIRS Band 10. Primary source for LST. Must be filtered for daytime, summer months (Jun-Aug), and cloud cover < 50%. |
| **VIF (Validation)** | Reference (Parquet) | ` | **Not Used for Analysis**. This dataset is for reference validation of citations, not for the statistical modeling of UHI. |

**Dataset-Variable Fit Analysis**:
- **Predictors**: OSM Building Density, Road Density, Tree Node Density (Proxy), **Land-Use Covariates** (Impervious Surface Fraction).
 - *Fit*: OSM data is available for all three cities. Tree nodes are sparse in dense downtowns; the plan explicitly handles this by imputing missing values using **NDVI from Landsat** (where OSM is 0 but NDVI > threshold) to correct for underestimation in high-UHI zones.
- **Outcome**: Land Surface Temperature (LST).
 - *Fit*: Landsat surface reflectance data is available for 2018-2022. Cloud cover gaps are handled by masking pixels with >50% cloud cover. MODIS is used only to fill remaining gaps.
- **Alignment**: Both sources must be reprojected to a common CRS (e.g., EPSG:3857 or local UTM) and resampled to 30m. This is the critical step (FR-001).

**Constraint Check**: The plan avoids GPU usage. `pysal` and `mgwr` support CPU execution. Large rasters will be processed in tiles for aggregation, but **modeling is performed on a stratified sample** to fit within 7GB RAM and 6h runtime.

## Methodological Rigor

### Statistical Approach
1. **Exploratory Analysis**: Calculate Pearson/Spearman correlations and Moran's I to detect spatial autocorrelation (FR-003).
2. **Collinearity Check**: Compute Variance Inflation Factor (VIF). If VIF > 5, flag as collinear (US-2).
3. **Sampling Strategy**:
 - **Stratified Random Sampling**: Select [deferred] to [deferred] points per city, stratified by land-use class (residential, commercial, industrial, green space) to ensure representation of high-UHI zones.
 - **Rationale**: Fitting GWR/SAR on large-scale pixel datasets is O(N^2) and intractable. Sampling preserves spatial structure while ensuring computational feasibility.
4. **Modeling**:
 - **OLS**: Baseline linear model.
 - **SAR (Spatial Lag/Error)**: Accounts for global spatial dependence.
 - **GWR**: Accounts for local spatial heterogeneity (non-stationarity).
5. **Validation**: 5-fold spatial cross-validation (spatial blocks) to prevent leakage (FR-005).
6. **Inference**: Benjamini-Hochberg procedure for FDR control (FR-006).
7. **Robustness**: Sensitivity analysis on GWR bandwidth (FR-007) and **Albedo Sensitivity Analysis** (Constitution Principle VII).
8. **Hypothesis Testing**: **Toroidal Shift Permutation Test** (Spatially Restricted Permutation) to preserve spatial autocorrelation under the null.

### Addressing Specific Concerns
- **Multiple Comparisons**: All p-values for variable significance will be corrected using Benjamini-Hochberg (FR-006).
- **Sample Size/Power**: With stratified sampling (N ~ k-50k), power is sufficient for detecting effect sizes. Spatial dependence is accounted for in the model structure.
- **Causal Inference**: The data is observational. All claims will be framed as **associational** (FR-008). No randomization exists.
- **Measurement Validity**: OSM tree nodes are a proxy for canopy cover. The plan explicitly acknowledges this limitation and includes **NDVI-based imputation** for sparse areas and a **sensitivity analysis on albedo** (using land-cover derived albedo estimates) to quantify missing factor variance.
- **Predictor Collinearity**: Building density and road density are likely correlated. VIF will be calculated; if high, they will be reported descriptively, not as independent effects.
- **Spatial Permutation**: Standard permutation destroys spatial structure. We will use **toroidal shifts** (shifting the grid cyclically) to generate the null distribution, ensuring the spatial autocorrelation of the predictors is preserved.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (limited CPU, 7GB RAM, No GPU).
- **Strategy**:
 - **Data Subsetting**: Process each city independently.
 - **Tiling**: Large rasters will be split into tiles (e.g., 10km x 10km) for **aggregation** (density calculation) to avoid memory overflow.
 - **Sampling**: **Model fitting** (GWR/SAR) is performed on a stratified random sample (N ≤ 50,000) to ensure O(N^2) complexity is tractable.
 - **Libraries**: `rasterio` (streaming), `pysal` (optimized C extensions), `scikit-learn` (CPU).
 - **Runtime**: Estimated < 4 hours for full pipeline (Ingest -> EDA -> Sample -> Model -> Validate).
 - **No GPU**: No CUDA, no mixed-precision training. Models are linear/regression based, which are CPU-efficient.

## Decision Log

| Decision | Rationale | Alternative Rejected |
|:--- |:--- |:--- |
| **Use Overpass API via `overpy`** | Dynamic, up-to-date, no need to host massive vector files. | Downloading static OSM extracts is too large for 14GB disk limit. |
| **30m Resolution** | Matches Landsat 8 resolution; standard for urban studies. | 1km (MODIS native) is too coarse for building-level analysis. |
| **Stratified Sampling for GWR** | Required to fit O(N^2) models on 2 CPU cores within 6h. | Full grid fitting is intractable (days/weeks). |
| **GWR Bandwidth Selection via AICc** | Minimizes information loss; standard in `mgwr`. | Fixed bandwidth is arbitrary and may miss local patterns. |
| **Spatial CV (Blocks)** | Prevents leakage from spatial autocorrelation. | Random CV inflates R² artificially. |
| **Toroidal Shift Permutation** | Preserves spatial autocorrelation under null. | Standard permutation invalidates spatial tests. |
| **NDVI Imputation for Trees** | Corrects OSM sparsity in dense urban cores. | Ignoring sparsity leads to underestimation of cooling effect. |
