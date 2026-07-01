# Feature Specification: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

**Feature Branch**: `001-bird-migration-climate-correlation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST ingest raw eBird Basic Dataset (EBD) records and NOAA/PRISM climate data, filter them to migratory species and the 2020–2024 period, and aggregate them into a unified, grid-aligned dataset (0.5° × 0.5° cells) with computed phenology metrics (first arrival, median arrival, stopover duration) and seasonal climate averages.

**Why this priority**: Without a clean, aligned, and reproducible dataset, no statistical modeling or hypothesis testing can occur. This is the foundational step that enables all subsequent analysis.

**Independent Test**: The pipeline can be fully tested by running the ingestion and preprocessing scripts on a subset of data (e.g., one species, one region) and verifying that the output CSV contains the expected columns (species, grid_cell, week, phenology_metric, climate_temp, climate_precip) with no missing values in critical fields.

**Acceptance Scenarios**:

1. **Given** raw eBird and NOAA files are available in the input directory, **When** the preprocessing script is executed with the 2020–2024 filter, **Then** the output dataset contains a minimum of 208 weeks ([deferred] coverage) of data per grid cell for the specified migratory species, with phenology metrics calculated for at least [deferred]% of species-year combinations.
2. **Given** a species with sparse observations in a specific grid cell, **When** the aggregation logic runs, **Then** that cell is marked as "insufficient data" rather than generating a false phenology metric, and the cell is excluded from downstream modeling.

---

### User Story 2 - Phenology-Climate Correlation Modeling (Priority: P2)

The system MUST fit Generalized Additive Mixed Models (GAMMs) to quantify the association between phenology metrics and climate variables (temperature, precipitation, extreme weather indices), incorporating species-level random slopes and accounting for spatial autocorrelation via Moran’s I diagnostics and a Gaussian Process (GP) random effect with a Matérn covariance function.

**Why this priority**: This is the core analytical engine that directly addresses the research question. It transforms the preprocessed data into statistical evidence of climate sensitivity.

**Independent Test**: The modeling step can be tested by running the GAMM script on a synthetic dataset with known correlation parameters and verifying that the output includes coefficient estimates, p-values, and model fit statistics (e.g., R², AIC) that match the known parameters within a 5% tolerance.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset for a single species, **When** the GAMM is fitted with spring temperature as a smooth fixed effect, **Then** the output includes a p-value and the system flags the result as significant if p < 0.05 after FDR correction, and the model converges within 600 seconds.
2. **Given** a dataset with high spatial autocorrelation, **When** Moran’s I is computed on the model residuals, **Then** the system flags the model if Moran’s I > 0.15, indicating unmodeled spatial structure, and triggers a re-fit with a Gaussian Process (GP) random effect using a Matérn covariance function.

---

### User Story 3 - Route Shift Analysis and Uncertainty Quantification (Priority: P3)

The system MUST represent weekly migration centroids as trajectories on a Riemannian manifold, apply manifold-based trajectory statistics to detect spatial route shifts, and generate uncertainty intervals for temporal phenology shifts using bootstrapped confidence intervals.

**Why this priority**: This extends the analysis beyond simple timing to spatial route changes and provides robust uncertainty estimates, addressing the "routes" component of the research question and the need for reliable confidence intervals. The Riemannian approach is essential for detecting non-linear spatial shifts that linear methods miss.

**Independent Test**: The route analysis can be tested by running the trajectory module on a synthetic dataset with randomized labels (null hypothesis) and verifying that the permutation test correctly identifies no significant shift (p > 0.05) in the absence of true signal.

**Acceptance Scenarios**:

1. **Given** weekly centroid coordinates for a species, **When** the Riemannian trajectory analysis is executed, **Then** the output includes a shift vector (magnitude and direction) and a p-value derived from 10,000 permutation shuffles, with the computation completing in ≤ 1800 seconds.
2. **Given** a set of model predictions, **When** the bootstrapped confidence intervals are aggregated, **Then** the 95% confidence interval width is [deferred] days for the predicted phenology shift, ensuring adequate precision for ecological interpretation.

---

### Edge Cases

- What happens when a species has insufficient data in a grid cell to compute a phenology metric? **System handles this by marking the cell as "insufficient data" and excluding it from modeling, with a log entry recording the species, grid cell, and reason.**
- How does the system handle missing climate data for a specific grid cell and week? **System imputes missing values using spatial interpolation from neighboring cells (within 1° radius) and flags the imputed cells in the output metadata.**
- What if the GAMM fails to converge for a species due to collinearity? **System logs the failure, skips the species for that model, and proceeds to the next one, ensuring the pipeline does not halt.**

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and cache eBird Basic Dataset (EBD) for North America (2020–2024) and NOAA/PRISM climate data, ensuring all files are stored in a versioned directory structure (See US-1).
- **FR-002**: System MUST filter eBird records to migratory species using the Cornell Lab of Ornithology list and aggregate observations to weekly counts per 0.5° × 0.5° grid cell (See US-1).
- **FR-003**: System MUST compute phenology metrics (first arrival, median arrival, stopover duration) and seasonal climate averages (March–May temperature, precipitation) for each grid cell and species-year combination (See US-1).
- **FR-004**: System MUST fit Generalized Additive Mixed Models (GAMMs) with phenology metrics as responses, climate variables as smooth fixed effects, and species-year random intercepts/slopes (See US-2).
- **FR-005**: System MUST perform permutation tests (10,000 shuffles) and apply Benjamini–Hochberg FDR correction to all species-climate coefficients to control false discovery rate (See US-2).
- **FR-006**: System MUST represent weekly migration centroids as trajectories on a Riemannian manifold and apply manifold-based trajectory statistics to detect spatial route shifts (See US-3).
- **FR-007**: System MUST generate 95% confidence intervals for model predictions using bootstrapped resampling of the centroid estimation process to quantify uncertainty (See US-3).

### Key Entities

- **MigrationRecord**: Represents a single bird observation with attributes: species, latitude, longitude, date, count, checklist ID.
- **PhenologyMetric**: Represents a computed metric for a species-grid cell-week combination with attributes: species, grid_cell, week, first_arrival_date, median_arrival_date, stopover_duration.
- **ClimateVariable**: Represents a climate measurement for a grid cell-week combination with attributes: grid_cell, week, mean_temperature, total_precipitation, extreme_weather_index.
- **Trajectory**: Represents a sequence of weekly centroids for a species-year with attributes: species, year, weekly_centroids (list of lat/lon pairs), shift_vector.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The statistical power and effect size stability of the phenology-climate association tests are measured against the total number of migratory species present in the filtered dataset (See US-2).
- **SC-002**: The proportion of grid cells with "insufficient data" after preprocessing is measured against the target of [deferred]% of total cells (See US-1).
- **SC-003**: The convergence rate of GAMMs (successful fits / total attempts) is measured against the target of [deferred]% (See US-2).
- **SC-004**: The width of 95% confidence intervals from the bootstrapped ensemble is measured against the target of [deferred] days for phenology shift predictions (See US-3).
- **SC-005**: The total runtime of the analysis pipeline (download → preprocess → model → visualize) is measured against the CI runner time limit defined in Assumptions (See Assumptions).

## Assumptions

- **Assumption about data availability**: The eBird Basic Dataset and NOAA/PRISM climate data for 2020–2024 are publicly accessible and can be downloaded within the CI runner time limit without authentication issues.
- **Assumption about computational resources**: The analysis will run on a standard computational environment capable of handling GAMMs and permutation tests; specific hardware constraints are not hardcoded to allow for scalable execution.
- **Assumption about statistical validity**: The Benjamini–Hochberg FDR correction is sufficient to control false discovery across all tested species, and the 10,000 permutation shuffles provide stable empirical p-values.
- **Assumption about data quality**: The eBird and NOAA/PRISM datasets are free from systematic biases that would invalidate the phenology-climate correlations (e.g., no temporal gaps in climate records, consistent observer effort in eBird).
- **Assumption about methodological scope**: The Riemannian manifold trajectory analysis and bootstrapped uncertainty quantification are computationally feasible within the defined CI runner time limit, with the Matérn covariance function providing an efficient approximation for spatial autocorrelation.