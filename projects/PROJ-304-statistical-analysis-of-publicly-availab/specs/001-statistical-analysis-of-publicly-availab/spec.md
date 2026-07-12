# Feature Specification: Statistical Analysis of Publicly Available Urban Noise Pollution Data

**Feature Branch**: `001-statistical-analysis-urban-noise`  
**Created**: 2026-07-06  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Urban Noise Pollution Data"

## User Scenarios & Testing

### User Story 1 - Data Aggregation and Harmonization (Priority: P1)

The system must ingest raw noise measurements from citizen science archives (e.g., NoiseTube) and municipal open data portals, then harmonize them with external covariates (traffic volume from OSM, land use from OSMnx, population density from WorldPop) into a unified spatial grid of appropriate resolution in WGS84.

**Why this priority**: Without a clean, unified dataset, no statistical modeling can occur. This is the foundational step that enables all subsequent analysis.

**Independent Test**: The pipeline can be tested by running the data ingestion script on a sample of raw CSV/GeoJSON files and verifying the output is a single GeoDataFrame with no missing coordinates and aligned coordinate reference systems.

**Acceptance Scenarios**:

1. **Given** raw noise data in mixed formats (CSV, GeoJSON) and covariate data from distinct sources, **When** the ingestion script executes, **Then** the output is a unified GeoDataFrame where every row represents a 200m x 200m grid cell with aggregated noise metrics (mean, median, 95th percentile) and matched covariates.
2. **Given** a grid cell with missing traffic data, **When** the harmonization process runs, **Then** the system either imputes the value using spatial interpolation or flags the cell as incomplete for exclusion, ensuring no null values exist in the final predictor columns used for modeling.

---

### User Story 2 - Baseline and Spatial Model Fitting (Priority: P2)

The system must fit an Ordinary Least Squares (OLS) regression model and two spatial regression models (Spatial Lag and Spatial Error) using the harmonized dataset, explicitly modeling spatial autocorrelation.

**Why this priority**: This addresses the core research question: comparing the efficacy of spatial models against a standard baseline to determine if spatial dependence is a significant factor in urban noise.

**Independent Test**: The modeling step can be tested by running the fitting script on a static subset of the data and verifying that the OLS, Lag, and Error models converge, producing coefficients and diagnostic statistics (AIC, R², Moran's I of residuals).

**Acceptance Scenarios**:

1. **Given** the harmonized dataset with noise metrics and predictors, **When** the OLS model is fitted, **Then** the system outputs regression coefficients, p-values for each predictor (traffic, land use, population), and the initial Moran's I statistic for residuals.
2. **Given** the same dataset, **When** the Spatial Lag and Spatial Error models are fitted using `PySAL`, **Then** the system outputs the spatial autoregressive parameter (λ or ρ), its p-value, and reports the Moran's I statistic and p-value for the residuals.

---

### User Story 3 - Spatial Cross-Validation and Performance Comparison (Priority: P3)

The system must perform 5-fold spatial cross-validation to prevent data leakage and compare the models using RMSE, R², and AIC to determine which approach best forecasts noise hotspots.

**Why this priority**: Standard random cross-validation is invalid for spatial data due to autocorrelation. This step ensures the performance metrics are statistically sound and the model's predictive power is genuine.

**Independent Test**: The validation step can be tested by executing the cross-validation loop and verifying that the training and test folds are spatially disjoint (no adjacent cells in train/test sets) and that performance metrics are aggregated correctly.

**Acceptance Scenarios**:

1. **Given** the fitted models, **When** 5-fold spatial cross-validation is executed, **Then** the system generates a report comparing the mean RMSE and R² across folds for OLS vs. Spatial models, AND performs a Diebold-Mariano test (or non-parametric equivalent) on the fold differences to determine if the performance difference is statistically significant (p < 0.05).
2. **Given** the cross-validation results, **When** the Akaike Information Criterion (AIC) is calculated, **Then** the system identifies the model with the lowest AIC, providing evidence for the most parsimonious model fit.

---

### Edge Cases

- **What happens when** the dataset contains grid cells with zero traffic volume or no land-use classification? **How does system handle** this? The system treats 'zero' traffic volume as a valid observed value (0) and does NOT impute it. Only 'missing' (null) data triggers imputation or exclusion as defined in US-1 Scenario 2.
- **How does system handle** extreme outliers in decibel readings (e.g., >140 dB due to sensor error)? The system must apply a robust statistical filter (e.g., interquartile range) to cap or remove outliers before modeling to prevent skewing the regression.
- **What happens when** the spatial weight matrix construction fails due to disconnected components? The system must default to a nearest-neighbor weight matrix or log a critical error and halt, preventing silent model failure.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest noise data from citizen science archives and municipal portals, and covariates from OpenStreetMap and WorldPop, harmonizing them into a 200m x 200m grid in WGS84 (See US-1).
- **FR-002**: System MUST calculate aggregated noise metrics (arithmetic mean of all readings, median, 95th percentile) per 200m x 200m grid cell to serve as the outcome variable (See US-1).
- **FR-003**: System MUST fit an Ordinary Least Squares (OLS) regression model with noise metrics as the outcome and traffic, land use, and population as predictors (See US-2).
- **FR-004**: System MUST fit Spatial Lag and Spatial Error models using `PySAL` to explicitly model spatial autocorrelation in the dependent variable and error terms (See US-2).
- **FR-005**: System MUST perform 5-fold spatial cross-validation ensuring training and test sets are spatially disjoint to prevent data leakage (See US-3).
- **FR-006**: System MUST calculate and report Moran's I for the residuals of all models to verify the removal of spatial dependence (See US-2).
- **FR-007**: System MUST compare model performance using RMSE, R², and AIC, and report the best-performing model (See US-3).
- **FR-008**: System MUST frame all findings as associational, explicitly avoiding causal language regarding environmental predictors (See US-2).
- **FR-009**: System MUST implement the Benjamini-Hochberg False Discovery Rate (FDR) correction at alpha=0.05 for testing the significance of standard covariates (traffic, land use, population) across the fitted models, to control for multiple comparisons (See US-2).
- **FR-010**: System MUST execute the entire analysis pipeline on a CPU-only environment within 6 hours, using no more than 7GB RAM, for a dataset of up to 50,000 grid cells (See US-1).

### Key Entities

- **SpatialGridCell**: Represents a 200m x 200m area in WGS84, containing aggregated noise metrics and matched covariates.
- **ModelFit**: Represents the output of a regression model (OLS, Lag, or Error), containing coefficients, standard errors, p-values, and diagnostic statistics (AIC, R², Moran's I).
- **CrossValidationFold**: Represents a single iteration of the spatial cross-validation, containing the training set, test set, and resulting performance metrics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The best spatial model achieves a Moran's I p-value > 0.05 (statistically insignificant autocorrelation) in residuals, OR achieves a reduction in the Moran's I statistic of ≥ 10% relative to the OLS baseline (See US-2).
- **SC-002**: The spatial models demonstrate a statistically significant reduction in RMSE compared to the OLS baseline (p < 0.05 via Diebold-Mariano test) (See US-3).
- **SC-003**: The spatial autoregressive parameter (λ or ρ) in the best-fitting model is statistically significant at alpha=0.05 (See US-2).
- **SC-004**: The entire pipeline executes within the 6-hour CPU-only constraint with memory usage under 7GB for up to 50,000 grid cells (See US-1).
- **SC-005**: The proportion of predictor variables found to be statistically significant (p < 0.05) after applying Benjamini-Hochberg FDR correction (See US-2).

## Assumptions

- **Assumption about data availability**: Publicly available datasets (NoiseTube, NYC Open Data, OSM, WorldPop) contain sufficient variables (traffic volume, land use, population density, noise levels) to answer the research question; if a specific variable is missing, a `[NEEDS CLARIFICATION]` will be raised.
- **Assumption about data quality**: Citizen science noise data, while potentially noisy, is sufficiently representative of urban noise patterns to yield statistically valid results after aggregation and outlier removal.
- **Assumption about spatial scale**: A 200m x 200m grid resolution is appropriate for capturing the spatial heterogeneity of urban noise without introducing excessive computational burden or spatial autocorrelation artifacts.
- **Assumption about methodological constraints**: The analysis is observational; therefore, any identified relationships are associational and do not imply causation, consistent with the lack of random assignment.
- **Assumption about computational resources**: The `PySAL` and `scikit-learn` libraries can be executed on a standard GitHub Actions free-tier runner (2 CPU cores, 7GB RAM) without requiring GPU acceleration or specialized hardware.
- **Assumption about threshold justification**: The significance threshold (p < 0.05) is a standard community default for the corrected p-values after FDR application.