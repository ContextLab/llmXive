# Feature Specification: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Feature Branch**: `001-predicting-species-distribution-shifts`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

The system MUST download historical occurrence records (1970-2000) and corresponding climate rasters (WorldClim v2), then preprocess them by filtering for breeding season, removing duplicates, and spatially thinning points to reduce autocorrelation.

**Why this priority**: This is the foundational step; without clean, temporally-aligned occurrence and climate data, no model can be trained or validated.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains ≥1000 unique, thinned coordinates per target species with matched climate variables, without requiring model training.

**Acceptance Scenarios**:

1. **Given** a list of target species names, **When** the pipeline runs, **Then** occurrence records are filtered to breeding months and duplicates removed.
2. **Given** occurrence coordinates, **When** spatial thinning is applied, **Then** points are separated by at least 10km (or defined distance) to reduce spatial autocorrelation.
3. **Given** climate rasters, **When** extracted at occurrence points, **Then** every record has non-null values for temperature and precipitation variables.

---

### User Story 2 - Model Training and Validation (Priority: P2)

The system MUST train three SDM algorithms (MaxEnt-style, Random Forest, Bioclim) on the historical dataset using a [deferred] train / [deferred] validation split, ensuring all computations run on CPU without GPU acceleration.

**Why this priority**: This delivers the core analytical capability to assess predictive skill, directly addressing the research question regarding SDM reliability.

**Independent Test**: Can be fully tested by training models on a single species subset and verifying that training completes within 1 hour and outputs performance metrics (AUC, TSS) without CUDA errors.

**Acceptance Scenarios**:

1. **Given** the preprocessed historical dataset, **When** the training script runs, **Then** models are trained using scikit-learn or equivalent CPU-optimized libraries.
2. **Given** a 70/30 split, **When** validation occurs, **Then** performance metrics (AUC, TSS) are calculated on the held-out [deferred] set.
3. **Given** hardware constraints, **When** models train, **Then** no GPU/CUDA dependencies are invoked (verified via process monitoring).

---

### User Story 3 - Future Projection and Evaluation (Priority: P3)

The system MUST project trained models onto future climate scenarios (CMIP6 SSP2-4.5, 2050) and evaluate predictive performance against recent occurrence records (2005-2020) using paired statistical tests.

**Why this priority**: This completes the forecasting loop, allowing comparison of historic predictions against recent observations to quantify reliability.

**Independent Test**: Can be fully tested by loading pre-trained models and running projections against the recent test set, producing a summary table of AUC/TSS improvements.

**Acceptance Scenarios**:

1. **Given** trained models and future climate rasters, **When** projection runs, **Then** suitability maps are generated for 2050 scenarios.
2. **Given** recent occurrence records (2005-2020), **When** evaluated against projections, **Then** AUC and TSS metrics are computed.
3. **Given** multiple model results, **When** comparison occurs, **Then** paired statistical tests (t-test or Wilcoxon) are performed with appropriate error correction.

---

### Edge Cases

- What happens when a species has <100 occurrence records after thinning? (System MUST skip or flag with `[NEEDS CLARIFICATION]`).
- How does system handle missing climate data for specific coordinates? (System MUST impute using nearest neighbor or exclude the point).
- What happens if recent test records (2005-2020) are unavailable for a target species? (System MUST log a warning and exclude from evaluation metrics).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download North American bird occurrence data (1970-2000) via GBIF API and climate rasters from WorldClim v2, ensuring all required predictor variables are present for every record (See US-1).
- **FR-002**: System MUST spatially thin occurrence points to a minimum distance (e.g., 10km) to reduce spatial autocorrelation before model training (See US-1).
- **FR-003**: System MUST train all SDM algorithms using CPU-only libraries (e.g., `scikit-learn`) with no GPU/CUDA dependencies to ensure compatibility with free-tier CI runners (See US-2).
- **FR-004**: System MUST frame all reported findings as ASSOCIATIONAL rather than causal, acknowledging the observational nature of the occurrence and climate data (See US-2).
- **FR-005**: System MUST perform a sensitivity analysis on the suitability probability threshold (sweeping absolute diff ∈ {0.01, 0.05, 0.1}) and apply multiple-comparison correction for paired hypothesis tests (See US-3).

### Key Entities

- **Occurrence Record**: Represents a species sighting with latitude, longitude, date, and source.
- **Climate Variable**: Represents environmental data (temperature, precipitation) at a specific grid resolution.
- **Model Artifact**: Represents the trained SDM object (MaxEnt, RF, or Bioclim) ready for projection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive performance (AUC) is measured against the baseline expectation of ≥0.70 for historical-to-future generalization (See US-2).
- **SC-002**: Total compute time is measured against the 6-hour GitHub Actions free-tier limit, ensuring the full workflow completes within 360 minutes (See US-3).
- **SC-003**: Sensitivity analysis results are measured against the requirement that headline rates (false-positive/negative) are reported across the swept threshold set (0.01, 0.05, 0.1) (See US-3).

## Assumptions

- Users have stable internet connectivity to access GBIF and WorldClim APIs without firewall restrictions.
- A subset of North American bird species (e.g., 10-20 common species) will be selected to ensure the analysis fits within the 6-hour compute window and 7GB RAM limit.
- The 2.5 arc-min grid resolution from WorldClim is sufficient for the spatial scale of the target bird species' ranges.
- `[NEEDS CLARIFICATION: Does the specific target species list contain sufficient records in the 2005-2020 test period to validate model performance?]`
