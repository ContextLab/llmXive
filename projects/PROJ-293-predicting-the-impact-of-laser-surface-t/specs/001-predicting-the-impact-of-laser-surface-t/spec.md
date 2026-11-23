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

1. **Given** a set of raw CSV files from OpenML and literature supplements with varying column names, **When** the ingestion script runs, **Then** the output dataset contains standardized columns: `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`, and `wear_rate`. The system MUST map source columns to this canonical schema based on a provided `schema_map.json` or standard naming conventions (e.g., 'power' or 'laser_power' -> 'power'). If the source dataset (e.g., 'face-shape-rule-set') lacks these specific LST columns, the system MUST halt and report `data_schema_mismatch` error. (See FR-001, FR-002, FR-009)
2. **Given** records with missing numerical values in predictor columns, **When** the preprocessing step runs, **Then** any record with a missing required predictor variable (excluding `contact_load` and `sliding_speed` which are handled by FR-009) is dropped from the analysis dataset, and the `missing_record_count` metric is incremented. (See FR-002)
3. **Given** categorical `pattern_geometry` entries, **When** one-hot encoding is applied, **Then** the resulting feature matrix contains binary columns for each unique geometry type without data loss. (See FR-001)
4. **Given** the aggregated dataset, **When** the validation step runs, **Then** the system MUST verify the presence of at least 3 distinct sources. If fewer than 3 sources are found, the system MUST log a `data_source_limitation` warning but proceed. If the dataset lacks the required `wear_rate` target or key LST predictors, the system MUST trigger a `data_insufficiency_error` and halt. (See FR-001, FR-012)

---

### User Story 2 - Train and Validate Regression Models (Priority: P2)

The researcher needs to train multiple regression models (Linear, Random Forest, Gradient Boosting) on the processed data, perform hyperparameter tuning via grid search, and evaluate performance on a held-out test set to identify the best functional relationship.

**Why this priority**: This is the core analytical engine. It directly addresses the research question by quantifying the relationship between inputs and wear resistance.

**Independent Test**: Can be fully tested by executing the training pipeline on the preprocessed dataset and verifying that the model with the highest R² score on the test set is selected and saved.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset split into [deferred] training and [deferred] testing, **When** the grid search runs, **Then** the system generates a grid of at least 10 distinct total combinations of hyperparameters (e.g., crossing `n_estimators`, `max_depth`, and `learning_rate`) and records the best model parameters. (See FR-004)
2. **Given** the trained models, **When** evaluated on the held-out test set, **Then** performance metrics (R², MAE, RMSE) are calculated and logged, and the system selects the model with the highest R² score, regardless of algorithm type. (See FR-003)
3. **Given** a trained model, **When** a leave-one-material-class-out cross-validation is performed (e.g., train on steels, test on aluminum), **Then** the generalization error is computed and compared to the standard test error. The system MUST calculate the ratio `test_R²_loo / test_R²_standard`. If this ratio is < 0.8, the system MUST log a WARNING to stdout and record `transferability_failure_flag: true` in the `model_report.json`. If `test_R²_standard` is 0 or undefined, or if `test_R²_loo` is undefined, the ratio is set to 0 and a `ratio_undefined: true` flag is recorded. (See FR-006, SC-003)
4. **Given** the full dataset, **When** the sensitivity analysis runs, **Then** the system trains a model on the 'normalized-only' subset and another on the 'full' (normalized + raw) subset. The system MUST report the difference in R² and MAE between these two models. If the 'raw' subset fails the statistical validity check (FR-017), the system MUST exclude it from this analysis and report `raw_subset_invalid`. (See FR-011, FR-017)

---

### User Story 3 - Interpret Feature Importance and Interactions (Priority: P3)

The researcher needs to extract SHAP values from the best-performing model to rank feature importance and visualize non-linear dependencies, specifically to identify which LST parameters (e.g., scanning speed) dominate wear resistance and how they interact with material properties.

**Why this priority**: This provides the scientific insight ("functional relationship") rather than just a prediction score. It answers *why* certain parameters matter, fulfilling the "virtual prototyping" goal.

**Independent Test**: Can be fully tested by generating SHAP summary plots and dependency plots and verifying that `scanning_speed` and `pattern_geometry` appear as top contributors in the visualization.

**Acceptance Scenarios**:

1. **Given** the best-performing regression model, **When** SHAP values are computed, **Then** A summary plot is generated showing the top features ranked by mean absolute SHAP value. (See FR-005)
2. **Given** the SHAP dependency plots, **When** visualized for `power` vs. `scanning_speed`, **Then** non-linear interaction effects are identified if the SHAP interaction value magnitude > 0.1 OR if a polynomial fit (degree 2) to the dependency plot yields an R² > 0.5. The system MUST validate these findings against permutation testing (FR-008) and VIF diagnostics (FR-010). (See FR-005, FR-008, FR-010, SC-008)
3. **Given** the feature importance rankings, **When** analyzed, **Then** the report explicitly states whether `scanning_speed` or `pattern_geometry` is the dominant predictor, supporting the hypothesis of a non-linear relationship. (See FR-005)

---

### User Story 4 - Data Availability Validation (Priority: P1)

The researcher needs to validate that the aggregated dataset meets the minimum requirements for the intended analysis. If the dataset is insufficient (N < 300 or missing targets), the system must gracefully degrade the scope rather than failing silently.

**Why this priority**: Prevents the pipeline from producing meaningless results on invalid data and ensures the research question is reframed appropriately if data is scarce.

**Independent Test**: Can be fully tested by providing a mock dataset with < 100 records and verifying the system halts with the correct error code, or providing a dataset with 150 records and verifying the system proceeds with a warning.

**Acceptance Scenarios**:

1. **Given** an aggregated dataset with < 100 records, **When** the validation step runs, **Then** the system MUST trigger a `data_insufficiency_error` and halt (exit code 1). (See SC-004, SC-006)
2. **Given** an aggregated dataset with 100-299 records, **When** the validation step runs, **Then** the system MUST output a warning `data_insufficiency_warning`, proceed with the analysis, and set the `study_scope` to "pilot_study" in the report. (See SC-004)
3. **Given** a dataset with >= 300 records, **When** the validation step runs, **Then** the system proceeds normally with `study_scope` set to "full_study". (See SC-004)

---

### Edge Cases

- What happens when the aggregated dataset contains an insufficient number of records after preprocessing? (The system must still run but flag a power limitation).
- How does the system handle a material class in the test set that has zero representation in the training set during leave-one-out validation? (The error should be recorded, but the pipeline must not crash).
- What happens if a specific LST parameter (e.g., `pulse_duration`) has zero variance across all records? (The feature must be dropped or handled to prevent model singularity).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest tabular data from at least 3 distinct sources (OpenML, HuggingFace, literature supplements) and merge them into a single dataframe with standardized column names for process parameters, material properties, and wear outcomes. A "distinct source" is defined as a unique repository URL or a distinct published paper with a separate supplement. The system MUST verify the presence of LST-specific columns (pulse_duration, power, scanning_speed, wear_rate) before proceeding. (See US-1)
- **FR-002**: System MUST drop any record where a required predictor variable (`pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`) is missing. The system MUST NOT impute missing predictor values. However, if `contact_load` or `sliding_speed` are missing, the record MUST be retained with the raw `wear_rate` value and a flag `normalization_method='raw'` set, as these are optional for the *normalized* target calculation only. These 'raw' records MUST NOT be mixed into the primary training set (see FR-013). (See US-1)
- **FR-003**: System MUST train at least three distinct regression models (Linear Regression, Random Forest Regressor, Gradient Boosting Regressor) using scikit-learn on a CPU-only environment. The system MUST NOT utilize GPU acceleration. (See US-2)
- **FR-004**: System MUST perform hyperparameter optimization via grid search over a minimum of 10 distinct total grid points (combinations of `n_estimators`, `max_depth`, and `learning_rate`) using 5-fold cross-validation. (See US-2)
- **FR-005**: System MUST compute and report SHAP (SHapley Additive exPlanations) values for the best-performing model to rank feature importance and visualize non-linear dependencies. (See US-3)
- **FR-006**: System MUST execute a leave-one-material-class-out cross-validation to assess model generalizability across different base materials. If fewer than 3 material classes exist in the dataset, the system MUST fallback to K-Fold cross-validation (K=5), log a warning, and explicitly state that the research question has shifted to "within-material prediction" rather than "cross-material generalizability". If the normalized subset size per class is < 30, the system MUST fallback to Linear Regression only to avoid overfitting on small samples. (See US-2)
- **FR-007**: System MUST explicitly frame all reported correlations as associational and avoid causal language unless the dataset includes randomized assignment. (See US-2)
- **FR-008**: System MUST apply a permutation-based significance testing framework (minimum 2000 permutations) to generate p-values for feature importance. If no features meet the p < 0.05 threshold, the system MUST report `no_significant_features`. If the variance of p-values across features is > 0.05, the system MUST flag `unstable_significance`. A feature is considered "suggestive" if p < 0.1 but >= 0.05. (See US-3)
- **FR-009**: System MUST normalize raw wear rate values to a specific wear coefficient (K) using Archard's law. The system MUST first convert `wear_rate` (linear or mass) to Volume (V) using density and contact area data from the source metadata. If `contact_load` or `sliding_speed` are missing, the system MUST retain the record using the raw `wear_rate` and set the flag `normalization_method='raw'`. (See US-1)
- **FR-010**: System MUST perform Variance Inflation Factor (VIF) diagnostics on the feature set. If any pair of features has a VIF > 5, the system MUST exclude the feature with the highest VIF value from the pair and re-calculate until all VIFs are ≤ 5, to mitigate collinearity issues. (See US-3)
- **FR-011**: System MUST perform a sensitivity analysis comparing the performance of the best model trained on the 'normalized-only' subset versus the 'full' (normalized + raw) subset. The system MUST report the difference in R² and MAE between these two models. (See US-2)
- **FR-012**: System MUST report a `data_source_limitation` warning if fewer than 3 distinct sources are found, but must proceed with available data. (See US-1)
- **FR-013**: System MUST train the primary regression model (FR-003) ONLY on the subset of records where `normalization_method='normalized'`. The 'raw' subset is reserved exclusively for the sensitivity analysis (FR-011) and must not be mixed into the primary training set. (See US-2)
- **FR-014**: System MUST perform a power analysis before model training. If the power analysis indicates < 0.8 power for the expected effect size (α=0.05), the system MUST switch to a simpler model (Linear Regression) or report a `power_insufficiency` warning. (See US-2)
- **FR-015**: System MUST define a deterministic resolution strategy for VIF > 5 (see FR-010) and ensure the final model uses only the reduced feature set. (See US-3)
- **FR-016**: System MUST enforce a runtime limit of 6 hours for the entire pipeline (ingestion to SHAP generation). If the pipeline exceeds this limit, the system MUST terminate with exit code 1 and log a `runtime_timeout` error. (See US-2)
- **FR-017**: System MUST perform a statistical validity check on the 'raw' subset before including it in the sensitivity analysis. The system MUST run Shapiro-Wilk (normality) and Levene's (homogeneity) tests. If p < 0.05 for either, the 'raw' subset MUST be excluded from the sensitivity analysis and the system MUST report `raw_subset_invalid`. (See US-2)
- **FR-018**: System MUST handle unit conversions for Archard's law normalization. If `wear_rate` is reported in linear (mm) or mass (mg) units, the system MUST apply density and geometry conversions to derive Volume (V) before calculating the wear coefficient K. (See US-1)

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
- **SC-002**: The feature importance ranking derived from SHAP values is measured against an independent held-out experimental dataset or a distinct physical mechanism (e.,g., microstructural evidence) not correlated with the training features to validate the model's physical interpretability. If the dataset lacks a `microstructural_features` column, the system MUST perform a 'physical plausibility check' by verifying SHAP signs against Archard's law (e.g., load should positively correlate with wear). If signs contradict physics, the system MUST flag `physical_plausibility_failure`. If no external validation is possible, the study MUST be classified as "purely associational" and report `validation_target_unavailable` as a known limitation, not a success. (See US-3)
- **SC-003**: The generalization error (drop in R²) during leave-one-material-class-out cross-validation is measured against the standard test error to assess the robustness of the functional relationship across material classes. Specifically, the system MUST report the ratio `test_R²_loo / test_R²_standard` and the `transferability_failure_flag` if the ratio < 0.8. If the fallback to K-Fold is triggered (FR-006), the system MUST report the within-material R² and the `fallback_active` flag. (See US-2)
- **SC-004**: The number of records in the final aggregated dataset is measured against the target threshold. The project succeeds if the final count >= 300 (exit code 0). If 100 <= count < 300, the system MUST output exit code 2 and a warning `data_insufficiency_warning`, proceeding with a "pilot_study" scope. If count < 100, the system MUST trigger a `data_insufficiency_error` and halt (exit code 1). The count must be split into `normalized_count` and `raw_count`. If `normalized_count` < 100, SC-006 takes precedence and the system halts. (See US-1)
- **SC-005**: The runtime of the entire pipeline (ingestion to SHAP generation) is measured against the 6-hour limit defined in FR-016. The pipeline MUST complete within 6 hours; if it exceeds this, the run is marked as failed (exit code 1). (See FR-016)
- **SC-006**: The system MUST define a measurable threshold for insufficient data. If the `normalized_count` (records with valid Archard normalization) is < 100, the system MUST trigger a `data_insufficiency_error` and halt the primary regression analysis, proceeding only to the sensitivity analysis (FR-011) if `total_count` >= 100. (See US-2)
- **SC-007**: The data ingestion pipeline MUST report a `data_schema_mismatch` error if the standardized columns cannot be mapped from the source data (specifically if LST-specific columns like `pulse_duration` are missing), and MUST halt if the number of distinct sources is < 1. (See US-1)
- **SC-008**: The statistical significance of feature importance rankings MUST be validated by permutation testing (p < 0.05). If no features meet this threshold, the system MUST report `no_significant_features`. If the variance of p-values is > 0.05, the system MUST report `unstable_significance`. (See US-3)

## Assumptions

- **Assumption about data availability**: The project assumes that at least 300 records with complete LST parameters can be aggregated from open sources. If this threshold is not met, the project scope degrades to a pilot study (N < 300) with reduced statistical power, and the research question shifts to "exploratory analysis" rather than "predictive modeling". The ingestion pipeline is designed to handle missing `contact_load` or `sliding_speed` by retaining records with raw `wear_rate` values (flagged), ensuring the dataset size does not drop below the critical threshold for analysis.
- **Assumption about inference framing**: Since the data is aggregated from observational studies without random assignment, all findings regarding the relationship between LST parameters and wear resistance will be framed as associational, not causal.
- **Assumption about compute constraints**: The dataset size (post-sampling if necessary) will fit within the available RAM and disk limits of the GitHub Actions free runner, and the total analysis time will remain within the 6-hour limit.
- **Assumption about threshold justification**: Any decision cutoffs used in data filtering or model selection (e.g., minimum R² for model acceptance) will be justified by community standards (e.g., R² > 0.7 as a benchmark for "good" fit in materials science) and sensitivity analysis will be performed on these cutoffs.
- **Assumption about measurement validity**: The wear_rate values in the aggregated dataset are derived from validated tribological testing methods (e.g., pin-on-disk) and are comparable across different studies after normalization to a specific wear coefficient.
- **Assumption about predictor collinearity**: If `power` and `scanning_speed` are used to derive a `line_energy` feature, the model will not claim independent predictive effects for all three; instead, collinearity diagnostics (VIF) will be run, and the joint relationship will be described descriptively.
- **Assumption about dataset content**: The system assumes that the provided dataset URLs (e.g., 'face-shape-rule-set') may contain LST data only if the schema validation (US-1 Scenario 1) confirms the presence of required columns. If the dataset name suggests a mismatch (e.g., "face-shape") but the schema validation passes, the system proceeds with a warning `schema_name_mismatch`. If the schema validation fails, the system halts.