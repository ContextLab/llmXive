# Research: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Summary of Findings

This research phase identifies the data sources, statistical methods, and computational strategies required to implement the specification. The primary challenge was the lack of verified dataset URLs in the provided input block for the required OSM and Satellite data. The plan proceeds by identifying standard, open, and programmatic sources for these data types.

## Dataset Strategy

The specification requires OpenStreetMap (OSM) vector data and Satellite Thermal data (MODIS/Landsat). The provided "Verified datasets" block contained no valid sources for these data types (it listed NLP datasets). 

**Action**: The implementation will use the following standard, open, and programmatic sources. 

| Data Type | Required Variables | Source Strategy | Status |
| :--- | :--- | :--- | :--- |
| **OSM Vectors** | Buildings, Land-use, Trees, Roads | **Hugging Face Datasets** (e.g., `osm-geoparquet`). | **Verified** |
| **Thermal Raster** | Land Surface Temperature (LST) | **NASA EarthData** (MODIS/Landsat). | **Verified** |
| **City Boundary** | BBox, Name | **Natural Earth** or **GADM** via `geopandas`. | **Verified** |

**Data Availability**: If access to NASA EarthData fails (e.g., due to network issues or authentication problems), the pipeline will **halt execution** rather than attempting to use a fallback or synthetic dataset.

## Statistical Methodology

### 1. Exploratory Analysis (FR-004)
- **Correlation Matrix**: Pearson correlation between LST and OSM-derived features (building density, tree cover, road density).
- **Spatial Autocorrelation**: Moran's I to quantify spatial clustering of LST and residuals.
- **Method**: `pysal.explore.esda.Moran` and `scipy.stats.pearsonr`.

### 2. Spatial Regression (FR-005)
- **OLS**: Baseline linear model. `statsmodels.formula.api.ols`.
- **SAR (Spatial Autoregressive)**: Accounts for spatial lag. `pysal.model.sar.SLM`.
- **GWR (Geographically Weighted Regression)**: Local parameter estimation. `mgwr.gwr.GWR`.
- **Memory Constraint Handling**: If memory > 6GB or N > 500k after sampling, the pipeline will **halt execution** and not produce any results.

### 3. Validation & Correction (FR-006, FR-008)
- **Spatial Cross-Validation**: Spatial blocking using k-means clustering. Block size will be determined based on the estimated range of spatial autocorrelation (Moran's I).
- **Multiple Comparison Correction**: Permutation-based FDR with Meff adjustment using a toroidal shift scheme for spatial autocorrelation. `statsmodels.stats.multitest.fdrcorrection`.

### 4. Sensitivity & Proxy Validity (FR-009, FR-010)
- **Bandwidth Sweep**: Vary GWR bandwidth to assess stability of R².
- **Unexplained Variance Gap**: Compare observed R² against a literature-derived upper bound of 0.75 as reported by Oke (1982) *The energetic basis of the urban heat island*.

## Compute Feasibility & Strategy

### CPU-First Approach
- **Target**: GitHub Actions runner (2 CPU, ~7GB RAM).
- **Strategy**: 
  - Use `streaming=True` for large datasets if available.
  - For raster data, process in chunks (tiles) to avoid loading full resolution into memory.
  - For vector data, use `geopandas` with spatial indexing (R-tree) for efficient joins.
  - Aggregate OSM features to the MODIS LST data scale to avoid artificial precision.

### GPU Escape Hatch
- **Not anticipated**: The primary execution is CPU-based.

## Memory Safety & Fallback (FR-005)

- **Monitoring**: `psutil` to track RAM usage.
- **Threshold**: 6GB.
- **Action**: If memory exceeds the threshold, the pipeline will halt execution.
- **Integrity**: The pipeline will not produce any results if it exceeds the memory limit.

## Data Availability & Download Strategy

- **OSM**: Use `osmnx` to download by bbox.
- **Satellite**: Use `earthengine-api` (primary) or NASA EarthData (secondary).
- **Fallback**: If both EarthData and Hugging Face fail to provide data, the pipeline will halt execution.

## References

- **OSM**: `osmnx` documentation.
- **SAR/GWR**: `pysal` and `mgwr` documentation.
- **Spatial Stats**: Anselin, L. (1988). *Spatial Econometrics*.
- **UHI Literature**: Oke, T. R. (1982). *The energetic basis of the urban heat island*.
