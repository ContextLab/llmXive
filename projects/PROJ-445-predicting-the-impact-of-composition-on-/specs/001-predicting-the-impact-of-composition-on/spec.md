# Feature Specification: Predicting the Impact of Composition on the Glass Transition Temperature of Chalcogenide Glasses

**Feature Branch**: `001-glass-transition-prediction`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "How do mean coordination number and chemical heterogeneity jointly determine the glass transition temperature in chalcogenide networks?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load and preprocess chalcogenide composition data with feature engineering (Priority: P1)

The researcher MUST be able to download the chalcogenide dataset from the 2022 study's supplementary repository, compute compositional descriptors (mean coordination number, electronegativity variance, atomic radius variance), and prepare a stratified train/test split to enable baseline model training.

**Why this priority**: This is the foundational step; without valid data loading and feature computation, no modeling or analysis can proceed. It delivers immediate value by validating dataset-variable fit and enabling all downstream work.

**Independent Test**: Can be fully tested by executing the data loading script and verifying that (a) the dataset loads without errors, (b) all required features are computed for each sample, and (c) the train/test split maintains ≥80% training proportion with stratification by chemical family.

**Acceptance Scenarios**:

1. **Given** the supplementary dataset is accessible at the documented URL, **When** the data loading script executes, **Then** all samples are loaded with their Tg values and elemental compositions intact
2. **Given** elemental compositions are present, **When** feature computation runs, **Then** mean coordination number, electronegativity variance, and atomic radius variance are computed for ≥95% of samples (allowing for missing elemental data)
3. **Given** the full dataset is prepared, **When** the stratified split executes, **Then** the training set contains ≥80% of samples and the test set contains ≤20%, with both sets preserving the chemical family distribution

---

### User Story 2 - Train and evaluate gradient boosting model against linear baseline (Priority: P2)

The researcher MUST be able to train a Gradient Boosting Regressor using scikit-learn on CPU with 5-fold cross-validation, tune hyperparameters, and compare performance (RMSE, R²) against a linear regression baseline to confirm non-linear interaction effects.

**Why this priority**: This is the core analytical work that answers the research question. It must succeed to demonstrate whether chemical heterogeneity contributes beyond mean coordination number alone.

**Independent Test**: Can be fully tested by executing the training script and verifying that (a) the gradient boosting model trains without GPU/CUDA dependencies, (b) 5-fold CV completes within the 6-hour CI time limit, and (c) performance metrics (RMSE, R²) are computed for both models on the held-out test set.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset is available, **When** the gradient boosting model trains, **Then** the model completes training using only CPU resources (no CUDA/device_map="cuda" or 8-bit quantization)
2. **Given** the model trains, **When** 5-fold cross-validation runs, **Then** the full CV cycle completes within ≤6 hours on a free-tier CI runner (2 CPU, ~7 GB RAM)
3. **Given** both gradient boosting and linear baseline models are trained, **When** test evaluation runs, **Then** RMSE and R² scores are computed and logged for both models on the held-out test set

---

### User Story 3 - Generate SHAP analysis and feature importance report (Priority: P3)

The researcher MUST be able to apply SHAP (SHapley Additive exPlanations) analysis to quantify the contribution of each descriptor to Tg predictions and produce a report identifying which features drive model predictions.

**Why this priority**: This delivers the interpretability layer that directly addresses the research question about joint determination. It is essential for distinguishing topological constraints from chemical effects but depends on successful model training.

**Independent Test**: Can be fully tested by executing the SHAP analysis script and verifying that (a) SHAP values are computed for all features, (b) a feature importance ranking is produced, and (c) the report identifies the relative contribution of chemical heterogeneity descriptors versus mean coordination number.

**Acceptance Scenarios**:

1. **Given** a trained gradient boosting model is available, **When** SHAP analysis executes, **Then** SHAP values are computed for all compositional descriptors without requiring GPU acceleration
2. **Given** SHAP values are computed, **When** the importance report generates, **Then** the report ranks features by mean absolute SHAP value and includes a summary of chemical heterogeneity contribution
3. **Given** the full analysis completes, **When** the results are logged, **Then** the output includes both quantitative metrics (feature importance scores) and qualitative interpretation of heterogeneity effects

---

### Edge Cases

- What happens when the supplementary dataset is inaccessible or the URL returns an error? → The system MUST log the failure with HTTP status code and retry up to 3 times before halting with explicit error message.
- How does the system handle samples with missing elemental data (e.g., incomplete composition formulas)? → The system MUST exclude such samples from feature computation and log the count of excluded samples in the preprocessing report.
- What happens when the stratified split results in test set with <5 samples for a chemical family? → The system MUST log a warning and proceed with available data, but the final report MUST note this limitation.
- How does the system handle SHAP computation that exceeds memory limits on ~7 GB RAM? → The system MUST sample the dataset to ≤5000 samples for SHAP analysis and record this scoping decision in Assumptions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the chalcogenide dataset from the documented supplementary repository URL and validate that all required columns (composition, Tg) are present (See US-1)
- **FR-002**: System MUST compute mean coordination number, electronegativity variance, and atomic radius variance for each sample using elemental property databases (See US-1)
- **FR-003**: System MUST split data into training (≥80%) and testing (≤20%) sets with stratification by chemical family to ensure generalization testing (See US-1)
- **FR-004**: System MUST train a Gradient Boosting Regressor using scikit-learn on CPU with 5-fold cross-validation for hyperparameter tuning (See US-2)
- **FR-005**: System MUST compute and log RMSE and R² performance metrics for both gradient boosting and linear baseline models on the held-out test set (See US-2)
- **FR-006**: System MUST apply SHAP analysis to compute feature importance rankings and quantify contribution of chemical heterogeneity descriptors (See US-3)
- **FR-007**: System MUST execute all analysis within 6 hours on a free-tier CI runner (2 CPU, ~7 GB RAM, ~14 GB disk, no GPU) (See US-2)
- **FR-008**: System MUST frame all findings as ASSOCIATIONAL (not causal) since the dataset is observational with no random assignment (See US-2)

### Key Entities *(include if feature involves data)*

- **ChalcogenideSample**: Represents a single glass composition with attributes: elemental_formula, mean_coordination_number, electronegativity_variance, atomic_radius_variance, Tg_value, chemical_family
- **ModelPerformance**: Represents evaluation results with attributes: model_type, rmse, r_squared, cv_fold_scores, training_time_seconds
- **SHAPImportance**: Represents feature attribution with attributes: feature_name, mean_absolute_shap_value, shap_value_distribution

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Test set RMSE is measured against the linear baseline RMSE to quantify non-linear interaction effects (See US-2)
- **SC-002**: Test set R² is measured against the linear baseline R² to confirm gradient boosting generalization performance (See US-2)
- **SC-003**: Mean absolute SHAP value for electronegativity variance is measured against mean absolute SHAP value for mean coordination number to quantify relative heterogeneity contribution (See US-3)
- **SC-004**: Total analysis runtime is measured against the 6-hour CI time limit to verify CPU-only feasibility (See US-2)
- **SC-005**: Feature importance ranking is measured against the literature baseline (rigidity theory paper) to validate constraint theory predictions (See US-3)

### Methodological Soundness Criteria

- **SC-006**: Dataset-variable fit is measured by verifying all required predictors (mean coordination, electronegativity variance, atomic radius variance) and outcome (Tg) are present in the source dataset; if any variable is missing, a `[NEEDS CLARIFICATION: does dataset contain <variable>?]` marker is recorded (See US-1)
- **SC-007**: Multiple-comparison correction is measured by applying family-wise error rate control when testing >1 hypothesis (feature importance comparisons); the method used is recorded in the final report (See US-3)
- **SC-008**: Predictor collinearity is measured by computing variance inflation factors (VIF) for compositional descriptors; if VIF >5 for any pair, the joint relationship is framed descriptively and collinearity diagnostics are recorded (See US-3)

## Assumptions

- The supplementary dataset from the cited study (arxiv.org/abs/2211.00691v1) is accessible and contains all required variables (elemental compositions and Tg values); if the dataset lacks chemical heterogeneity measures beyond mean coordination, this gap is recorded as `[NEEDS CLARIFICATION: does dataset contain electronegativity variance and atomic radius variance?]`
- The chalcogenide dataset size is ≤1000 samples, ensuring it fits within ~7 GB RAM and ~14 GB disk on free-tier CI runners; if larger, the system will sample to ≤5000 samples for SHAP analysis and record this scoping decision
- Elemental property databases (for coordination numbers, electronegativity, atomic radii) are available via standard Python packages (e.g., mendeleev) without requiring external network calls during analysis
- The 80/20 stratified split preserves sufficient samples per chemical family; if a family has <5 samples in the test set, the limitation is documented in the final report
- All analysis uses scikit-learn's default precision (float64) without 8-bit or 4-bit quantization, as these require CUDA which is unavailable on free-tier CI
- SHAP analysis will use the `shap.TreeExplainer` for gradient boosting models, which is CPU-tractable and does not require GPU acceleration
- The 6-hour CI time limit is sufficient for 5-fold CV with hyperparameter tuning on ≤1000 samples; if runtime exceeds this, the system will reduce CV folds to 3 or reduce hyperparameter search space
