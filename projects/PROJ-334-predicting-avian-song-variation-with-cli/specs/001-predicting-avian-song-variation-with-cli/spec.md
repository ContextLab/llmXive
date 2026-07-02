# Feature Specification: Predicting Avian Song Variation with Climatic and Geographic Factors

**Feature Branch**: `001-predict-avian-song-variation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Avian Song Variation with Climatic and Geographic Factors"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Variable Alignment (Priority: P1)

The system must successfully load the primary avian acoustic dataset and the external climatic/geographic datasets, then align them by geographic location and species identifier to create a unified analysis-ready table.

**Why this priority**: Without a clean, aligned dataset containing both the response variable (song metrics) and predictors (climate/geo), no analysis can proceed. This is the foundational step for the entire research pipeline.

**Independent Test**: Can be fully tested by executing the data loading script against the provided sample CSVs and verifying the output schema contains the required columns (species_id, song_metric_1, song_metric_2, temperature, precipitation, latitude, longitude) with no missing rows due to failed joins.

**Acceptance Scenarios**:

1. **Given** a CSV of bird song recordings and a CSV of climate data, **When** the ingestion script runs, **Then** the output table contains a calculated match rate (matched rows / total input rows) with no duplicate rows, ensuring unique matches based on the spatial join logic.
2. **Given** a species in the song dataset that has no corresponding climate data, **When** the ingestion script runs, **Then** that species is excluded from the final analysis table, and a warning log entry is generated listing the excluded species count.
3. **Given** mismatched coordinate systems (e.g., WGS84 vs. NAD83) in the source files, **When** the ingestion script runs, **Then** the system automatically reprojects all coordinates to WGS before performing the spatial join.

---

### User Story 2 - Exploratory Data Analysis and Correlation Matrix (Priority: P2)

The system must generate a statistical summary and a correlation matrix to visualize the relationships between song metrics and environmental predictors, providing the initial evidence for the research question.

**Why this priority**: This step validates the data quality and provides the first empirical answer to "do these factors correlate?" It is a standalone deliverable that can be reviewed by domain experts even before complex modeling begins.

**Independent Test**: Can be fully tested by running the EDA script and verifying that a JSON report is generated containing a correlation matrix where the matrix is symmetric, the diagonal values are exactly 1.0, and all values are strictly within the range [-1.0, 1.0].

**Acceptance Scenarios**:

1. **Given** the aligned analysis dataset, **When** the EDA script executes, **Then** a correlation matrix is generated showing the Pearson correlation coefficient between each song metric and each climatic variable, with values ranging strictly between -1.0 and 1.0.
2. **Given** a pair of highly correlated predictors (e.g., temperature and elevation), **When** the EDA script executes, **Then** the report flags this pair with a correlation coefficient exceeding the multicollinearity threshold defined in the analysis plan (default 0.8) and recommends checking for multicollinearity in subsequent modeling.
3. **Given** the dataset, **When** the EDA script executes, **Then** a summary statistics table is produced showing the mean, standard deviation, and range for all continuous variables, with no infinite values.

---

### User Story 3 - Predictive Modeling with Sensitivity Analysis (Priority: P3)

The system must fit a linear regression model to predict song variation from climate/geo factors and perform a sensitivity analysis on any decision thresholds (if applicable) or model hyperparameters, ensuring the findings are robust.

**Why this priority**: This delivers the core research outcome (the predictive model) and addresses the methodological requirement for robustness. It is the final step in the research loop.

**Independent Test**: Can be fully tested by running the modeling script and verifying that a model file is saved, along with a sensitivity report showing how model performance (R²) changes when the training data is perturbed or when a specific threshold (e.g., p-value cutoff) is varied.

**Acceptance Scenarios**:

1. **Given** the training data, **When** the regression model is trained, **Then** the model achieves a statistically significant improvement in R² over a null model (intercept-only), demonstrating predictive capability beyond random chance.
2. **Given** a p-value threshold of 0.05 for variable significance, **When** the sensitivity analysis runs, **Then** the report shows the change in the number of significant predictors when the threshold is swept to {0.01, 0.10}.
3. **Given** the fitted model, **When** the sensitivity analysis runs, **Then** the system reports the variation in the number of significant predictors across the specified threshold sweep.

### Edge Cases

- What happens when the acoustic dataset contains species with no corresponding climate records within the defined radius? (Handled by exclusion and logging).
- How does the system handle missing values in the climate data (e.g., gaps in weather station records)? (Impute using nearest-neighbor or exclude, depending on threshold).
- How does the system handle a scenario where the climate and song data are perfectly collinear (e.g., all song data is from a single location)? (The system must detect zero variance in predictors and abort with a clear error).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load and merge the avian song dataset with the climatic and geographic datasets using species ID and geographic coordinates as keys, ensuring no data loss due to coordinate mismatches. (See US-1)
- **FR-002**: System MUST generate a correlation matrix and summary statistics report to quantify the linear relationships between song metrics and environmental predictors. (See US-2)
- **FR-003**: System MUST fit a multiple linear regression model to predict song variation from the aligned environmental variables, explicitly treating the relationship as associational. (See US-3)
- **FR-004**: System MUST perform a sensitivity analysis by sweeping the significance threshold (p-value) over the set {0.01, 0.05, 0.10} and reporting the change in the number of significant predictors and model R². (See US-3)
- **FR-005**: System MUST include a collinearity diagnostic (Variance Inflation Factor) for all predictors and flag any pair with VIF > 5. (See US-2)
- **FR-006**: System MUST apply a False Discovery Rate (FDR) control (Benjamini-Hochberg procedure) to p-values when testing multiple hypotheses simultaneously across different song metrics. (See US-3)

### Key Entities

- **SongRecord**: Represents a single acoustic recording, containing attributes: `species_id`, `song_metric_1` (e.g., frequency), `song_metric_2` (e.g., duration), `location_lat`, `location_lon`.
- **ClimateSnapshot**: Represents environmental conditions at a specific location and time, containing attributes: `location_lat`, `location_lon`, `temperature`, `precipitation`, `elevation`.
- **AnalysisDataset**: The merged entity resulting from the join of `SongRecord` and `ClimateSnapshot`, containing all matched records (predictors and outcomes) aligned by location.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The proportion of song recordings successfully matched with climate data is measured against the total number of recordings in the input dataset. (See FR-001)
- **SC-002**: The model's predictive performance (R²) is measured against a null model (intercept-only), requiring a quantifiable improvement in R² to validate the hypothesis. (See FR-003)
- **SC-003**: The stability of the model's variable selection is measured against the threshold sweep, requiring that the Jaccard index of significant predictors is calculated and reported across the {0.01, 0.05, 0.10} range. (See FR-004)
- **SC-004**: The multicollinearity diagnostic is measured against the VIF threshold of 5, requiring that no predictor pair exceeds this limit without a descriptive joint interpretation. (See FR-005)
- **SC-005**: The computational execution time is measured against the 6-hour free-tier runner limit, requiring the entire pipeline (ingestion to sensitivity analysis) to complete within 1 hour to ensure feasibility. (See Assumptions)

## Assumptions

- The primary avian song dataset (e.g., Xeno-Canto or similar) contains sufficient metadata (species ID, GPS coordinates) to allow for a spatial join with the WorldClim or similar global climate dataset.
- The relationship between climate and song is treated as associational (observational study) due to the lack of random assignment; no causal claims will be made in the final report.
- The dataset size (after sampling if necessary) will fit within the available RAM limit of the GitHub Actions free-tier runner.; if the full dataset exceeds this, a stratified random sample of a sufficiently large number of records will be used.
- The analysis will use standard Python libraries (pandas, scikit-learn, statsmodels) which are CPU-tractable and do not require GPU acceleration.
- The climatic variables (temperature, precipitation) are available at a resolution sufficient to match the geographic precision of the bird song recordings (e.g., on the order of kilometers or arc-seconds).
- The "sensitivity analysis" threshold sweep is computationally trivial (re-running the model 3 times) and will not exceed the 6-hour job limit.
- Any missing values in the climate data will be handled by imputation using the median value of the nearest neighboring grid cells, assuming spatial autocorrelation.