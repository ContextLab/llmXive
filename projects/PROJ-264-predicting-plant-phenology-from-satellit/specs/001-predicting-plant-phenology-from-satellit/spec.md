# Feature Specification: Predicting Plant Phenology from Satellite Imagery and Climate Data

**Feature Branch**: `001-predict-plant-phenology`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Plant Phenology from Satellite Imagery and Climate Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Alignment (Priority: P1)

The system MUST successfully download, process, and temporally align satellite imagery (Sentinel-2), climate data (NOAA/NASA), and ground-truth phenology observations (Nature's Notebook) for a defined set of study sites.

**Why this priority**: Without a clean, aligned dataset, no modeling or analysis can occur. This is the foundational data pipeline required for any research output.

**Independent Test**: Can be fully tested by running the data ingestion script for a single site and verifying that a single output file contains synchronized rows for satellite indices, climate variables, and phenological event dates with no missing temporal gaps for the target year.

**Acceptance Scenarios**:

1. **Given** a list of 10–15 valid site coordinates and a target year, **When** the ingestion pipeline executes, **Then** a consolidated dataset is generated containing NDVI, EVI, temperature, precipitation, and phenology event dates aligned to a 10-day interval.
2. **Given** a site where satellite imagery is missing for a specific 10-day window due to cloud cover, **When** the pipeline executes, **Then** the system interpolates the missing satellite value using the preceding and succeeding valid observations or flags the row for exclusion, ensuring the dataset remains temporally continuous.
3. **Given** a ground-truth phenology event date that falls between two 10-day satellite intervals, **When** the pipeline executes, **Then** the system correctly associates the event with the nearest preceding satellite observation window for feature extraction.

---

### User Story 2 - Predictive Model Training and Validation (Priority: P2)

The system MUST train a gradient boosting regression model (XGBoost) to predict phenological event timing using the aligned dataset, employing 5-fold cross-validation.

**Why this priority**: This is the core analytical engine of the project. It transforms the raw data into the predictive capability required to answer the research question.

**Independent Test**: Can be fully tested by training the model on a subset of sites, evaluating it on a held-out test site (not used in training), and verifying that the model produces a numeric prediction for phenological timing with a calculated R² and RMSE.

**Acceptance Scenarios**:

1. **Given** a training dataset of 10–15 sites, **When** the model training process completes, **Then** the system outputs a trained model artifact and a performance report containing RMSE, MAE, and R² metrics calculated on a held-out test set (the last [deferred] of sites sorted by latitude).
2. **Given** a dataset with multiple phenological events (budburst, flowering, senescence), **When** the model trains, **Then** it produces separate prediction models (or a multi-output model) for each event type, ensuring specific performance metrics are reported for each event.
3. **Given** a model trained on data from 2018–2022, **When** evaluated on 2023 data, **Then** the system reports the generalization error to confirm the model is not overfitting to historical patterns, provided the test set climate distribution (mean temperature/precipitation) does not differ from the training set by more than 1 standard deviation.

---

### User Story 3 - Sensitivity Analysis and Predictor Importance (Priority: P3)

The system MUST perform a sensitivity analysis on the regularization hyperparameters and identify the most influential climate and satellite predictors contributing to the model's predictions.

**Why this priority**: This addresses the methodological requirement for robustness and interpretability, ensuring the results are not artifacts of arbitrary parameter choices and providing ecological insight into drivers.

**Independent Test**: Can be fully tested by running the sensitivity analysis script which sweeps a specific threshold parameter and generates a plot or table showing how the prediction error (RMSE) varies across the sweep.

**Acceptance Scenarios**:

1. **Given** a model trained with a specific regularization parameter (alpha), **When** the sensitivity analysis runs, **Then** the system reports the change in RMSE and R² as the parameter is swept across values {0.01, 0.05, 0.1} relative to the baseline.
2. **Given** a trained model, **When** the feature importance analysis runs, **Then** the system outputs a ranked list of predictors (e.g., cumulative growing degree days, NDVI rate of change) with their relative contribution scores calculated via permutation importance.
3. **Given** multiple hypotheses about which climate variable drives phenology, **When** the analysis completes, **Then** the system provides a statistical summary indicating which variables consistently show the highest predictive power across cross-validation folds.

---

### Edge Cases

- What happens when a study site has zero cloud-free satellite observations for a critical phenological window (e.g., early spring)? The system must flag the site as "insufficient data" and exclude it from the final model training to prevent bias, rather than imputing with highly uncertain values. This is a specific sub-case of FR-008 where interpolation is impossible due to a gap >1 consecutive interval.
- How does the system handle sites where the ground-truth phenology observation is missing for a specific year? The system must treat the missing label as a masked value during training (excluding that row) rather than imputing a date, to avoid introducing label noise.
- What occurs if the climate data source (NOAA) returns a null value for a specific station on a specific day? The system must fall back to the nearest neighbor station data or interpolate linearly, logging the specific fallback method used for auditability.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download Sentinel-2 time-series data for 10–15 study sites via the Google Earth Engine API, extracting NDVI and EVI at 10-day intervals for 2018–2023. Sites must be selected deterministically based on having >80% cloud-free coverage in the spring (March-May) of 2020 (See US-1).
- **FR-002**: System MUST retrieve daily climate data (temperature, precipitation, solar radiation) from NOAA GHCN and NASA POWER APIs and align them temporally with satellite data (See US-1).
- **FR-003**: System MUST obtain ground-truth phenology observations from Nature's Notebook via their public API and map them to the specific study sites (See US-1).
- **FR-004**: System MUST train a gradient boosting regression model using XGBoost. If XGBoost fails to converge, the system MUST fall back to LightGBM and select the model with the lower 5-fold cross-validation RMSE (See US-2).
- **FR-005**: System MUST evaluate model performance using RMSE, MAE, and R² on held-out test years/sites to ensure generalization (See US-2).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the regularization parameter (alpha) over the set {0.01, 0.05, 0.1} and report the variation in RMSE (See US-3).
- **FR-007**: System MUST identify and rank all predictors with a permutation importance score > 0.01 contributing to the model's predictions (See US-3).
- **FR-008**: System MUST handle missing satellite data due to cloud cover by linearly interpolating if ≤1 consecutive 10-day intervals are missing; otherwise, the system MUST exclude the affected rows to ensure no gaps in the training sequence (See US-1).

### Key Entities

- **StudySite**: Represents a geographic location defined by latitude/longitude, containing metadata on plant functional type and the associated time-series data.
- **PhenologicalEvent**: Represents a specific biological transition (budburst, flowering, senescence) with an observed date and the corresponding environmental state at that time.
- **EnvironmentalTimeSeries**: A structured dataset containing aligned rows of satellite indices (NDVI, EVI) and climate variables (temperature, precipitation) indexed by date and site.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Prediction accuracy (R²) is measured against the baseline of a simple linear regression model using only temperature data (See US-2).
- **SC-002**: Generalization error (RMSE on held-out years) is measured against the training set error to quantify overfitting, conditional on the test set climate distribution overlapping with the training set within 1 standard deviation (See US-2).
- **SC-003**: Sensitivity of the model to threshold selection is measured by the range of RMSE values observed across the sweep {0.01, 0.05, 0.1} (See US-3).
- **SC-004**: Predictor importance is measured by the increase in RMSE (via 5-fold cross-validation) when each feature is permuted versus excluded (See US-3).
- **SC-005**: Data coverage is measured by the percentage of 10-day intervals with valid (non-interpolated and non-null) satellite data across all study sites (See US-1).

## Assumptions

- The Google Earth Engine API, NOAA GHCN, and NASA POWER APIs are accessible and provide sufficient historical data (2018–2023) for the selected study sites without requiring authentication beyond standard public access.
- The gradient boosting models (XGBoost/LightGBM) can be trained on the full dataset of 10–15 sites within the 6-hour time limit of the GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) without requiring GPU acceleration.
- The "Nature's Notebook" public API provides phenological event dates with sufficient granularity (specific dates) to align with the 10-day satellite intervals.
- The selected study sites represent a diverse range of plant functional types, ensuring the model learns generalizable patterns rather than site-specific noise.
- Cloud cover in the selected study regions is not so pervasive that it prevents the extraction of at least 80% of the required 10-day intervals for the training period; if >20% data is missing, the site is excluded.
- The relationship between satellite indices/climate variables and phenological timing is sufficiently captured by the selected gradient boosting model architecture without requiring deep learning or complex temporal neural networks.
- The sensitivity analysis threshold set {0.01, 0.05, 0.1} represents a standard range for regularization parameters (alpha/lambda) in gradient boosting literature, chosen to detect overfitting without excessive computational cost.