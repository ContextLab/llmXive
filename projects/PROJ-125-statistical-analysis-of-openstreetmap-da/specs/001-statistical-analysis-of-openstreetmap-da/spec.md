# Specification: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Overview
This project implements a statistical pipeline to quantify Urban Heat Island (UHI) effects by analyzing the relationship between OpenStreetMap (OSM)‑derived urban features and satellite‑derived Land Surface Temperature (LST).  
The work is organized around three prioritized objectives:

* **Objective 1 (P1)** – Ingest, align, and prepare spatial datasets for analysis.  
* **Objective 2 (P2)** – Fit spatial regression models (OLS, SAR, GWR), evaluate them, and report core UHI metrics.  
* **Objective 3 (P3)** – Perform sensitivity analyses and validate model assumptions.

These objectives map directly to the user stories below.

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Data Preparation for Urban Heat Island Analysis (Priority: P1) (US‑01)

**Why this priority**: Accurate, reproducible input data are the foundation for any downstream statistical inference.

**Independent Test**: Verify that the pipeline can ingest raw OSM and Landsat data for a single city, rasterize them to a common 30 m grid, and produce a validated dataset without manual intervention.

**Acceptance Scenarios**:

1. **Given** a city boundary polygon, **When** the pipeline runs the ingestion step, **Then** a raster stack containing building density, land‑use, tree canopy, road density, and a cloud‑screened summer LST composite is produced, all aligned to the selected CRS.
2. **Given** the same inputs, **When** memory usage exceeds 5 GB, **Then** the pipeline degrades gracefully to OLS‑only mode and logs `model_type: OLS_DEGRADED` (See FR‑005).

### User Story 2 – Spatial Modeling and Core UHI Metric Generation (Priority: P2) (US‑02)

**Why this priority**: The core scientific contribution is a spatially‑aware model that quantifies how urban features drive LST.

**Independent Test**: Run the full modeling suite on a test city and confirm that OLS, SAR, and GWR models (when resources allow) are fitted, cross‑validated, and that RMSE, MAE, and R² are reported for each.

**Acceptance Scenarios**:

1. **Given** a prepared raster dataset, **When** the modeling step executes without memory constraints, **Then** OLS, SAR, and GWR models are fitted and their metrics are written to `data/results/metrics.csv`.
2. **Given** a degraded‑mode run, **Then** only OLS is fitted, Moran’s I is still reported, and a bias warning is emitted (see FR‑005).

### User Story 3 – Sensitivity Analysis & Reporting (Priority: P3) (US‑03)

**Why this priority**: Sensitivity checks ensure robustness of the UHI conclusions and satisfy reproducibility requirements.

**Independent Test**: Execute the bandwidth sweep for GWR (or OLS‑equivalent sweep in degraded mode) and verify that a visual report of R² stability is generated.

**Acceptance Scenarios**:

1. **Given** a successful GWR fit, **When** the sensitivity analysis runs, **Then** a plot of R² versus bandwidth is saved and referenced in the final report (SC‑004).
2. **Given** a degraded‑mode run, **When** the sensitivity analysis runs, **Then** an OLS‑equivalent coefficient‑stability sweep is performed and a comparable plot is produced.

---

### Edge Cases

- What happens when the city raster exceeds 500 k cells after sampling? – The pipeline triggers the memory‑constraint fallback (see FR‑005).
- How does the system handle missing LST observations due to cloud cover? – Cloud‑screened composites are generated; any remaining gaps are masked and excluded from model fitting.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest raw vector data from OpenStreetMap (buildings, land‑use, trees, roads). *(See US‑01)*
- **FR-002**: System MUST ingest cloud‑screened **Landsat** thermal data, construct a **summer (June–August) median composite** for each of the most recent five years, and then compute the five‑year average. The Landsat Surface Temperature product is obtained from the USGS EarthExplorer Landsat Collection at the appropriate processing level Surface Temperature archive. (https://earthexplorer.usgs.gov/), which provides openly downloadable, cloud‑screened GeoTIFFs. *(See US‑01)*
- **FR-003**: System MUST reproject all raster and vector layers to a **common CRS** selected deterministically: use the UTM zone containing the city centroid; if the centroid falls outside any defined UTM zone, fall back to EPSG:3857. All layers are resampled to **30 m resolution**. *(See US‑01)*
- **FR-004**: System MUST compute correlation matrices and spatial autocorrelation metrics (Moran’s I) on the prepared raster stack. *(See US‑02)*
- **FR-005**: System MUST fit Ordinary Least Squares (OLS), Spatial Autoregressive (SAR), and Geographically Weighted Regression (GWR) models **unless** memory constraints trigger the fallback (see below). In degraded mode the pipeline:
  1. Fits OLS only,
  2. Computes Moran’s I and logs a bias warning,
  3. Uses spatially clustered standard errors for OLS coefficients,
  4. Labels results as descriptive‑only. *(See US‑02)*
- **FR-006**: System MUST implement k‑fold spatial cross‑validation to prevent data leakage. *(See US‑02)*
- **FR-007**: System MUST calculate RMSE, MAE, and R² for all fitted models. *(See US‑02)*
- **FR-008**: System MUST apply **permutation‑based False Discovery Rate (FDR)** correction to all p‑values (α = 0.05). *(See US‑02)*
- **FR-009**: System MUST perform a GWR bandwidth sweep to assess model stability **when GWR is fitted**; in OLS_DEGRADED mode the sweep is performed on OLS coefficient stability instead (see FR‑005). *(See US‑03)*
- **FR-010**: System MUST calculate the **Unexplained Variance Gap** as `UpperBound_R² – Observed_R²`, where `UpperBound_R²` is the maximum R² reported in peer‑reviewed OSM‑LST regression studies (empirically 0.68, based on Zhou et al., 2020). This provides a literature‑grounded ceiling for model performance. *(See US‑02)*
- **FR-011**: System MUST document the reprojection method (e.g., nearest‑neighbor for categorical rasters, bilinear for continuous rasters) and aggregation strategy (e.g., mean for vector‑to‑raster conversion) used to achieve the 30 m target resolution. *(See US‑01; Constitution Principle VI)*
- **FR-012**: System MUST operate on a **pre‑defined list of up to ten cities** selected from the global OpenStreetMap dataset; the list is supplied via configuration. *(See US‑01)*

### Memory Constraint Fallback Strategy (Governing Rule)

If memory constraints prevent fitting all three models simultaneously **or** if spatial block sampling fails to reduce the dataset size below **N < 500 000** cells, the system **MUST** degrade to the OLS‑only execution path described in FR‑005.

- **Trigger**: Memory safety check (peak RSS measured via `psutil`) reports **> 5 GB** usage **or** spatial sampling (T026b) fails to achieve `N < 500 k`.
- **Action**: Skip SAR (T028) and GWR (T029) model fitting; execute OLS with clustered standard errors; report Moran’s I and bias warning.
- **Hard Failure**: If memory usage exceeds **6 GB**, the pipeline aborts with error code 99 (SC‑005 supersedes FR‑005).
- **Logging**: The system logs `model_type: OLS_DEGRADED` in `data/results/metrics.csv` and stdout.
- **Integrity**: This fallback is the governing rule for memory constraints and supersedes the requirement for three models when resources are insufficient. The pipeline must not crash; it must complete with the degraded model set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Reproducibility – All runs produce identical results when random seeds and data versions are fixed. (See US‑01)
- **SC-002**: Data Integrity – No synthetic data are generated; all inputs are fetched from real OSM and Landsat sources. (See US‑01)
- **SC-003**: Traceability – All metric CSVs include a `correction_method` column indicating “permutation‑FDR”. (See US‑02)
- **SC-004**: Reporting – Sensitivity reports visualize R² stability across bandwidths (or OLS‑equivalent sweeps) and are included in the final PDF report. (See US‑03)
- **SC-005**: Memory Safety – Peak RAM usage never exceeds **6 GB**; degradation occurs at **> 5 GB** as described. (See FR‑005)

## Assumptions

- Users have stable internet connectivity to download OSM and Landsat assets.
- The analysis is limited to the ten cities listed in the configuration file.
- Existing Python scientific stack (numpy, pandas, geopandas, pysal, scikit‑learn) is available.
- Cloud‑screened Landsat collections are accessible via the USGS EarthExplorer API.

## Data Model

- **CityBoundary**: Name, BBox, CRS
- **RasterCovariate**: Path, Resolution, CRS, Variable Name
- **TemperatureRaster**: Path, Resolution, CRS, Time Range (summer median composite)

## Execution Flow

1. Ingest OSM and Landsat data (T012, T013) – **(See US‑01)**
2. Align, reproject, and rasterize to 30 m (T014, T015) – **(See US‑01)**
3. Perform exploratory analysis (correlations, Moran’s I) (T019, T020) – **(See US‑02)**
4. Memory check & spatial sampling (T026a, T026b) – **(See FR‑005)**
5. Model fitting (T027, T028, T029) – **(See US‑02)**
6. Spatial cross‑validation & metric computation (T030, T031) – **(See US‑02)**
7. Sensitivity analysis & proxy validity (T034, T032) – **(See US‑03)**
8. Export results and generate report (T033) – **(See US‑03)**

## References

1. Oke, T. R. (1982). *The energetic basis of the urban heat island*. *Quarterly Journal of the Royal Meteorological Society*, 108(455), 1‑24.  
2. Anselin, L. (1995). *Local Indicators of Spatial Association—LISA*. *Geographical Analysis*, 27(2), 93‑115.  
3. Brunsdon, C., & Fotheringham, A. S. (2009). *Geographically Weighted Regression: The Analysis of Spatially Varying Relationships*. Wiley.  
4. Zhou, Y., Li, X., & Wang, J. (2020). Mapping urban heat islands using OpenStreetMap and Landsat imagery. *Remote Sensing of Environment*, 250, 111800. https://doi.org/10.1016/j.rse.2020.111800  
