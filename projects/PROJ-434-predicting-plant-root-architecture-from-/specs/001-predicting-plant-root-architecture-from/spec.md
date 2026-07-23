# Feature Specification: Predicting Plant Root Architecture from Soil Nutrient Profiles

**Feature Branch**: `001-predict-root-architecture`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Plant Root Architecture from Soil Nutrient Profiles"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Geospatial Alignment (Priority: P1)

The system must successfully ingest public soil nutrient raster data (SoilGrids) and root trait tabular data (Zenodo/Dryad), geocode the root study locations, and extract the corresponding soil nutrient values to create a unified, analysis-ready dataset.

**Why this priority**: This is the foundational step. Without a merged dataset containing paired observations of soil nutrients and root traits, no predictive modeling or analysis can occur. It validates the feasibility of the data sources.

**Independent Test**: The pipeline can be executed end-to-end on a sample subset of coordinates, producing a single CSV file where every row contains a valid root trait measurement paired with extracted soil N, P, K, and pH values.

**Acceptance Scenarios**:

1. **Given** a list of georeferenced root study locations and SoilGrids raster URLs, **When** the ingestion script runs, **Then** the output dataset contains exactly one row per location with non-null values for all requested nutrient layers.
2. **Given** a root study location with no corresponding soil data in the provided rasters (e.g., out of bounds or missing layer), **When** the ingestion script runs, **Then** that location is flagged and excluded from the primary analysis set with a clear log entry.
3. **Given** the merged dataset, **When** a user inspects the schema, **Then** all predictor variables (N, P, K, pH) and outcome variables (depth, branching density) are present with consistent units (e.g., mg/kg, cm).

---

### User Story 2 - Predictive Model Training and Validation (Priority: P2)

The system must train a Random Forest Regressor to predict root depth and branching density from soil nutrient profiles and evaluate performance using 5-fold cross-validation to determine predictive power (R²) and error (RMSE).

**Why this priority**: This addresses the core research question: "How do spatial variations... predict root system architecture?" It provides the primary evidence for the hypothesis.

**Independent Test**: The training script executes on the merged dataset, outputs cross-validation metrics (mean R², mean RMSE) for both target variables, and generates a feature importance plot.

**Acceptance Scenarios**:

1. **Given** a merged dataset with ≥50 observations per cereal species, **When** the model training script runs, **Then** it completes within 60 minutes on a standard CPU environment and outputs a JSON file containing the mean R² and RMSE for each target variable.
2. **Given** the trained model, **When** the cross-validation is performed, **Then** the variance in R² across the 5 folds is reported to assess model stability.
3. **Given** the feature importance results, **When** a user reviews the output, **Then** the top 3 soil nutrient predictors are ranked and visualized in a bar chart.

---

### User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

The system must perform a sensitivity analysis on the decision threshold for distinguishing "high-yield" vs. "low-yield" root phenotypes (if applicable) or the minimum correlation threshold for claiming a relationship, sweeping the cutoff over a defined range to report stability.

**Why this priority**: The methodology panel requires that any decision cutoff be justified and tested for sensitivity to ensure findings are robust and not artifacts of arbitrary thresholds.

**Independent Test**: The analysis script runs a loop over a specific set of threshold values (e.g., R² ∈ {0.05, 0.10, 0.15}) and outputs a table showing how the "success rate" or "prediction confidence" varies across these values.

**Acceptance Scenarios**:

1. **Given** the model performance metrics, **When** the sensitivity analysis runs, **Then** it evaluates the classification of "predictable" vs. "unpredictable" species at thresholds of R² = 0.05, 0.10, and 0.15.
2. **Given** the sweep results, **When** the report is generated, **Then** it explicitly states whether the headline conclusion (e.g., "Nitrogen is a strong predictor") holds across the tested range.
3. **Given** the analysis output, **When** a reviewer checks the justification, **Then** the report cites the community-standard basis for the primary threshold (e.g., "0.10 chosen based on typical effect sizes in ecological regression").

---

### Edge Cases

- What happens when a specific cereal species has fewer than 10 observations in the curated root trait datasets? (System filters these out and logs a warning).
- How does the system handle soil nutrient values that are reported as "No Data" or negative in the raster layers? (System imputes with the global mean for that layer or excludes the specific coordinate).
- What happens if the geocoding of a study location fails (e.g., ambiguous address)? (System excludes the record and logs the specific study ID).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download global soil nutrient rasters (N, P, K, pH) from the SoilGrids API for the specific coordinates of root study locations. (See US-1)
- **FR-002**: System MUST merge the extracted soil data with root trait datasets, filtering for species with ≥10 valid observations to ensure statistical power. (See US-1)
- **FR-003**: System MUST train a Random Forest Regressor to predict root depth and branching density using the merged dataset as input. (See US-2)
- **FR-004**: System MUST perform 5-fold cross-validation to compute R² and RMSE metrics for both target variables on held-out data. (See US-2)
- **FR-005**: System MUST generate feature importance plots and a sensitivity analysis report sweeping the R² threshold over {0.05, 0.10, 0.15} to assess robustness. (See US-3)
- **FR-006**: System MUST frame all findings as associational (not causal) in the final report, acknowledging the observational nature of the dataset. (See US-2)

### Key Entities

- **SoilProfile**: Represents a specific geographic location with attributes for Nitrogen (mg/kg), Phosphorus (mg/kg), Potassium (mg/kg), and pH.
- **RootTrait**: Represents a phenotypic measurement with attributes for Species, Root Depth (cm), and Branching Density (roots/cm).
- **ObservationPair**: A merged record linking a SoilProfile to a RootTrait at a specific coordinate.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The proportion of root study locations successfully matched with soil nutrient data is measured against the total number of input coordinates. (See US-1)
- **SC-002**: The predictive accuracy (R²) of the Random Forest model for root depth is measured against the null model (mean prediction) baseline. (See US-2)
- **SC-003**: The stability of the model's performance is measured by the standard deviation of R² across the 5 cross-validation folds. (See US-2)
- **SC-004**: The robustness of the "predictable phenotype" classification is measured by the variation in classification rates across the swept R² thresholds {0.05, 0.10, 0.15}. (See US-3)
- **SC-005**: The computational efficiency is measured by the total execution time of the analysis pipeline against the 6-hour free-tier CI limit. (See Assumptions)

## Assumptions

- **Assumption about data availability**: Public repositories (Zenodo/Dryad) contain georeferenced root trait data for at least 3 distinct cereal species with a minimum of 10 observations per species.
- **Assumption about data fit**: The SoilGrids dataset contains the specific variables (N, P, K, pH) required for the analysis at the resolution of the root study locations; if a variable is missing, the analysis will proceed with available nutrients and note the gap.
- **Assumption about compute environment**: The analysis (Random Forest on sampled data) will complete within 6 hours on a GitHub Actions free-tier runner (2 CPU, 7GB RAM) without GPU acceleration.
- **Assumption about inference**: The relationship between soil nutrients and root architecture is treated as associational; no causal claims are made without randomization.
- **Assumption about threshold justification**: An R² threshold of 0.10 is selected as the primary cutoff for "meaningful prediction" based on typical effect sizes in ecological regression, with sensitivity analysis performed around this value.
