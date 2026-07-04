# Feature Specification: Predicting Coral Bleaching Susceptibility from Environmental Data

**Feature Branch**: `001-predict-coral-bleaching`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Can a machine‑learning model that integrates publicly available oceanographic variables and species‑level trait data accurately predict bleaching susceptibility for individual reef locations and coral taxa?"

## User Scenarios & Testing

### User Story 1 - Data Integration and Feature Construction (Priority: P1)

A researcher needs to aggregate heterogeneous data sources (NOAA satellite rasters, UNEP reef geometries, Coral Trait Database traits, and ReefBase bleaching events) into a single, analysis-ready dataset where each row represents a unique reef-species combination with aligned environmental and trait features.

**Why this priority**: Without a unified, clean dataset, no model can be trained. This is the foundational step that enables all subsequent analysis and must be independently testable to ensure data integrity before modeling begins.

**Independent Test**: The system can be tested by running the data ingestion pipeline and verifying that the output CSV contains exactly the expected number of rows (matching the intersection of reef locations and species) and that all required columns (SST, DHW, thermal tolerance, bleaching label) are populated without nulls in critical fields.

**Acceptance Scenarios**:
1. **Given** the raw NOAA, UNEP, Trait DB, and ReefBase files are available, **When** the ingestion script executes, **Then** a unified dataset is generated with a 5-km grid resolution and no missing values for the primary predictors (SST, DHW, traits), achieved by imputing missing values using the nearest valid temporal neighbor or excluding rows if the gap exceeds a substantial duration threshold.
2. **Given** a specific reef location and coral species, **When** the feature extraction runs, **Then** the resulting row contains the mean SST and DHW for the relevant time window and the specific thermal tolerance value for that species.

---

### User Story 2 - Model Training, Spatial Generalization, and Statistical Validation (Priority: P2)

A conservation analyst needs a trained Gradient Boosting model that predicts bleaching susceptibility, demonstrates the ability to generalize to unseen geographic regions (e.g., trained on the Western Pacific, tested on the Eastern Pacific), and provides statistically validated feature importance rankings.

**Why this priority**: The core scientific value lies in the model's predictive power, its ability to transfer across regions, and the statistical confidence in the identified drivers, validating the utility of the environmental-trait integration.

**Independent Test**: The system can be tested by executing the training script with a fixed random seed and spatial split, then reporting the ROC-AUC score on the held-out geographic test set and the significance of top features.

**Acceptance Scenarios**:
1. **Given** the unified dataset is split by geographic region (train: Western Pacific, test: Eastern Pacific), **When** the XGBoost model is trained with 5-fold cross-validation, **Then** the model reports the ROC-AUC score on the held-out test set.
2. **Given** the trained model, **When** a permutation importance analysis is run, **Then** the output ranks "Degree-Heating-Weeks" and "Species Thermal Tolerance" as top features.
3. **Given** the feature importance scores, **When** the statistical validation step executes, **Then** empirical p-values are calculated via a permutation-based approach and corrected using the Benjamini-Hochberg FDR method.

---

### User Story 3 - Risk Mapping, Interpretability, and Threshold Robustness (Priority: P3)

A reef manager needs a visual risk map (probability of bleaching) for a target region (e.g., Indo-Pacific), a summary of which specific environmental factors drive the risk, and an analysis of how classification thresholds impact risk predictions.

**Why this priority**: This translates the abstract model output into actionable intelligence for conservation planning, fulfilling the "actionable guidance" goal of the research question and ensuring operational robustness.

**Independent Test**: The system can be tested by generating a GeoTIFF map and a summary report, verifying that high-risk zones align with known historical bleaching events and that the feature importance summary and threshold sensitivity analysis are generated.

**Acceptance Scenarios**:
1. **Given** the trained model and 2024 environmental rasters, **When** the risk mapping script executes, **Then** a GeoTIFF file is produced where pixel values represent the probability of bleaching (ranging from zero to one).
2. **Given** a high-risk zone identified on the map, **When** the model explanation is queried, **Then** the output identifies the dominant driver (e.g., "High DHW combined with low thermal tolerance") for that specific location.
3. **Given** the model predictions, **When** the threshold sensitivity analysis executes, **Then** the output reports false-positive and false-negative rates for varying probability cutoffs.

### Edge Cases

- What happens when a reef location in the target region has no corresponding species trait data in the Coral Trait Database? (System should exclude or impute with a documented "unknown" flag).
- How does the system handle missing satellite data (cloud cover) for a specific 30-day window? (System should use the nearest valid temporal neighbor or interpolate, but flag the row).
- What if the spatial split results in a test set with zero positive bleaching events? (System should detect this class imbalance and skip the ROC-AUC calculation, reporting a warning instead).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest and merge data from NOAA SST/DHW rasters, UNEP reef geometries, Coral Trait Database, and ReefBase events into a single tabular format with a standardized spatial resolution.. (See US-1)
- **FR-002**: The system MUST compute lagged environmental variables (e.g., 30-day rolling mean SST) and interaction terms between DHW and species thermal tolerance. (See US-1)
- **FR-003**: The system MUST train a Gradient Boosting Machine (XGBoost) using a spatial split strategy (train on Western Pacific, test on Eastern Pacific) to ensure geographic generalization. (See US-2)
- **FR-004**: The system MUST perform 5-fold cross-validation for hyperparameter tuning (max_depth, learning_rate, n_estimators) within the training region. (See US-2)
- **FR-005**: The system MUST generate a probability map (GeoTIFF) for the target region using the fitted model and 2024 environmental data. (See US-3)
- **FR-006**: The system MUST output a permutation importance ranking of predictors to identify top environmental and trait drivers. (See US-2)
- **FR-007**: The system MUST apply a family-wise error correction (Benjamini-Hochberg FDR) to all statistical significance tests regarding predictor importance, where p-values are derived from an empirical permutation test with a sufficient number of permutations, justified as essential to prevent false-positive feature identification in high-dimensional data. (See US-2)
- **FR-008**: The system MUST perform a sensitivity analysis of the classification threshold by sweeping the probability cutoff over a range of representative thresholds and reporting the variation in false-positive and false-negative rates, essential for determining robust operational thresholds in risk mapping. (See US-3)
- **FR-009**: The system MUST perform a Variance Inflation Factor (VIF) analysis on environmental predictors and drop any feature with VIF > 5 prior to model training to address collinearity bias. (See US-2)

### Key Entities

- **Reef-Species Unit**: A unique combination of a reef location (mapped to a 5-km grid cell) and a coral species, serving as the primary observation row.
- **Environmental Profile**: The set of time-aggregated oceanographic variables (SST, DHW, chlorophyll-a, wind speed) associated with a Reef-Species Unit.
- **Trait Profile**: The set of biological characteristics (thermal tolerance, growth rate, colony size) associated with the species in the Reef-Species Unit.
- **Bleaching Label**: The binary outcome (bleached/not) derived from ReefBase historical events.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The ROC-AUC score on the held-out geographic test set is measured via the spatial hold-out set defined in US-2 and compared against the baseline of a random classifier (0.5). (See US-2)
- **SC-002**: The ranking stability of the top-3 predictors identified by permutation importance is measured via multiple bootstrap resamples to assess empirical robustness. (See US-2)
- **SC-003**: The spatial risk map is measured against independent historical bleaching reports (from ReefBase) to calculate the Area Under the Precision-Recall Curve (AUPRC) between predicted probability and the binary observed severity. (See US-3)
- **SC-004**: The computational runtime of the full pipeline is measured against the time limit of the GitHub Actions free-tier runner. (See US-2)
- **SC-005**: The sensitivity analysis of the classification threshold is measured by sweeping the probability cutoff over {0.3, 0.5, 0.7} and reporting the variation in false-positive and false-negative rates. (See US-3)

## Assumptions

- **Dataset Variable Fit**: It is assumed that the Coral Trait Database contains sufficient thermal tolerance data for the dominant species in the UNEP reef dataset; if a species is missing, it will be excluded from the analysis.
- **Observational Framing**: All findings are framed as associational; the model identifies correlations between environmental traits and bleaching, not causal mechanisms, as the data is observational.
- **Compute Constraints**: The analysis assumes that sampling the reef grid to fit within available RAM and running the XGBoost model on a CPU-only environment (limited core configuration) will complete within 6 hours; if the full dataset is too large, a spatial subset will be used.
- **Threshold Justification**: The classification threshold for "high risk" is set at 0.5 by default, justified as the standard decision boundary for binary classification, but a sensitivity analysis (FR-008) is required to validate this choice.
- **Data Availability**: It is assumed that the NOAA Coral Reef Watch and ReefBase APIs/data archives are accessible without authentication or rate-limiting that would block the GitHub Actions runner.
- **Collinearity**: It is assumed that environmental variables (e.g., SST and DHW) may be correlated; FR-009 explicitly addresses this by dropping highly correlated features (VIF > 5) prior to modeling.