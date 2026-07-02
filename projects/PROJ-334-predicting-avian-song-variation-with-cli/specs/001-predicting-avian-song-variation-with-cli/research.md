# Research: Predicting Avian Song Variation with Climatic and Geographic Factors

## 1. Dataset Strategy

The project requires three distinct data sources: Avian Acoustic Recordings, Climate Data, and Geographic Data.

### 1.1 Verified Datasets
**CRITICAL**: The following datasets are the ONLY sources verified for this project. All data ingestion will rely on these real-world sources to ensure scientific validity.

*   **Avian Acoustic Data**:
    *   **Source**: Xeno-Canto (https://xeno-canto.org/)
    *   **Access Method**: `pyxeno` library or direct API download.
    *   **Variables**: Species name, recording location (lat/lon), audio file (metadata extraction for song metrics).
    *   **Verification**: Publicly accessible, standard format (WAV/MP3 with metadata).
*   **Climate Data**:
    *   **Source**: WorldClim v2.1 (https://www.worldclim.org/data/worldclim21.html)
    *   **Access Method**: `geopandas` / `rasterio` to extract values at specific coordinates.
    *   **Variables**: Annual mean temperature, annual precipitation.
    *   **Verification**: Standard global climate dataset, widely used in ecology.
*   **Geographic Data**:
    *   **Source**: GEBCO / OpenStreetMap (https://www.gebco.net/)
    *   **Access Method**: `rasterio` for elevation extraction.
    *   **Variables**: Elevation (meters).
    *   **Verification**: Standard global topographic dataset.

**Note**: Synthetic data is **REJECTED**. The pipeline will be built to ingest and process the real-world datasets listed above.

### 1.2 Variable Alignment Strategy
*   **Join Keys**: `species`, `location_id` (derived from lat/lon coordinates).
*   **Handling Mismatches**: Records in the acoustic dataset without a corresponding climate entry (e.g., missing climate data for a specific coordinate) will be dropped (FR-001, Edge Cases).
*   **Temporal Aggregation**: Climate data (monthly/annual) will be matched to the recording date. If exact match is unavailable, the closest temporal aggregate will be selected.

### 1.3 Data Volume Estimation
*   **Assumption**: The dataset will be filtered to a manageable size (e.g., top 20 most common species) to fit within the 7 GB RAM limit.
*   **Scaling**: If the full dataset exceeds 2 GB, a stratified random sample will be applied.

## 2. Methodological Rigor

### 2.1 Statistical Approach
*   **Primary Model**: Ordinary Least Squares (OLS) Linear Regression.
*   **Alternative**: Generalized Linear Model (GLM) with Gamma or Poisson family if residuals fail Shapiro-Wilk (p < 0.05) (FR-009).
*   **Confounders**: Geographic coordinates (lat, lon, elevation) will be included as covariates to proxy for habitat structure.
    *   **Limitation**: Coordinates are a spatial proxy, not a strict phylogenetic proxy. The plan acknowledges this limitation and frames results as "spatially adjusted associations".
    *   **Mitigation**: **Moran's I test** will be performed to detect spatial autocorrelation.
*   **Collinearity**: If |r| > 0.8 between predictors (e.g., Latitude and Temperature), PCA or Ridge Regression will be applied (FR-002).

### 2.2 Causal Diagram (DAG) and Assumptions
*   **DAG Construction**: A Directed Acyclic Graph will be constructed to visualize assumed confounders (e.g., habitat, migration).
*   **Justification**: The inclusion of climate and spatial covariates is justified based on the DAG to isolate the associational effect of climate on song variation, acknowledging that unmeasured confounders (e.g., diet) may exist.
*   **Framing**: All results will be explicitly labeled as "Associational Analysis" (FR-003).

### 2.3 Sensitivity Analysis
*   **Thresholds**: P-values {0.01, 0.05, 0.1}.
*   **Metric**: Change in R², number of significant predictors, and **effect size (Cohen's f²)**.
*   **Rationale**: Including effect size estimation addresses the limitation of p-value sweeping alone, ensuring the stability of the magnitude of the association is assessed.

### 2.4 Power and Sample Size
*   **Method**: Post-hoc power analysis using `statsmodels.stats.power`.
*   **Procedure**: After initial data ingestion, the observed variance and effect sizes will be used to calculate the achieved power for the planned sample size.
*   **Reporting**: The report will explicitly state the achieved power and acknowledge if the study is underpowered to detect small effects (f² = 0.02).

## 3. Compute Feasibility

*   **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, No GPU).
*   **Libraries**: `scikit-learn`, `statsmodels`, `pandas`, `geopandas`, `rasterio`. All are CPU-optimized.
*   **No GPU**: No `torch` with CUDA, no `bitsandbytes`.
*   **Runtime**: The pipeline (ingestion + EDA + modeling + sensitivity loop) is estimated to run in < 30 minutes for a dataset of 100k rows, well within the 6-hour limit.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Data Access Failure** | Fatal: Cannot run. | Fallback to cached data if API fails; explicit error handling. |
| **High Collinearity** | Model instability. | Automatic PCA/Ridge fallback (FR-002). |
| **Non-Normal Residuals** | Invalid p-values. | Automatic GLM switch (FR-009). |
| **Memory Overflow** | CI Job Fail. | Chunked processing or sampling if data > 2GB. |
| **Spatial Autocorrelation** | Spurious associations. | Moran's I test and spatial covariate inclusion. |