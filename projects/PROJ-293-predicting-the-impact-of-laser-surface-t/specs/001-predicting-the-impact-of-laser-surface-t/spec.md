# Feature Specification: Predicting the Impact of Laser Surface Texturing on Wear Resistance

**Feature Branch**: `001-predict-lst-wear`  
**Created**: 2026-07-26  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Laser Surface Texturing on Wear Resistance"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Aggregate and Preprocess LST Wear Data (Priority: P1)

The researcher needs to ingest raw tabular data from diverse sources (OpenML, HuggingFace, literature supplements), standardize the schema (process parameters vs. material properties vs. wear outcomes), and handle missing values to create a clean, analysis-ready dataset.

**Why this priority**: Without a consolidated, clean dataset, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: Can be fully tested by running the data ingestion pipeline on a mock dataset and verifying that the output CSV contains exactly the expected columns with no missing target variables and dropped records for missing predictors.

**Acceptance Scenarios**:

1. **Given** a set of raw CSV files from OpenML and literature supplements with varying column names, **When** the ingestion script runs, **Then** the output dataset contains standardized columns: `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`, and `wear_rate`. The system MUST map source columns to this canonical schema based on a provided `schema_map.json` or standard naming conventions (e.g., 'power' or 'laser_power' -> 'power').
2. **Given** records with missing numerical values in predictor columns, **When** the preprocessing step runs, **Then** any record with a missing required predictor variable (excluding `contact_load` and `sliding_speed` which are handled by FR-009) is dropped from the analysis dataset, and the `missing_record_count` metric is incremented.
3. **Given** categorical `pattern_geometry` entries, **When** one-hot encoding is applied, **Then** the resulting feature matrix contains binary columns for each unique geometry type without data loss.

---

### User Story 2 - Train and Validate Regression Models (Priority: P2)

The researcher needs to train multiple regression models (Linear, Random Forest, Gradient Boosting) on the processed data, perform hyperparameter tuning via grid search, and evaluate performance on a held-out test set to identify the best functional relationship.

**Why this priority**: This is the core analytical engine. It directly addresses the research question by quantifying the relationship between inputs and wear resistance.

**Independent Test**: Can be fully tested by executing the training pipeline on the preprocessed dataset and verifying that the model with the highest R² score on the test set is selected and saved.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset split into [deferred] training and [deferred] testing, **When** the grid search runs, **Then** the system generates a grid of at least 10 distinct total combinations of hyperparameters (e.g., crossing `n_estimators`, `max_depth`, and `learning_rate`) and records the best model parameters.
2. **Given** the trained models, **When** evaluated on the held-out test set, **Then** performance metrics (R², MAE, RMSE) are calculated and logged, and the system selects the model with the highest R² score, regardless of algorithm type.
3. **Given** a trained model, **When** a leave-one-material-class-out cross-validation is performed (e.g., train on steels, test on aluminum), **Then** the generalization error is computed and compared to the standard test error. The system MUST calculate the ratio `test_R²_loo / test_R²_standard`. If this ratio is < 0.8, the system MUST log a WARNING to stdout and record `transferability_failure: true` in the `model_report.json`.

---

### User Story 3 - Interpret Feature Importance and Interactions (Priority: P3)

The researcher needs to extract SHAP values from the best-performing model to rank feature importance and visualize non-linear dependencies, specifically to identify which LST parameters (e.g., scanning speed) dominate wear resistance and how they interact with material properties.

**Why this priority**: This provides the scientific insight ("functional relationship") rather than just a prediction score. It answers *why* certain parameters matter, fulfilling the "virtual prototyping" goal.

**Independent Test**: Can be fully tested by generating SHAP summary plots and dependency plots and verifying that `scanning_speed` and `pattern_geometry` appear as top contributors in the visualization.

**Acceptance Scenarios**:

1. **Given** the best-performing regression model, **When** SHAP values are computed, **Then** a summary plot is generated showing the top 10 features ranked by mean absolute SHAP value.
2. **Given** the SHAP dependency plots, **When** visualized for `power` vs. `scanning_speed`, **Then** non-linear interaction effects are identified if the SHAP interaction value magnitude > 0.1 OR if a polynomial fit (degree 2) to the dependency plot yields an R² > 0.5.
3. **Given** the feature importance rankings, **When** analyzed, **Then** the report explicitly states whether `scanning_speed` or `pattern_geometry` is the dominant predictor, supporting the hypothesis of a non-linear relationship.

---

### Edge Cases

- What happens when the aggregated dataset contains an insufficient number of records after preprocessing? (The system must still run but flag a power limitation).
- How does the system handle a material class in the test set that has zero representation in the training set during leave-one-out validation? (The error should be recorded, but the pipeline must not crash).
- What happens if a specific LST parameter (e.g., `pulse_duration`) has zero variance across all records? (The feature must be dropped or handled to prevent model singularity).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest tabular data from at least 3 distinct sources (OpenML, HuggingFace, literature supplements) and merge them into a single dataframe with standardized column names for process parameters, material properties, and wear outcomes. (See US-1)
- **FR-002**: System MUST drop any record where a required predictor variable (`pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`) is missing. The system MUST NOT impute missing predictor values. However, if `contact_load` or `sliding_speed` are missing, the record MUST be retained with the raw `wear_rate` value and a flag `normalization_method='raw'` set. (See US-1)
- **FR-003**: System MUST train at least three distinct regression models (Linear Regression, Random Forest Regressor, Gradient Boosting Regressor) using scikit-learn on a CPU-only environment. The system MUST NOT utilize GPU acceleration. (See US-2)
- **FR-004**: System MUST perform hyperparameter optimization via grid search over a minimum of 10 distinct total grid points (combinations of `n_estimators`, `max_depth`, and `learning_rate`) using 5-fold cross-validation. (See US-2)
- **FR-005**: System MUST compute and report SHAP (SHapley Additive exPlanations) values for the best-performing model to rank feature importance and visualize non-linear dependencies. (See US-3)
- **FR-006**: System MUST execute a leave-one-material-class-out cross-validation to assess model generalizability across different base materials. If fewer than 3 material classes exist in the dataset, the system MUST fallback to K-Fold cross-validation (K=5) and log a warning. This analysis is framed as a transferability failure analysis. (See US-2)
- **FR-007**: System MUST explicitly frame all reported correlations as associational and avoid causal language unless the dataset includes randomized assignment. (See US-2)
- **FR-008**: System MUST apply a permutation-based significance testing framework (minimum 500 permutations) to generate p-values for feature importance, avoiding standard multiple-comparison corrections designed for independent tests. (See US-3)
- **FR-009**: System MUST normalize raw wear rate values to a specific wear coefficient (K) using Archard's law or a similar standard, accounting for contact load and sliding speed, before aggregation to ensure cross-study comparability. If `contact_load` or `sliding_speed` are missing in the source data, the system MUST retain the record using the raw `wear_rate` and set the flag `normalization_method='raw'`. (See US-1)
- **FR-010**: System MUST perform Variance Inflation Factor (VIF) diagnostics on the feature set. If any pair of features has a VIF > 5, the system MUST exclude one feature from the pair before running permutation tests to mitigate collinearity issues. (See US-3)
- **FR-011**: System MUST perform a sensitivity analysis comparing the performance of the best model trained on the 'normalized-only' subset versus the 'full' (normalized + raw) subset. The system MUST report the difference in R² and MAE between these two models. (See US-2)

### Key Entities

- **LSTRecord**: A single experimental instance containing process parameters (pulse duration, power, scanning speed, pattern geometry), material properties (hardness, elastic modulus), and the target outcome (wear_rate).
- **ModelPerformance**: A record storing the R², MAE, and RMSE metrics for a specific model configuration on both training and test splits.
- **FeatureImportance**: A mapping of each input feature to its SHAP value magnitude, indicating its contribution to the wear_rate prediction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The coefficient of determination (R²) of the best-performing model on the held-out test set is measured against the baseline Linear Regression R² to quantify the improvement from non-linear modeling. (See US-2)
- **SC-002**: The feature importance ranking derived from SHAP values is measured against an independent held-out experimental dataset or a distinct physical mechanism (e.g., microstructural evidence) not correlated with the training features to validate the model's physical interpretability. If the dataset lacks a `microstructural_features` column, the system MUST report `validation_target_unavailable` and proceed with the associational analysis only. (See US-3)
- **SC-003**: The generalization error (drop in R²) during leave-one-material-class-out cross-validation is measured against the standard test error to assess the robustness of the functional relationship across material classes. (See US-2)
- **SC-004**: The number of records in the final aggregated dataset is measured against the target threshold. The project succeeds if the final count >= 300; otherwise, a warning is triggered and the analysis proceeds with a power limitation flag. The count must be split into `normalized_count` and `raw_count`. (See US-1)
- **SC-005**: The runtime of the entire pipeline (ingestion to SHAP generation) is measured against the 6-hour GitHub Actions free-tier limit. The pipeline MUST complete within 6 hours; if it exceeds this, the run is marked as failed. (See FR-003)
- **SC-006**: The system MUST define a measurable threshold for insufficient data. If the `normalized_count` (records with valid Archard normalization) is < 100, the system MUST trigger a `data_insufficiency_error` and halt the primary regression analysis, proceeding only to the sensitivity analysis (FR-011). (See US-2)

## Assumptions

- **Assumption about data availability**: The open-access repositories and literature supplements contain sufficient records to meet the N=300 target after standardization. The ingestion pipeline is designed to handle missing `contact_load` or `sliding_speed` by retaining records with raw `wear_rate` values (flagged), ensuring the dataset size does not drop below the critical threshold for analysis.
- **Assumption about inference framing**: Since the data is aggregated from observational studies without random assignment, all findings regarding the relationship between LST parameters and wear resistance will be framed as associational, not causal.
- **Assumption about compute constraints**: The dataset size (post-sampling if necessary) will fit within the available RAM and disk limits of the GitHub Actions free runner, and the total analysis time will remain within the 6-hour limit.
- **Assumption about threshold justification**: Any decision cutoffs used in data filtering or model selection (e.g., minimum R² for model acceptance) will be justified by community standards (e.g., R² > 0.7 as a benchmark for "good" fit in materials science) and sensitivity analysis will be performed on these cutoffs.
- **Assumption about measurement validity**: The wear_rate values in the aggregated dataset are derived from validated tribological testing methods (e.g., pin-on-disk) and are comparable across different studies after normalization to a specific wear coefficient.
- **Assumption about predictor collinearity**: If `power` and `scanning_speed` are used to derive a `line_energy` feature, the model will not claim independent predictive effects for all three; instead, collinearity diagnostics (VIF) will be run, and the joint relationship will be described descriptively.