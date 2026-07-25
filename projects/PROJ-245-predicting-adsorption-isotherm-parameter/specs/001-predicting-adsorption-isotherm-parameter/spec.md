# Feature Specification: Predicting Adsorption Isotherm Parameters from Molecular Features

**Feature Branch**: `001-predict-adsorption-isotherm-params`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Predicting Adsorption Isotherm Parameters from Molecular Features"

## User Scenarios & Testing

### User Story 1 - Curate and Prepare the Adsorption Dataset (Priority: P1)

**User Journey**: A researcher uploads raw adsorption data from the NIST Adsorption Database and the MOF-1000 Zenodo repository. The system filters for Type I isotherms, calculates molecular descriptors (polarizability, van der Waals volume) using RDKit, extracts adsorbent properties (pore volume, surface area), and outputs a clean, normalized CSV ready for modeling.

**Why this priority**: Without a high-quality, consistent dataset linking descriptors to isotherm parameters, no predictive model can be trained. This is the foundational step that enables all subsequent analysis.

**Independent Test**: The pipeline can be tested by running it on a small, manually curated subset of the NIST data and verifying that the output CSV contains exactly the expected columns (e.g., `polarizability`, `langmuir_capacity`, `henry_constant`) with no missing values or unit inconsistencies.

**Acceptance Scenarios**:
1. **Given** a raw NIST dataset containing mixed isotherm types (I, II, IV), **When** the preprocessing script runs, **Then** only entries identified as Type I isotherms are retained, and entries with missing Henry's constants or Langmuir capacities are excluded.
2. **Given** a molecular structure file (e.g., SDF) for an adsorbate, **When** the RDKit descriptor calculation module runs, **Then** the output includes `molecular_weight`, `polar_surface_area`, and `van_der_waals_volume` with values in standard units (e.g., Å³ for volume).
3. **Given** a dataset where adsorbent properties (e.g., surface area) are listed in different units (m²/g vs cm²/g), **When** the normalization step runs, **Then** all surface area values are converted to m²/g before model training.

---

### User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

**User Journey**: A data scientist selects a target isotherm parameter (e.g., Langmuir capacity) and trains three baseline models (Linear Regression, Random Forest, Gradient Boosting) on the prepared dataset. The system performs 5-fold cross-validation, optimizes hyperparameters, and reports performance metrics (R², RMSE, MAE) on a held-out test set that ensures no material leakage.

**Why this priority**: This step validates the core hypothesis that molecular descriptors can predict thermodynamic parameters. It determines if the project proceeds to interpretation or requires a different approach.

**Independent Test**: The modeling pipeline can be tested by running it on a synthetic dataset with known linear relationships to verify the code logic (e.g., that the training loop executes, splits data, and reports metrics correctly). Note: This is a logic verification test only; scientific validation of the hypothesis MUST use real experimental data.

**Acceptance Scenarios**:
1. **Given** the prepared dataset split into training and test sets (split proportion 0.8/0.2) with material-level separation, **When** the training loop completes, **Then** the system reports the R², RMSE, and MAE for the best-performing model on the independent test set.
2. **Given** a model trained on 5-fold cross-validation, **When** hyperparameter tuning is complete, **Then** the system logs the optimal parameters (e.g., `n_estimators=200`, `max_depth=10`) and the mean cross-validation R² score.
3. **Given** a trained model, **When** it is evaluated against a null model (predicting the mean), **Then** the trained model's RMSE is at least 20% lower than the null model's RMSE.

---

### User Story 3 - Interpret Model Drivers via SHAP Analysis (Priority: P3)

**User Journey**: A domain expert reviews the best-performing model's feature importance. The system generates SHAP summary plots and partial dependence plots to identify which molecular descriptors (e.g., polarizability) most strongly influence the predicted isotherm parameters, validating these findings against known physicochemical principles.

**Why this priority**: This step answers the primary research question ("Which descriptors... most strongly determine..."). It transforms the "black box" prediction into actionable scientific insight for materials design.

**Independent Test**: The interpretation module can be tested by applying it to a model trained on a dataset with a known dominant feature (e.g., `kinetic_diameter`), verifying that the SHAP analysis correctly ranks this feature as the top contributor.

**Acceptance Scenarios**:
1. **Given** the trained Random Forest model, **When** SHAP analysis is executed, **Then** the top 3 features by mean absolute SHAP value are identified and displayed in a summary plot.
2. **Given** the feature `polarizability`, **When** the partial dependence plot is generated, **Then** the plot shows a relationship that is monotonically non-decreasing with respect to adsorbate density and bounded by the Langmuir capacity parameter.
3. **Given** the set of identified top descriptors, **When** the results are compared to the `LiteratureConsensusList` (defined in Key Entities), **Then** the system generates a report discussing the alignment or divergence of the model's findings against the consensus list, explicitly noting any novel drivers discovered or established drivers that were not selected by the model.

---

### Edge Cases

- **What happens when** the dataset contains adsorbates with identical molecular descriptors but different isotherm parameters? The system must flag these as potential outliers or measurement errors rather than forcing a fit.
- **How does the system handle** adsorbents with missing pore volume data in the metadata? The system must either impute the value using a defined method (e.g., mean of similar materials) or exclude the entry, logging the exclusion reason.
- **What happens when** the test set performance is poor (R² < 0.5)? The system must output a diagnostic report suggesting potential causes (e.g., "Non-linear effects not captured by descriptors") rather than silently failing.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST calculate a configurable set of molecular descriptors (including but not limited to molecular weight, polar surface area, polarizability, H-bond donors/acceptors, van der Waals volume) for all adsorbates using RDKit. (See US-1)
- **FR-002**: The system MUST filter the raw dataset to include only Type I isotherms and remove entries with missing target parameters (Henry's constant, Langmuir capacity). (See US-1)
- **FR-003**: The system MUST split the dataset into training and test sets such that no single adsorbent material appears in both sets to prevent data leakage. (See US-2)
- **FR-004**: The system MUST train at least three distinct regression models (Linear Regression, Random Forest, Gradient Boosting) and select the best performer based on cross-validated R². (See US-2)
- **FR-005**: The system MUST generate SHAP summary plots and partial dependence plots for the top-ranked features of the best-performing model. (See US-3)
- **FR-006**: The system MUST generate permutation-based p-values for the top feature importances and apply a False Discovery Rate (FDR) correction (Benjamini-Hochberg) to these p-values. (Justification: Essential to prevent false-positive feature selection in high-dimensional descriptor space.) (See US-2, US-3)
- **FR-007**: The system MUST implement cluster-aware permutation testing for feature importance, where feature values are shuffled *within* material clusters (defined as all entries sharing the same adsorbent structure ID) to handle multicollinearity, and MUST report the adjusted p-values. (See US-2, US-3)
- **FR-008**: The system MUST generate a final report that compares the identified top descriptors against the `LiteratureConsensusList` and explicitly discusses the alignment or divergence of findings, rather than requiring a strict match. The report MUST highlight any novel descriptors identified by the model that are not on the consensus list, and any consensus descriptors that the model failed to identify as significant. (See US-3)
- **FR-009**: The system MUST generate and persist a runtime log artifact at `data/benchmarks/runtime_log.json` containing the start time, end time, total duration, and status of the full pipeline execution. (See US-2)

### Key Entities

- **Adsorbate**: Represents the gas molecule being adsorbed; key attributes include molecular structure, polarizability, kinetic diameter, and van der Waals volume.
- **Adsorbent**: Represents the porous material; key attributes include surface area, pore volume, functional group counts, and crystal structure metadata.
- **IsothermParameter**: Represents the target thermodynamic values; attributes include Henry's constant (K_H), Langmuir capacity (Q_max), and Freundlich exponent (n).
- **ModelPerformance**: Represents the evaluation metrics; attributes include R², RMSE, MAE, and cross-validation scores.
- **LiteratureConsensusList**: A configurable list of known dominant drivers (e.g., polarizability, kinetic diameter, Lennard-Jones energy parameter, quadrupole moment, molecular volume) used for comparative analysis and discussion, NOT for validation or strict matching.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The R-squared value of the best-performing model on the independent test set is measured against a null model baseline; the observed value and 95% confidence interval are reported (threshold ≥ 0.2 improvement over null). (See US-2)
- **SC-002**: The feature importance ranking derived from SHAP analysis is compared against the `LiteratureConsensusList`; the report MUST discuss the alignment or divergence of findings, explicitly identifying at least one point of convergence or divergence. (See US-3)
- **SC-003**: The R² of a model trained *only* on the top 3 molecular descriptors is measured against a null model baseline; the observed value and 95% confidence interval are reported (threshold ≥ 0.2 improvement over null). (See US-3)
- **SC-004**: The computational runtime of the full pipeline (data curation to SHAP analysis) is measured against a fixed duration of ≤ 4 hours. (See US-2)
- **SC-005**: The output report MUST include the adjusted p-values or q-values for the top-ranked features, confirming the multiple-comparison correction was applied. (See US-3)

## Assumptions

- The NIST Adsorption Database and MOF-1000 Zenodo dataset contain sufficient entries (N > 500) with complete metadata (surface area, pore volume) to train a robust machine learning model without severe overfitting.
- The molecular descriptors calculable via RDKit (polarizability, van der Waals volume) are sufficient proxies for the complex electronic interactions governing adsorption, or that their correlation with experimental parameters is strong enough for screening purposes.
- The GitHub Actions free-tier runner (multi-core CPU, sufficient RAM) is sufficient to process the dataset and train Random Forest/Gradient Boosting models on the sampled data without exceeding memory limits or the designated time budget (≤ 4 hours).
- The "Type I" isotherm classification in the source data is consistent and reliable; no manual re-classification of isotherm shapes is required.
- The relationship between molecular descriptors and isotherm parameters is sufficiently captured by the selected regression models (Linear, RF, GB) without requiring deep learning architectures or GPU acceleration.
- The dataset contains distinct adsorbent structure IDs that can be used as the clustering key for permutation testing.