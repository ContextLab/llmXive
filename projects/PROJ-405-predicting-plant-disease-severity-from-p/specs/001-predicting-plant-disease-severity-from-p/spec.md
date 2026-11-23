# Feature Specification: Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

**Feature Branch**: `001-predict-plant-disease-severity`  
**Created**: 2026-09-08  
**Status**: Draft  
**Input**: User description: "Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Constructing the Weather-Integrated Visual Severity Dataset (Priority: P1)

The research pipeline MUST ingest the PlantVillage image dataset and link each image to historical meteorological data (temperature, humidity, precipitation) for the 7-day window preceding capture. The system must then compute continuous "visual severity" metrics (lesion area ratio, necrosis color index, texture entropy) using OpenCV to create a unified analysis-ready table.

**Why this priority**: Without a unified dataset linking visual features to environmental context, no statistical modeling or hypothesis testing regarding environmental modulation can occur. This is the foundational data engineering step.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a representative subset of images and verifying the output CSV contains non-null values for image features, weather variables, and the computed 7-day aggregates.

**Acceptance Scenarios**:

1. **Given** a valid PlantVillage image file and its metadata (location/date), **When** the ingestion script executes, **Then** the output record must contain the calculated lesion area ratio and the mean temperature for the 7 days prior to the image date.
2. **Given** an image with missing location metadata, **When** the ingestion script executes, **Then** the system must log a warning and exclude the record from the primary analysis dataset to prevent weather-mapping errors.
3. **Given** a dataset of [deferred] images, **When** the visual feature extraction runs on a subset of 50 images, **Then** the total memory usage must not exceed 7 GB RAM and the process must complete within 4 hours on a standard CPU-only runner.

---

### User Story 2 - Validating the Environmental Modulation Hypothesis (Priority: P2)

The system MUST train a baseline Random Forest regressor to predict "visual severity" using only image features. It MUST then calculate the residuals of this baseline prediction (Visual Severity - Baseline_Prediction). The system MUST train an augmented Random Forest regressor to predict these **residuals** using weather variables and interaction terms. It must then perform a paired permutation test (1,000 iterations) to determine if the weather-augmented model significantly reduces the prediction error of the residuals compared to a null model predicting zero residuals.

**Why this priority**: This directly addresses the core research question: "To what extent does environmental context modulate the consistency of visual lesion area progression?" By predicting residuals, we isolate the variance in severity not explained by image features, allowing weather to be tested as a modifier of the unexplained variance, avoiding tautological validation.

**Independent Test**: The analysis can be fully tested by running the modeling script on the prepared dataset and verifying that the permutation test returns a p-value for the R² difference of the residual prediction and an R² metric, confirming whether weather explains the unexplained variance.

**Acceptance Scenarios**:

1. **Given** the unified dataset, **When** the baseline model is trained, **Then** the system must output the R² score and mean absolute error (MAE) for the test set predicting raw visual severity.
2. **Given** the baseline results, **When** the residual calculation and augmented model training run, **Then** the system must output a p-value from a paired permutation test of R² differences (Augmented vs Null) indicating the statistical significance of weather variables in predicting residuals (α = 0.05).
3. **Given** a null result where weather adds no predictive value to residuals, **When** the analysis completes, **Then** the system must explicitly flag this outcome as a "Null Result" rather than a failure, validating the static symptom-severity assumption.

---

### User Story 3 - Visualizing Interaction Effects and Threshold Sensitivity (Priority: P3)

The system MUST generate partial dependence plots to visualize how the slope of the residual prediction vs. weather relationship changes across temperature and humidity bins. Additionally, it must perform a sensitivity analysis sweeping a classification threshold derived from the continuous visual severity metric to demonstrate robustness.

**Why this priority**: Visualization is required to interpret the "modulation" effect described in the expected results. Sensitivity analysis ensures the findings are not artifacts of arbitrary parameter choices when converting continuous severity to binary classes.

**Independent Test**: The analysis can be fully tested by generating the plots and verifying that the output files exist and show distinct trends for different weather bins, and that the sensitivity report lists the variation in key metrics across the tested threshold range.

**Acceptance Scenarios**:

1. **Given** the trained augmented model, **When** the partial dependence plot generation runs, **Then** the output must include a plot showing the interaction effect between humidity and image features on predicted residual severity.
2. **Given** a baseline classification threshold defined as the 90th percentile of visual severity in the training set, **When** the sensitivity analysis runs, **Then** the system must report the false-positive and false-negative rates for thresholds at absolute deviations of {0.01, 0.05, 0.1} from this baseline value.
3. **Given** the sensitivity results, **When** the report is generated, **Then** it must explicitly state whether the headline findings hold across the swept threshold range.

### Edge Cases

- What happens if the Open-Meteo API returns no data for a specific date/location (e.g., missing historical records)? The system must impute using the nearest neighbor station or exclude the record with a specific log flag.
- How does the system handle images where lesion segmentation fails (e.g., [deferred] lesion area detected in a "diseased" class)? The system must filter these outliers or flag them for manual review, as they represent a data quality issue rather than a biological signal.
- What if the 7-day weather window spans a month boundary or leap year? The date arithmetic must correctly handle these transitions to ensure the correct historical data is fetched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract continuous visual severity metrics (lesion area ratio, necrosis color index, texture entropy) from input leaf images using OpenCV without requiring GPU acceleration. (See US-1)
- **FR-002**: System MUST map image metadata to historical weather data (temperature, humidity, precipitation) for the 7-day window preceding capture using the Open-Meteo API or NOAA GHCN-Daily. (See US-1)
- **FR-003**: System MUST train a Random Forest regressor to predict raw visual severity using a baseline set of image-only predictors. (See US-2)
- **FR-004**: System MUST train an augmented Random Forest regressor to predict the **residuals of visual severity** (Target minus Baseline_Prediction) using weather main effects and interaction terms. (See US-2)
- **FR-005**: System MUST perform a paired permutation test with ≥1,000 iterations to statistically validate the unique variance contribution of weather features in predicting the residuals over a null model. (See US-2)
- **FR-006**: System MUST generate partial dependence plots visualizing the interaction between weather variables and image features on predicted residual severity. (See US-3)
- **FR-007**: System MUST execute a sensitivity analysis sweeping a classification threshold (derived from a high percentile of visual severity) over absolute deviations of {0.01, 0.05, 0.1} and report the variation in F1 score and False Positive Rate. (See US-3)
- **FR-008**: System MUST ensure all data processing and model training for the **full PlantVillage dataset** fit within 7 GB RAM and complete within 6 hours on a CPU-only runner. (See US-1, US-2, US-3)

### Key Entities

- **ImageRecord**: Represents a single leaf image with attributes for file path, disease label, extracted visual features (lesion area, color index, entropy), and linked metadata (location, date).
- **WeatherContext**: Represents the aggregated meteorological state for a specific location and 7-day window, containing mean temperature, mean humidity, and total precipitation.
- **ModelFit**: Represents the result of a regression training run, containing performance metrics (R², MAE) for the specific target (raw severity or residuals), feature importance scores, and permutation test statistics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in prediction error (MAE) of the augmented model (predicting residuals) compared to a null model (predicting zero residuals) is measured against the permutation test distribution to determine statistical significance (p < 0.05). (See US-2)
- **SC-002**: The variation in false-positive and false-negative rates across the sensitivity analysis thresholds (absolute deviations of {0.01, 0.05, 0.1} from the 90th percentile) is measured against the baseline threshold performance to confirm robustness. (See US-3)
- **SC-003**: The computational resource usage (RAM peak, total runtime) is measured against the GitHub Actions free-tier limits to ensure feasibility. (See US-1, US-2, US-3)
- **SC-004**: The p-value for the weather feature importance in the augmented model (predicting residuals) must be < 0.05, indicating that weather explains variance in severity not captured by image features. (See US-2)

## Assumptions

- The PlantVillage dataset contains sufficient metadata (location and date) to reliably query historical weather data for the 7-day window preceding image capture.
- The Open-Meteo API (or NOAA GHCN-Daily) provides historical weather data with sufficient resolution and coverage for the locations and dates present in the PlantVillage dataset.
- The "visual severity" metrics derived from OpenCV (lesion area, color index) serve as a valid proxy for biological disease severity (spore load/biomass) for the purpose of this correlational study.
- The Random Forest algorithm is sufficiently robust to handle the collinearity likely present between temperature and humidity variables without requiring explicit dimensionality reduction (e.g., PCA) for this initial analysis.
- The computational constraints of the free-tier runner (7 GB RAM, 6 hours) are sufficient to process the full PlantVillage dataset using batched OpenCV operations and a single Random Forest model without subsampling.
- The study is observational; therefore, any findings regarding the relationship between weather and symptom progression will be framed as associational, not causal, in the final report.
- The 7-day weather window is an appropriate temporal scale for capturing the environmental stressors affecting the visual progression of the diseases in the dataset.