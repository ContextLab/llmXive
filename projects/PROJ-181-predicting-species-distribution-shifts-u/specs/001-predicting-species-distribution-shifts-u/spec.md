# Feature Specification: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Feature Branch**: `001-predicting-species-distribution-shifts`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

The system MUST download historical occurrence records (from a multi-decade baseline period) and corresponding climate rasters (WorldClim), then preprocess them by filtering for breeding season, removing duplicates, and spatially thinning points to reduce autocorrelation.

**Why this priority**: This is the foundational step; without clean, temporally-aligned occurrence and climate data, no model can be trained or validated.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains unique coordinates where no two points are within the minimum distance defined in FR-014, and that climate variables are successfully extracted for every record.

**Acceptance Scenarios**:

1. **Given** a list of target species names, **When** the pipeline runs, **Then** occurrence records are filtered to breeding months and duplicates removed.
2. **Given** occurrence coordinates, **When** spatial thinning is applied, **Then** points are separated by at least the minimum distance specified in FR-014 to reduce spatial autocorrelation.
3. **Given** climate rasters, **When** extracted at occurrence points, **Then** every record has non-null values for temperature and precipitation variables.

---

### User Story 2 - Model Training and Validation (Priority: P2)

The system MUST train three SDM algorithms (MaxEnt-style, Random Forest, Bioclim) on the historical dataset using a [deferred] train / [deferred] validation split (to be determined by methodology, e.g., 70/30) via spatial block cross-validation as defined in FR-006, ensuring all computations run on CPU without GPU acceleration.

**Why this priority**: This delivers the core analytical capability to assess predictive skill, directly addressing the research question regarding SDM reliability.

**Independent Test**: Can be fully tested by training models on a single species subset and verifying that training completes successfully and outputs performance metrics (AUC, TSS) without CUDA errors.

**Acceptance Scenarios**:

1. **Given** the preprocessed historical dataset, **When** the training script runs, **Then** models are trained using scikit-learn or equivalent CPU-optimized libraries.
2. **Given** the spatial block configuration defined in FR-006, **When** validation occurs, **Then** performance metrics (AUC, TSS) are calculated on the held-out blocks.
3. **Given** hardware constraints, **When** models train, **Then** no GPU/CUDA dependencies are invoked (verified via process monitoring).

---

### User Story 3 - Future Projection and Evaluation (Priority: P3)

The system MUST project trained models onto future climate scenarios (CMIP SSP, mid-21st century) and evaluate predictive performance against recent occurrence records (2000s-2020) using paired statistical tests and niche stability checks. This evaluation measures predictive accuracy, where low scores may indicate potential niche shifts, sampling bias, or dispersal limitation, but does not directly validate the biological mechanism of the shift.

**Why this priority**: This completes the forecasting loop, allowing comparison of historic predictions against recent observations to quantify reliability and distinguish between niche conservatism and range shift.

**Independent Test**: Can be fully tested by loading pre-trained models and running projections against the recent test set, producing a summary table of AUC/TSS improvements and niche stability metrics.

**Acceptance Scenarios**:

1. **Given** trained models and future climate rasters, **When** projection runs, **Then** suitability maps are generated for 2050 scenarios.
2. **Given** recent occurrence records (2005-2020), **When** evaluated against projections, **Then** AUC and TSS metrics are computed.
3. **Given** multiple model results, **When** comparison occurs, **Then** non-parametric hierarchical bootstrap resampling as defined in FR-009 is performed.
4. **Given** a target species with <100 occurrence records in the 2005-2020 test period, **When** evaluation occurs (as per FR-005), **Then** the system flags the species as 'INSUFFICIENT_DATA' and excludes it from the final performance aggregation.

---

### Edge Cases

- What happens when a species has <100 occurrence records after thinning? (System MUST skip or flag with status 'INSUFFICIENT_DATA' as defined in FR-005).
- How does system handle missing climate data for specific coordinates? (System MUST impute using nearest neighbor or exclude the point).
- What happens if recent test records (2005-2020) are unavailable for a target species? (System MUST log a warning and exclude from evaluation metrics).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download North American bird occurrence data (mid-to-late th century) via GBIF API or eBird and climate rasters from WorldClim v2 via wget or equivalent, ensuring all required predictor variables are present for every record (See US-1).
- **FR-002**: System MUST download recent occurrence records (early st century to present) via GBIF API or eBird for evaluation purposes (See US-3).
- **FR-003**: System MUST spatially thin occurrence points using a maximum distance thinning method with a default minimum distance threshold., or a dynamic calculation based on the 95th percentile of nearest neighbor distances if specified, to reduce spatial autocorrelation before model training (See US-1).
- **FR-004**: System MUST train all SDM algorithms using CPU-only libraries (e.g., `scikit-learn`) with no GPU/CUDA dependencies to ensure compatibility with free-tier CI runners (See US-2).
- **FR-005**: System MUST perform a sensitivity analysis on the suitability probability threshold by sweeping absolute differences across a range of small increments from a baseline threshold of 0.5, and apply multiple-comparison correction for paired hypothesis tests (See US-3).
- **FR-006**: System MUST include a dynamic validation check: if a target species has <100 occurrence records in the 2005-2020 test period, the system MUST flag the species as 'INSUFFICIENT_DATA' and exclude it from the final performance aggregation, while logging the specific count. This threshold of ≥100 records is set to ensure statistical power for AUC/TSS calculation, subject to the power analysis in FR-015 (See US-3).
- **FR-007**: System MUST use spatial block cross-validation for training and validation, dividing the spatial domain into K blocks (default K=5) using an equidistant grid algorithm and rotating the held-out block to ensure spatial independence between train and test sets (See US-2).
- **FR-008**: System MUST frame all reported findings as ASSOCIATIONAL by appending a specific disclaimer string ("Findings are associational and assume niche stability") to all generated reports, acknowledging the observational nature of the occurrence and climate data (See US-3).
- **FR-009**: System MUST test for niche stability by calculating and outputting the degradation in performance (delta AUC/TSS) when projecting historical models to future climate versus historical climate, as a measure of non-stationarity (See US-3).
- **FR-010**: System MUST use hierarchical bootstrap resampling with a sufficient number of iterations to compare model performance across species to account for the dependence structure and distributional properties of AUC/TSS metrics (See US-3).
- **FR-011**: System MUST perform a power analysis to validate that the sample size (≥100 records) is sufficient for a target effect size of 0.50 (Cohen's h) with power ≥ 0.8 before applying the static filter in FR-006 (See US-3).

### Key Entities

- **Occurrence Record**: Represents a species sighting with latitude, longitude, date, and source.
- **Climate Variable**: Represents environmental data (temperature, precipitation) at a specific grid resolution.
- **Model Artifact**: Represents the trained SDM object (MaxEnt, RF, or Bioclim) ready for projection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive performance (AUC) is measured against a baseline expectation defined as the AUC of a null model predicting mean prevalence for historical-to-future generalization (See US-2).
- **SC-002**: Total compute time is measured against the 6-hour GitHub Actions free-tier limit, ensuring the full workflow completes within 360 minutes (See US-3).
- **SC-003**: Sensitivity analysis results are measured against the requirement that headline rates (false-positive/negative) are reported in a summary table across the swept threshold set {0.01, 0.05, 0.10} from baseline 0.5 (See US-3).

## Assumptions

- Users have stable internet connectivity to access GBIF and WorldClim APIs without firewall restrictions.
- A subset of North American bird species (e.g., a representative number of common species) will be selected to ensure the analysis fits within the available compute time and memory constraints.
- The WorldClim grid resolution is sufficient for the spatial scale of the target bird species' ranges.