# Feature Specification: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

**Feature Branch**: `001-predicting-adhesion-strength`
**Created**: 2026-06-28
**Status**: Draft
**Input**: User description: "Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system MUST retrieve, parse, and standardize raw adhesion data from public repositories (NIST, Zenodo, Materials Project) into a unified analysis-ready format. This includes handling missing values, encoding categorical treatment types, and scaling continuous parameters.

**Why this priority**: Without a clean, unified dataset, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: The pipeline can be executed end-to-end on a sample of 100 records; it outputs a single CSV file with standardized columns and no missing critical values, which can be loaded into a pandas DataFrame without error.

**Acceptance Scenarios**:

1. **Given** raw CSV files from NIST and Zenodo containing mixed units and missing plasma power values, **When** the ingestion script runs, **Then** the output CSV contains a standardized `plasma_power_watts` column with median imputation applied to missing entries, and all units are converted to SI standards.
2. **Given** a dataset where `treatment_type` contains variations like "O2 Plasma", "Oxygen Plasma", and "O2-plasma", **When** the preprocessing step executes, **Then** these are mapped to a single canonical category "Oxygen Plasma" in the `treatment_type` column.
3. **Given** a record with a missing `substrate_roughness_nm` value, **When** the pipeline processes the data, **Then** the value is replaced with the median roughness of the specific substrate class, and a log entry flags the imputation.

---

### User Story 2 - Predictive Model Training and Validation (Priority: P2)

The system MUST train multiple regression models (Random Forest, Gradient Boosting, Linear Regression) on the prepared dataset using stratified cross-validation to predict adhesion strength from surface treatment parameters.

**Why this priority**: This is the core research activity. It directly addresses the research question by attempting to quantify the relationship between inputs and outputs.

**Independent Test**: The training script completes within 4 hours on a CPU-only runner, outputs a JSON file containing the best model's hyperparameters, validation R² score, and RMSE, and saves the model artifact.

**Acceptance Scenarios**:

1. **Given** a training set of 500 records split 70/15/15, **When** the model training job runs with a grid search of 50 combinations, **Then** the system selects the Random Forest model (or equivalent best performer) and reports a validation R² ≥ 0.0 (indicating no negative performance) and a runtime < 3.5 hours.
2. **Given** the trained models, **When** the evaluation step runs on the held-out test set, **Then** the system outputs a `test_r2`, `test_rmse`, and `test_mae` for each model, stored in a results JSON file.
3. **Given** the best performing model, **When** a 5-fold cross-validation is re-run on the full training set, **Then** the mean R² across folds is within 0.05 of the validation R² reported during grid search, confirming stability.

---

### User Story 3 - Statistical Significance and Interpretability Reporting (Priority: P3)

The system MUST perform a permutation test to establish statistical significance of the model's performance and generate SHAP values to interpret the contribution of each treatment parameter to adhesion strength.

**Why this priority**: This validates that the observed relationships are not due to chance and provides actionable insights for engineers, fulfilling the "explain variance" and "quantitative relationship" goals of the research question.

**Independent Test**: The analysis script generates a permutation p-value < 0.05 (or reports the specific value) and a SHAP summary plot image, both saved to the artifacts directory.

**Acceptance Scenarios**:

1. **Given** the best model and the test set, **When** a permutation test with 1,000 shuffles is executed, **Then** the system calculates a p-value and reports it in the final report; if p < 0.05, the relationship is flagged as statistically significant.
2. **Given** the best model, **When** SHAP analysis is performed, **Then** the system outputs a summary plot (PNG) and a JSON file ranking features by mean absolute SHAP value, clearly identifying the top 3 predictors (e.g., plasma power, exposure time).
3. **Given** the full results, **When** the final report is generated, **Then** it includes a section stating the proportion of variance explained (R²) with 95% confidence intervals derived from bootstrapping, and a statement on whether the R² ≥ 0.5 target was met.

### Edge Cases

- What happens when a specific polymer-substrate pair has fewer than 5 data points in the dataset? (System must exclude or aggregate to prevent overfitting on noise).
- How does the system handle a dataset where `plasma_power` is reported in kW instead of W, or `exposure_time` in minutes instead of seconds? (System must detect unit mismatches via schema validation and apply conversion factors or raise a specific error).
- What if the best model is a simple Linear Regression with R² < 0.1? (System must still report this result as a valid "null" finding, rather than crashing or hiding the result).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST retrieve datasets from NIST, Zenodo, and Materials Project using `wget` or `curl` and parse them into a unified pandas DataFrame structure. (See US-1)
- **FR-002**: The system MUST impute missing numeric values using the median of the specific feature and one-hot encode categorical treatment types. (See US-1)
- **FR-003**: The system MUST train at least three distinct regression models (Random Forest, Gradient Boosting, Linear Regression) using scikit-learn with a maximum of 50 hyperparameter combinations. (See US-2)
- **FR-004**: The system MUST perform a stratified 70/15/15 train/validation/test split based on `treatment_type` to ensure representation across categories. (See US-2)
- **FR-005**: The system MUST execute a permutation test with exactly 1,000 shuffles to calculate the p-value for the observed R² score. (See US-3)
- **FR-006**: The system MUST generate SHAP values for the best performing model to rank feature importance. (See US-3)
- **FR-007**: The system MUST output a final report containing R², RMSE, MAE, p-value, and feature importance rankings in both JSON and Markdown formats. (See US-3)

### Key Entities

- **TreatmentRecord**: Represents a single experimental observation. Key attributes: `treatment_type`, `plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`.
- **ModelArtifact**: Represents a trained model instance. Key attributes: `model_type`, `hyperparameters`, `validation_r2`, `test_r2`, `shap_values`.
- **AnalysisResult**: Represents the aggregate outcome of the research. Key attributes: `best_model_type`, `final_r2`, `p_value`, `top_predictors`, `confidence_interval`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of variance in adhesion strength explained by the model is measured against the target of R² ≥ 0.5. (See US-2, US-3)
- **SC-002**: The statistical significance of the model's predictive power is measured against the threshold of p < 0.05 via permutation test. (See US-3)
- **SC-003**: The model's predictive accuracy is measured against the test set using RMSE and MAE metrics. (See US-2)
- **SC-004**: The feature importance ranking is measured by the stability of SHAP values across 5-fold cross-validation (standard deviation of SHAP mean < 0.1). (See US-3)
- **SC-005**: The total compute time for the entire pipeline (ingestion to reporting) is measured against the 6-hour free-tier CI limit. (See US-1, US-2)

## Assumptions

- The public datasets (NIST, Zenodo, Materials Project) contain the required variables: plasma power, exposure time, chemical concentration, polymer surface energy, substrate roughness, and adhesion strength. [NEEDS CLARIFICATION: Does the specific Zenodo dataset (DOI) contain `polymer_surface_energy` and `substrate_roughness` for all records, or will these require imputation or exclusion?]
- The relationship between treatment parameters and adhesion strength is primarily associational; causal claims will not be made without randomization data.
- The dataset size is sufficient for a 70/15/15 split (minimum 200 records) to allow for meaningful model training and testing.
- The free-tier GitHub Actions runner (2 CPU, 7GB RAM) is sufficient for training Random Forest and Gradient Boosting models on a dataset of < 5,000 records.
- The "best" model is selected solely based on validation R², not on model complexity or training time.
- SHAP analysis will be performed using the `shap` library's CPU-compatible `TreeExplainer` for tree-based models to ensure feasibility within the 6-hour limit.
