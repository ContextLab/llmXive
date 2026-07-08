# Feature Specification: Predicting Molecular Properties from Open Babel Fingerprints with Random Forests

**Feature Branch**: `001-predicting-molecular-properties`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Properties from Open Babel Fingerprints with Random Forests"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Error Quantification (Priority: P1)

As a computational chemist, I need to generate a baseline prediction for logP, solubility, and boiling point using a standard additive fragment model (Crippen's method) for a diverse set of molecules (diversity measured by Tanimoto similarity < 0.7) so that I can establish the "additive" ground truth against which non-linear deviations are measured.

**Why this priority**: This is the foundational step. Without a quantified baseline error, the subsequent comparison to the Random Forest model is meaningless. It directly addresses the "What is known" gap regarding the magnitude of error in standard additive models, validated against known literature limitations of fragment methods.

**Independent Test**: Can be fully tested by running the Crippen's additive fragment algorithm on the provided dataset and outputting a CSV of predicted vs. experimental values with a calculated Mean Absolute Error (MAE).

**Acceptance Scenarios**:

1. **Given** a dataset of ≥ 5,000 molecules with SMILES and experimental values, **When** the additive fragment algorithm (Crippen's atomic contributions) is executed, **Then** a CSV file is generated containing predicted values and the overall MAE for each property is logged.
2. **Given** the generated baseline predictions, **When** the residuals (Experimental - Predicted) are calculated, **Then** the distribution of residuals is plotted to identify the magnitude of the "additive failure" before any machine learning is applied.

---

### User Story 2 - Non-Linear Model Training and Validation (Priority: P2)

As a data scientist, I need to train Random Forest regressors using Open Babel fingerprints (MACCS, ECFP4, FP2) on the same dataset and evaluate their performance via k-fold cross-validation so that I can quantify the improvement in predictive accuracy over the additive baseline.

**Why this priority**: This implements the core hypothesis that non-linear models capture interactions that additive models miss. It provides the "interaction zones" map by virtue of the model's superior fit.

**Independent Test**: Can be fully tested by training the Random Forest model, performing the 3-fold cross-validation, and reporting the RMSE and MAE, comparing them numerically to the P1 baseline metrics.

**Acceptance Scenarios**:

1. **Given** the fingerprint data and experimental targets, **When** the Random Forest model is trained with hyperparameter tuning via 3-fold cross-validation, **Then** the system outputs the cross-validation scores and the final test set MAE/RMSE for logP, solubility, and boiling point.
2. **Given** the test set predictions from both the additive baseline (P1) and the Random Forest model, **When** a paired statistical test (Wilcoxon signed-rank) is performed on the absolute errors, **Then** a p-value is reported indicating whether the Random Forest improvement is statistically significant (p < 0.05).

---

### User Story 3 - Interaction Zone Mapping (Priority: P3)

As a medicinal chemist, I need to identify specific fingerprint bit pairs (substructure contexts) that contribute most to the reduction in error using SHAP values, and validate these mappings against known chemical rules (e.g., steric hindrance tables), so that I can visualize the specific molecular contexts (e.g., steric hindrance) where standard additivity fails.

**Why this priority**: This addresses the "Why this gap matters" and "What is NOT known" sections by moving from "the model is better" to "here is *why* it is better," providing the mechanistic explanation required for the research question.

**Independent Test**: Can be fully tested by generating SHAP summary plots, interaction strength heatmaps, and mapping the top interacting fingerprint bits back to chemical substructures using RDKit, then cross-referencing with a chemical rules database.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model, **When** SHAP interaction values are computed, **Then** a heatmap is generated showing the top fingerprint bit pairs with the highest interaction strength.
2. **Given** the top interacting fingerprint bits, **When** these bits are mapped back to chemical substructures using RDKit and validated against known chemical rules, **Then** a list of specific molecular contexts (e.g., "adjacent polar and hydrophobic moieties") is outputted with example molecules illustrating these contexts.

### Edge Cases

- **Given** a molecule with a complex 3D conformation that is not captured by 2D fingerprints (e.g., specific steric clashes), **When** the model predicts the property, **Then** the residual error is flagged as a "potential 3D conformational failure" rather than a standard additive failure.
- **Given** a dataset subset where experimental values are missing or outliers exist (e.g., solubility > 1000 g/L), **When** the preprocessing step runs, **Then** these entries are excluded from the training set and logged in a "data_quality_report.csv" to prevent model skew.
- **Given** a Random Forest tree depth that exceeds the -hour CI time limit, **When** the training process is monitored, **Then** the process MUST automatically reduce dataset size or reduce fingerprint complexity (per FR-009) to ensure feasibility, rather than just adjusting depth.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess a diverse dataset of ≥ 5,000 molecules (diversity measured by Tanimoto similarity < 0.7) with SMILES and experimental logP, solubility, and boiling point values from PubChem/ChEMBL, filtering for high-confidence measurements and standardizing conditions (See US-1).
- **FR-002**: System MUST compute baseline predictions using Crippen's atomic contributions method for all properties in the dataset (See US-1).
- **FR-003**: System MUST generate Open Babel fingerprints (MACCS, ECFP4, FP2) for all molecules using the `obabel` command-line tool (See US-2).
- **FR-004**: System MUST train Random Forest regressors with hyperparameter tuning via 3-fold cross-validation on a CPU-only environment, ensuring total runtime ≤ 6 hours (See US-2).
- **FR-005**: System MUST perform a paired statistical test (Wilcoxon signed-rank) comparing the absolute errors of the additive baseline versus the Random Forest model to quantify significance (See US-2).
- **FR-006**: System MUST calculate SHAP interaction values to identify specific fingerprint bit pairs contributing most to error reduction (See US-3).
- **FR-007**: System MUST map high-interaction fingerprint bits back to chemical substructures using RDKit and output a list of "deviation contexts" (See US-3).
- **FR-008**: System MUST report dataset-variable fit, explicitly flagging any required variables (e.g., specific solvent conditions) that are not present in the source dataset in a `data_quality_report.csv` with a `missing_covariate` column (See Assumptions).
- **FR-009**: System MUST implement a priority-based fingerprint generation strategy (ECFP4 > MACCS > FP2) and, if the 6-hour runtime limit is breached, automatically reduce dataset size or skip lower-priority fingerprints to ensure completion (See US-2, Edge Cases).
- **FR-010**: System MUST validate SHAP interaction mappings against a database of known chemical rules (e.g., steric hindrance, electronic resonance) to distinguish physical phenomena from statistical artifacts (See US-3).

### Key Entities

- **Molecule**: Represents a chemical entity defined by its SMILES string, ID, and associated experimental property values (logP, solubility, boiling point).
- **Fingerprint**: A binary vector representation of a molecule derived from Open Babel (MACCS, ECFP4, FP2) used as input features for the model.
- **Prediction**: A record containing the predicted value from a specific model (Additive or RF) and the associated residual error.
- **InteractionContext**: A derived entity representing a specific pair of fingerprint bits (substructures) identified as having high interaction strength in the RF model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in Mean Absolute Error (MAE) for the Random Forest model compared to the additive baseline is measured against the baseline MAE to quantify non-linear capture (See FR-005, US-2).
- **SC-002**: The statistical significance of the error reduction is measured against a p-value threshold of 0.05 using a Wilcoxon signed-rank test (See FR-005, US-2).
- **SC-003**: The interpretability of the model is measured by the count of distinct molecular contexts (substructure pairs) identified via SHAP that explain ≥ [deferred] of the non-linear variance (defined as the variance of residuals: Experimental - Additive_Prediction) (See FR-007, US-3).
- **SC-004**: The computational feasibility is measured against a bounded runtime limit on a multi-core, limited-RAM runner, ensuring the entire pipeline completes without GPU acceleration (See FR-004, Assumptions).
- **SC-005**: The methodological validity is measured by the presence of a stability analysis for the interaction strength cutoff, sweeping the cutoff over a range of low values and reporting the Jaccard similarity of the identified interaction sets across these thresholds (See FR-006, Assumptions).

## Assumptions

- **Assumption about dataset-variable fit**: The project assumes the downloaded PubChem/ChEMBL dataset contains the necessary experimental values for logP, solubility, and boiling point. If the dataset lacks specific covariates (e.g., temperature, pH), the analysis will be framed as correlational for those specific conditions, and a `[deferred]` marker will be inserted if the gap is critical to the specific property being modeled.
- **Assumption about inference framing**: Since the study is observational (no random assignment of molecular structures), all findings regarding "causes" of under-prediction will be explicitly framed as **associational** correlations between substructure contexts and model error, not causal mechanisms.
- **Assumption about computational constraints**: The analysis assumes that sampling the dataset to ≤ 5,000 molecules and limiting Random Forest `max_depth` to 10 is sufficient to fit within the GB RAM and 6-hour CPU limit without requiring GPU acceleration or quantization.
- **Assumption about measurement validity**: The project assumes that the experimental values in the source databases (PubChem/ChEMBL) are validated and citable, serving as the ground truth for the regression tasks.
- **Assumption about threshold justification**: Any threshold used to define a "significant" interaction (e.g., SHAP value > 0.05) will be justified by community standards for feature importance and will be accompanied by a stability analysis sweeping the threshold over {0.01, 0.05, 0.1} to report how the identified "interaction zones" vary.
- **Assumption about predictor collinearity**: The project assumes that while fingerprint bits are highly correlated, the Random Forest model's ability to handle collinearity is sufficient for descriptive mapping; however, the Success Criteria will require a collinearity diagnostic (e.g., VIF check on aggregated features) to ensure independent predictive effects are not falsely claimed for definitionally related substructures.