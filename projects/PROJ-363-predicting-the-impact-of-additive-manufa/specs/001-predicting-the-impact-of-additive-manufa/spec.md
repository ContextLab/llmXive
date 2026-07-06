# Feature Specification: Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

**Feature Branch**: `001-predicting-impact-of-additive-manufacturing-parameters-on-porosity`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

As a materials researcher, I need to download a public LPBF 316L dataset, parse the CSV files, handle missing values, and normalize the numerical features so that I have a clean, standardized dataset ready for modeling.

**Why this priority**: This is the foundational step; without clean, normalized data, no modeling or analysis can proceed. It delivers a tangible artifact (the processed dataset) that is independently valuable.

**Independent Test**: Can be fully tested by verifying the existence of a processed CSV file containing normalized columns for laser power, scan speed, hatch spacing, layer thickness, and porosity, with no missing values.

**Acceptance Scenarios**:

1. **Given** a public LPBF 316L dataset URL is available, **When** the system downloads and parses the CSV, **Then** a local CSV file with all required columns (power, speed, hatch, thickness, porosity) exists.
2. **Given** the raw dataset contains missing values in numerical columns, **When** the preprocessing step runs, **Then** the missing values are imputed using a defined strategy (e.g., mean/median) and the resulting dataset has zero nulls.
3. **Given** the raw numerical features have different scales, **When** normalization is applied, **Then** all input features (power, speed, hatch, thickness) are scaled to the range [0, 1].

---

### User Story 2 - Model Training and Validation (Priority: P2)

As a data scientist, I need to train Gradient Boosting and MLP regression models on the preprocessed data using 5-fold cross-validation to determine which model best predicts porosity from process parameters.

**Why this priority**: This delivers the core predictive capability. While dependent on US-1, the training logic and validation metrics can be tested independently of the specific dataset source once data is available.

**Independent Test**: Can be fully tested by running the training script on a sample dataset and verifying that two trained model objects (Gradient Boosting, MLP) are saved along with a JSON report containing RMSE and R² scores for each fold.

**Acceptance Scenarios**:

1. **Given** a normalized dataset, **When** the training script executes, **Then** two distinct model files (`.pkl` or `.pt`) are generated in the output directory.
2. **Given** a dataset of size N, **When** 5-fold cross-validation is performed, **Then** the system outputs a summary of RMSE and R² for each of the 5 folds and the mean performance.
3. **Given** the training environment has no GPU, **When** the MLP model trains, **Then** it completes successfully using CPU-only computation within the 6-hour job limit.

---

### User Story 3 - Explainability and Statistical Analysis (Priority: P3)

As a domain expert, I need to generate SHAP plots and perform statistical significance testing on feature contributions to understand which process parameters most significantly influence porosity, ensuring the model's predictions are physically interpretable.

**Why this priority**: This provides the scientific insight required to fill the literature gap. It is the "value-add" that transforms a black-box prediction into a scientific finding.

**Independent Test**: Can be fully tested by verifying the generation of a SHAP summary plot image and a statistical report table showing 95% bootstrap confidence intervals for feature importance.

**Acceptance Scenarios**:

1. **Given** a trained Gradient Boosting model, **When** SHAP analysis is run, **Then** a summary plot visualizing the marginal effect of each parameter (power, speed, etc.) on porosity is saved.
2. **Given** the feature importance scores from the model, **When** Permutation Importance with 1,000 permutations is applied, **Then** a table is generated identifying which parameters have a statistically significant influence (p < 0.05) on porosity.
3. **Given** the derived feature (Volumetric Energy Density), **When** the analysis runs, **Then** its relative importance is reported alongside the raw parameters to validate physical intuition, provided it is not used simultaneously with raw parameters in the same model.

---

### Edge Cases

- **What happens when the public dataset has a different column naming convention?** The system must map common synonyms (e.g., "laser_power" vs "P") to the standard schema or fail gracefully with a clear error message listing expected vs. found columns.
- **How does the system handle a dataset with zero porosity variance?** If all porosity values are identical (or nearly so), the regression metrics (R²) will be undefined or zero; the system must detect this and flag it as a "Degenerate Dataset" rather than crashing.
- **What happens if the derived Volumetric Energy Density calculation results in division by zero?** (e.g., speed = 0). The system must filter out such rows during preprocessing or assign a safe sentinel value, logging the exclusion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download a public LPBF 316L dataset from a specified URL (Zenodo/OpenML) and parse it into a structured DataFrame (See US-1).
- **FR-002**: System MUST impute missing numerical values using the median of the respective column and normalize all input features to the range [0, 1] (See US-1).
- **FR-003**: System MUST calculate the derived feature Volumetric Energy Density ($E_v = P / (v \cdot h \cdot t)$) for every record where scan_speed > 0, hatch_spacing > 0, and layer_thickness > 0. If raw parameters are unavailable but Ev is provided, use the provided column; otherwise, skip calculation (See US-1).
- **FR-004**: System MUST train a Gradient Boosting Regressor and a Multi-Layer Perceptron (MLP) Regressor using 5-fold cross-validation (See US-2).
- **FR-005**: System MUST compute and report RMSE and R² metrics for each fold and the aggregate mean performance for both models (See US-2).
- **FR-006**: System MUST generate SHAP summary plots to visualize the marginal effect of each parameter on predicted porosity (See US-3).
- **FR-007**: System MUST perform Permutation Importance testing with 1,000 permutations and calculate 95% Bootstrap Confidence Intervals on SHAP values to determine statistical significance of parameters (p < 0.05) (See US-3).
- **FR-008**: System MUST save trained model artifacts, performance metrics, and visualization plots to the project directory (See US-2, US-3).
- **FR-009**: System MUST NOT utilize GPU acceleration during training or inference (See US-2).
- **FR-010**: System MUST NOT include both raw parameters and Volumetric Energy Density as simultaneous inputs in the same model to avoid multicollinearity (See US-3).

### Key Entities

- **ProcessParameters**: Represents the input settings for LPBF, including Laser Power (W), Scan Speed (mm/s), Hatch Spacing (mm), and Layer Thickness (mm).
- **PorosityMeasurement**: Represents the output variable, quantifying the percentage of void space in the printed 316L part.
- **VolumetricEnergyDensity**: A derived entity calculated from ProcessParameters, representing the energy input per unit volume (J/mm³).
- **ModelPerformance**: Represents the evaluation metrics (RMSE, R²) associated with a specific model and cross-validation fold.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model predictive accuracy (R²) is measured against the held-out test set; success is defined as R² ≥ 0.65 or strictly greater than a dummy regressor baseline (See US-2).
- **SC-002**: Feature significance (p-values from Permutation Importance) is measured against the standard alpha level of 0.05 to identify which parameters drive porosity (See US-3).
- **SC-003**: Computational feasibility is measured against the free-tier CI limits (≤6h runtime, ≤7GB RAM, CPU-only) to ensure the methodology is reproducible without specialized hardware (See US-2).
- **SC-004**: Data completeness is measured against the requirement for zero missing values in the final training set after imputation (See US-1).

## Assumptions

- **Dataset Availability**: A public dataset containing 316L LPBF parameters (power, speed, hatch, thickness) and measured porosity exists on Zenodo or OpenML and is accessible via `wget` without authentication.
- **Dataset Variable Fit**: The identified public dataset contains all required variables (power, speed, hatch, thickness, porosity). If the dataset lacks a specific variable (e.g., only provides energy density but not raw parameters), the project will use the provided energy density directly, and the derived feature engineering step will be adjusted accordingly.
- **Observational Nature**: The study is purely observational; findings will be framed as **associational** relationships between parameters and porosity, not causal effects, due to the lack of randomized controlled trials in the source data.
- **Compute Constraints**: The entire pipeline (download, preprocess, train 2 models, 5-fold CV, SHAP analysis) will complete within 6 hours on a GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) using CPU-only execution.
- **Measurement Validity**: The porosity values in the source dataset are derived from validated measurement techniques (e.g., micro-CT or optical microscopy) as reported in the dataset's metadata, ensuring the ground truth is reliable.
- **Threshold Justification**: No arbitrary decision thresholds (e.g., for classifying "high" vs "low" porosity) are introduced in this regression study; the analysis remains continuous. If a threshold is needed for future classification work, a sensitivity analysis will be required.
- **Power Consideration**: Sample size and statistical power are limited by the available public dataset size; the analysis will proceed with the available N, and any power limitations will be explicitly acknowledged in the final report.
- **Collinearity**: Since Volumetric Energy Density is mathematically derived from the raw parameters, the model will not claim independent predictive effects for both the raw parameters and the derived density simultaneously in a way that implies causality; collinearity diagnostics will be reported if both are used as inputs.