# Feature Specification: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

**Feature Branch**: `001-urban-heat-osm`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Rasterization (Priority: P1)

The system must ingest raw vector data from OpenStreetMap (OSM) and satellite thermal imagery (MODIS/Landsat) for selected cities, align them to a common coordinate reference system (CRS), and generate aligned 30m resolution raster covariates and target variables.

**Why this priority**: This is the foundational step; without aligned, high-quality data, no statistical modeling can occur. It delivers the primary dataset required for all subsequent analysis.

**Independent Test**: Can be fully tested by running the data pipeline for a single city (e.g., New York) and verifying that the output GeoTIFFs have matching dimensions, CRS, and non-null values in the overlap region.

**Acceptance Scenarios**:

1. **Given** a city boundary shapefile and OSM raw data, **When** the ingestion script runs, **Then** a rasterized GeoTIFF for building density is created with a 30m resolution and valid CRS.
2. **Given** raw MODIS/Landsat thermal data, **When** the ingestion script runs, **Then** a land-surface temperature raster is generated covering the same extent as the OSM covariates.
3. **Given** multiple input sources, **When** the alignment process completes, **Then** all output rasters share identical dimensions, origin, and CRS, allowing direct pixel-wise stacking.

---

### User Story 2 - Exploratory Spatial Analysis and Autocorrelation Check (Priority: P2)

The system must perform exploratory data analysis (EDA) to quantify relationships between OSM-derived features and temperature, including calculating correlation matrices, variograms, and spatial autocorrelation metrics (Moran's I).

**Why this priority**: This step validates the data quality and informs the choice of statistical models (e.g., confirming the need for spatial regression). It provides immediate scientific insight into the raw data.

**Independent Test**: Can be tested by running the EDA module on the aligned rasters and verifying the generation of a correlation matrix and a Moran's I statistic report.

**Acceptance Scenarios**:

1. **Given** the aligned raster stack, **When** the EDA module runs, **Then** a Pearson/Spearman correlation matrix between covariates and temperature is generated.
2. **Given** the temperature raster, **When** the spatial analysis runs, **Then** a variogram is computed and a Moran's I statistic is reported to quantify spatial autocorrelation.
3. **Given** the analysis results, **When** the report is generated, **Then** it includes a summary of the strength and direction of linear relationships between key predictors (e.g., vegetation, impervious surface) and temperature.

---

### User Story 3 - Spatial Regression Modeling and Validation (Priority: P3)

The system must fit multiple spatial regression models (OLS, GWR, SAR) to predict temperature from OSM features, perform spatial cross-validation to prevent leakage, and evaluate performance using RMSE and R².

**Why this priority**: This delivers the core research output: the predictive model and its validation. It tests the hypothesis that OSM data can predict UHI effects.

**Independent Test**: Can be tested by executing the modeling pipeline on the dataset, ensuring models are trained, cross-validated using spatial blocks, and that performance metrics are logged.

**Acceptance Scenarios**:

1. **Given** the prepared dataset, **When** the modeling pipeline runs, **Then** an Ordinary Least Squares (OLS) baseline model is fitted and its coefficients are recorded.
2. **Given** the dataset and OLS results, **When** the spatial modeling step runs, **Then** a Geographically Weighted Regression (GWR) and/or Spatial Lag/Error (SAR) model is fitted.
3. **Given** the fitted models, **When** the validation step runs, **Then** a 5-fold spatial cross-validation is performed, and RMSE and R² metrics are reported for each model.

### Edge Cases

- **Missing Data**: If the percentage of missing data (null values) in a city boundary exceeds **[deferred]**, the system MUST log a WARNING message to stdout and continue processing with a masked dataset. If missing data is ≤10%, the system proceeds without warning.
- **Cloud Cover**: If the cloud cover percentage for a satellite scene exceeds **[deferred]**, the system MUST generate a multi-date composite to ensure valid temperature values. If cloud cover is ≤20%, the system MUST exclude pixels with cloud flags and use the single-date composite.
- **Resolution Mismatch**: If the OSM data resolution is insufficient for 30m rasterization (requiring upsampling), the system MUST use bilinear interpolation for continuous data and nearest neighbor for categorical data. If the upsampling error exceeds **0.1** (calculated as the absolute difference between the original vector area and the rasterized area), the system MUST log an ERROR message to stderr and exit with code 1.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download OSM vector data (buildings, land-use, trees, roads) via the Overpass API for specified city boundaries. (See US-1)
- **FR-002**: System MUST ingest satellite thermal data (MODIS/Landsat) and compute daytime land-surface temperature composites for the most recent 5-year period available. (See US-1)
- **FR-003**: System MUST reproject all raster layers to a common CRS and resample them to a uniform 30m resolution. (See US-1)
- **FR-004**: System MUST calculate spatial autocorrelation (Moran's I) and variograms for the target temperature variable. (See US-2)
- **FR-005**: System MUST fit at least three distinct spatial models: Ordinary Least Squares (OLS), Geographically Weighted Regression (GWR), and a Spatial Lag/Error model (SAR). (See US-3)
- **FR-006**: System MUST perform 5-fold spatial cross-validation using spatial blocks to prevent data leakage. (See US-3)
- **FR-007**: System MUST report model performance metrics (RMSE, MAE, R²) for each fitted model AND output adjusted p-values for all predictors. (See US-3)
- **FR-008**: System MUST apply multiple-comparison correction (e.g., Bonferroni or FDR) to predictor significance using spatially robust standard errors (e.g., HAC) or permutation-based inference. (See US-3)
- **FR-009**: System MUST conduct a sensitivity analysis on the spatial bandwidth parameter for GWR, sweeping over a configurable set of values defined in the implementation plan to assess stability. (See US-3)

### Key Entities

- **CityBoundary**: Defines the spatial extent of the study area (e.g., New York, Chicago).
- **RasterCovariate**: A 30m resolution grid representing an OSM-derived feature (e.g., building density, tree canopy).
- **TemperatureRaster**: A 30m resolution grid representing land-surface temperature.
- **SpatialModel**: A statistical object containing coefficients, diagnostics, and performance metrics.
- **CrossValidationFold**: A partition of the data used for spatially blocked validation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system MUST output the proportion of variance explained (R²) by the best spatial model. (See FR-007)
- **SC-002**: The system MUST output the Root Mean Square Error (RMSE) for both the GWR and OLS models. (See FR-007)
- **SC-003**: The system MUST output adjusted p-values for all predictors after multiple-comparison correction. (See FR-008)
- **SC-004**: The stability of the GWR bandwidth parameter is measured by the variation in R² across the sensitivity sweep. (See FR-009)
- **SC-005**: The system MUST output the Moran's I value for model residuals to quantify remaining spatial autocorrelation. (See FR-004)

## Assumptions

- The OpenStreetMap data for the selected cities contains sufficient detail (building footprints, land-use tags) to derive meaningful 30m resolution covariates.
- MODIS/Landsat thermal data for the most recent 5-year period is available via AWS Open Data and can be downloaded without excessive bandwidth costs or time delays.
- The computational environment (GitHub Actions free tier) provides sufficient CPU and memory (≤7 GB RAM) to process the rasterized data for 3 cities without out-of-memory errors.
- The relationship between OSM features and temperature is primarily linear or locally linear, making GWR and SAR models appropriate.
- Cloud cover in satellite imagery is sufficiently low in the selected summer months to allow for valid temperature composites.
- The "spatial blocks" cross-validation strategy is feasible to implement given the raster grid structure.
- No GPU acceleration is available; all models must run in default precision on CPU.
- The dataset variables (building density, impervious surface, tree cover) are the primary drivers of UHI at the 30m scale, and other factors (albedo, anthropogenic heat) are secondary or correlated with these proxies.