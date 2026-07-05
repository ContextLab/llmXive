# Research: Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

## Executive Summary

This research investigates the relationship between spatial resolution and the statistical power to detect spatial autocorrelation (Moran's I) in categorical land cover data. As resolution coarsens (30m → 480m), the spatial signal is expected to degrade due to the "modifiable areal unit problem" (MAUP) and the loss of fine-grained heterogeneity. The study quantifies the resolution threshold where power drops below the standard benchmark.

## Dataset Strategy

The study relies on the National Land Cover Database (NLCD) for the contiguous United States, specifically subsetting for Colorado.

| Dataset Name | Source Type | Verified URL | Access Method | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **NLCD 2021 (Landsat 8)** | Remote Sensing | ` | `requests` (download) | Primary source for 30m raster. Contains categorical land cover. |
| **NLCD Parquet (Training)** | Tabular/Geo | ` | `pandas.read_parquet` | Alternative source if raster download fails; contains geospatial coordinates and land cover. |
| **NLCD Group 0_9** | Tabular/Geo | ` | `pandas.read_parquet` | Alternative source; verified for geospatial attributes. |

**Selection Rationale**: The `.zip` raster file is the primary choice as it directly provides the 30m grid required for `rasterio` processing. The Parquet files serve as fallbacks if the raster format is incompatible with the specific runner environment, though the raster is preferred for spatial resampling.

**Dataset Fit Verification**:
- **Required Variable**: Categorical Land Cover (30m). **Status**: Present in NLCD.
- **Required Variable**: Spatial Coordinates. **Status**: Inherent in raster grid.
- **Gap**: No external dataset provides the *exact* pre-aggregated 60m-480m rasters; these must be generated via resampling (FR-002).
- **Gap**: No dataset provides the "spatial lag parameter" for H1 simulation; this must be **derived via Maximum Likelihood Estimation (MLE) from the observed 30m data** (see Methodology).

## Methodology

### 0. Calibration: Parameter Estimation (New)
Before running the resolution sweep, we must determine the "true" spatial structure of the data to define a valid Alternative Hypothesis (H1).
- **Step**: Sample [deferred] of the 30m binary map.
- **Method**: Use Maximum Likelihood Estimation (MLE) to estimate the spatial lag parameter ($\lambda$) that maximizes the likelihood of the observed binary spatial pattern.
- **Validation**: Generate a synthetic dataset using the estimated $\lambda$ and compare its Moran's I to the observed 30m data. The parameter is accepted only if the difference is < 5%.
- **Rationale**: This avoids arbitrary parameter selection. The H1 simulations will now represent the recovery of the *observed* 30m signal at lower resolutions, not a synthetic artifact.

### 1. Data Preprocessing
- **Ingestion**: Download NLCD 30m raster. Clip to Colorado bounding box.
- **Resampling**: Use **Nearest-Neighbor** resampling to generate 60m, 120m, 240m, and 480m rasters.
 - *Rationale*: Preserves categorical integrity (Principle VII). Avoids interpolation artifacts that would create non-integer land cover values.
- **Binarization**: Select a class of interest (e.g., "Forest" = 1, "All Others" = 0). This creates a binary indicator map required for robust Moran's I calculation on categorical data.
- **Multi-Class Check**: Repeat the process for a second distinct class (e.g., "Urban") to ensure results are not class-specific artifacts.

### 2. Statistical Framework
- **Metric**: Moran's I (Global Spatial Autocorrelation).
- **Null Hypothesis (H0)**: Random spatial arrangement.
 - *Method*: 1,000 random permutations of the binary raster values (keeping the spatial weights matrix fixed).
 - *Output*: Null distribution of Moran's I; p-value calculation.
- **Alternative Hypothesis (H1)**: Spatially clustered data with the *observed* signal strength.
 - *Method*: Generate 1,000 synthetic datasets using a **Gibbs Sampler** (binary spatial autoregressive process) with the fixed $\lambda$ derived in Step 0.
 - *Rationale*: Standard linear spatial lag models are invalid for binary data. The Gibbs sampler ensures the synthetic data respects the binary constraint (0/1) while maintaining the spatial autocorrelation structure defined by $\lambda$.
- **Power Calculation**: Power = $P(\text{Reject } H0 \mid H1 \text{ is true})$.
 - Computed as the proportion of H1 simulations where the p-value < 0.05 (after Benjamini-Hochberg correction if multiple classes tested).
 - *Note*: Power is measured as the ability to detect the *fixed* 30m signal at lower resolutions.

### 3. Multiple Comparison & Rigor
- **Multiple Testing**: Apply **Benjamini-Hochberg** correction to p-values if testing multiple land cover classes to control False Discovery Rate (FDR).
- **Collinearity**: Not applicable for a single binary map.
- **Sample Size/Power**: The "sample size" is the number of pixels. As resolution coarsens, $N$ decreases. The study explicitly measures how this reduction in $N$ and the smoothing effect of aggregation impact power.

## Decision Log

| Decision | Rationale | Impact |
|:--- |:--- |:--- |
| **Use Nearest-Neighbor Resampling** | Required by Constitution Principle VII to preserve categorical integrity. | Prevents artificial smoothing that would bias Moran's I. |
| **Use 1,000 Permutations** | Balances computational cost (6h limit) with statistical stability. | May introduce slight noise in p-values; acceptable for exploratory study. |
| **Binary Indicator Map** | Moran's I on raw categorical data is complex; binary simplifies interpretation of "presence/absence" autocorrelation. | Reduces complexity; focuses on a single ecological question. |
| **CPU-Only Execution** | Mandatory for GitHub Actions free-tier. | Limits dataset size; requires careful memory management (chunked I/O). |
| **Colorado as Study Area** | Sufficient spatial heterogeneity; manageable file size for 30m data. | Ensures runtime < 6h. |
| **Gibbs Sampler for H1** | Required for construct validity on binary data; linear lag injection is invalid. | Ensures synthetic H1 data is a realistic binary spatial process. |
| **MLE for Lambda** | Ensures H1 reflects the *observed* data structure, not an arbitrary guess. | Validity of power estimates depends on accurate signal representation. |

## Limitations & Risks

1. **Signal Strength**: If the 30m data has very weak autocorrelation, the power curve may remain flat or low across all resolutions.
 * *Mitigation*: Pilot test on a small subset first.
2. **Edge Effects**: Coarser resolutions may have fewer edge pixels, altering the weights matrix.
 * *Mitigation*: Use a consistent weights matrix generation method (e.g., Queen's case) across all resolutions.
3. **Binary Simplification**: Collapsing multi-class data to binary discards information.
 * *Mitigation*: Perform sensitivity analysis on at least two distinct classes (Forest, Urban).

## References

1. **NLCD 2021**: ` (Verified)
2. **NLCD Parquet**: ` (Verified)
3. **NLCD Group**: ` (Verified)
4. **Anselin, L. (1995)**. Local Indicators of Spatial Association—LISA. *Geographical Analysis*. (Foundational for spatial autocorrelation).
5. **LeSage, J. & Pace, R. (2009)**. *Introduction to Spatial Econometrics*. CRC Press. (For MLE and Gibbs sampling in spatial models).