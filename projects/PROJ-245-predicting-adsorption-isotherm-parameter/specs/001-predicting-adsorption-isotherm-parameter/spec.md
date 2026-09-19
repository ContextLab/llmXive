# Feature Specification: Predicting Adsorption Isotherm Parameters from Molecular Features

**Feature Branch**: `001-predict-adsorption-isotherm-params`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Predicting Adsorption Isotherm Parameters from Molecular Features"

## User Scenarios & Testing

### User Story 1 - Curate and Prepare the Adsorption Dataset (Priority: P1)

**User Journey**: A researcher uploads raw adsorption data from the NIST Adsorption Database (via Zenodo mirror or QMOF) and the MOF-1000 Zenodo repository. The system filters for Type I isotherms (with a fallback to Type II or shape-fitting if necessary), calculates molecular descriptors (polarizability, van der Waals volume, kinetic diameter, Lennard-Jones energy parameter) using RDKit, extracts adsorbent properties (pore volume, surface area), and outputs a clean, normalized CSV ready for modeling.

**Why this priority**: Without a high-quality, consistent dataset linking descriptors to isotherm parameters, no predictive model can be trained. This is the foundational step that enables all subsequent analysis.

**Independent Test**: The pipeline can be tested by running it on a small, manually curated subset of the NIST data and verifying that the output CSV contains exactly the expected columns (e.g., `polarizability`, `langmuir_capacity`, `henry_constant`) with no missing values or unit inconsistencies.

**Acceptance Scenarios**:
1. **Given** a raw NIST dataset containing mixed isotherm types (I, II, IV), **When** the preprocessing script runs, **Then** only entries identified as Type I isotherms are retained; if fewer than 500 Type I entries are found, the system automatically includes Type II entries OR applies an automated shape-fitting heuristic (R² > 0.9 against a standard Type I model) to identify Type I entries, logging the fallback method used.
2. **Given** a molecular structure file (e.g., SDF) for an adsorbate, **When** the RDKit descriptor calculation module runs, **Then** the output includes `molecular_weight`, `polar_surface_area`, `van_der_waals_volume`, `kinetic_diameter`, and `lennard_jones_energy` with values in standard units (e.g., Å³ for volume).
3. **Given** a dataset where adsorbent properties (e.g., surface area) are listed in different units (m²/g vs cm²/g), **When** the normalization step runs, **Then** all surface area values are converted to m²/g before model training.
4. **Given** a dataset with missing pore volume data, **When** the imputation step runs, **Then** the system imputes the value using the mean of similar materials (based on surface area and functional group counts) or excludes the entry, logging the exclusion reason.

---

### User Story 1.5 - Statistical Validation of Feature Importance (Priority: P1)

**User Journey**: A domain expert validates the statistical significance of the identified feature drivers. The system performs **group permutation testing** (shuffling correlated features together) and **leave-one-adsorbent-out cross-validation** to ensure the p-values are robust against multicollinearity and material-specific biases. The system also performs a **global permutation test** by shuffling adsorbate IDs across adsorbents to break the physical pairing and generate a valid null distribution.

**Why this priority**: This step ensures the scientific validity of the feature importance claims, preventing false positives due to correlated descriptors or material-specific artifacts, and ensuring the model captures generalizable physics.

**Independent Test**: The validation module can be tested by running it on a synthetic dataset with known feature correlations and verifying that the p-values correctly reflect the true importance (or lack thereof) of the correlated features, and that the global permutation test correctly identifies the null hypothesis.

**Acceptance Scenarios**:
1. **Given** a set of correlated molecular descriptors (e.g., polarizability and van der Waals volume with correlation > 0.8), **When** the group permutation test runs, **Then** the features are permuted together as a group to preserve their correlation structure.
2. **Given** a dataset with multiple adsorbates per material, **When** the leave-one-adsorbent-out (LOCO) test runs, **Then** the model is trained on all adsorbents except one, and the performance is evaluated on the held-out adsorbent to test generalizability across materials.
3. **Given** a sparse dataset (one adsorbate per material), **When** the LOCO test runs, **Then** the system switches to leave-one-adsorbate-out cross-validation to ensure sufficient variance for testing.
4. **Given** the full dataset, **When** the global permutation test runs, **Then** the system shuffles adsorbate IDs across adsorbents (breaking the pairing) to generate a null distribution for feature importance, ensuring the test validates generalizable physics.

---

### User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

**User Journey**: A data scientist selects a target isotherm parameter (e.g., Langmuir capacity) and trains three baseline models (Linear Regression, Random Forest, Gradient Boosting) on the prepared dataset. The system performs 5-fold cross-validation, optimizes hyperparameters, and reports performance metrics (R², RMSE, MAE) on a held-out test set that ensures no material leakage.

**Why this priority**: This step validates the core hypothesis that molecular descriptors can predict thermodynamic parameters. It determines if the project proceeds to interpretation or requires a different approach.

**Independent Test**: The modeling pipeline can be tested by running it on a synthetic dataset with known linear relationships to verify the code logic (e.g., that the training loop executes, splits data, and reports metrics correctly). Note: This is a logic verification test only; scientific validation of the hypothesis MUST use real experimental data.

**Acceptance Scenarios**:
1. **Given** the prepared dataset split into training and test sets (split proportion 0.8/0.2) with material-level separation and stratification by adsorbate type, **When** the training loop completes, **Then** the system reports the R², RMSE, and MAE for the best-performing model on the independent test set.
2. **Given** a model trained on 5-fold cross-validation, **When** hyperparameter tuning is complete, **Then** the system logs the optimal parameters (e.g., `n_estimators=200`, `max_depth=10`) and the mean cross-validation R² score.
3. **Given** a trained model, **When** it is evaluated against a null model (predicting the geometric mean of the target), **Then** the trained model's RMSE is at least 20% lower than the null model's RMSE, validated by a paired t-test (p < 0.05).
4. **Given** the top 3 features identified by SHAP analysis, **When** a reduced-feature model is trained using only these features, **Then** the system reports the R² of this reduced model and compares it to the null model baseline.

---

### User Story 3 - Interpret Model Drivers via SHAP Analysis (Priority: P3)

**User Journey**: A domain expert reviews the best-performing model's feature importance. The system generates SHAP summary plots and partial dependence plots to identify which molecular descriptors (e.g., polarizability) most strongly influence the predicted isotherm parameters, validating these findings against known physicochemical principles and independent literature.

**Why this priority**: This step answers the primary research question ("Which descriptors... most strongly determine..."). It transforms the "black box" prediction into actionable scientific insight for materials design.

**Independent Test**: The interpretation module can be tested by applying it to a model trained on a dataset with a known dominant feature (e.g., `kinetic_diameter`), verifying that the SHAP analysis correctly ranks this feature as the top contributor.

**Acceptance Scenarios**:
1. **Given** the trained Random Forest model, **When** SHAP analysis is executed, **Then** the top 3 features by mean absolute SHAP value are identified and displayed in a summary plot.
2. **Given** the feature `polarizability`, **When** the partial dependence plot is generated, **Then** the plot shows a relationship that is physically plausible (e.g., consistent with known adsorption trends) and bounded by the Langmuir capacity parameter.
3. **Given** the set of identified top descriptors, **When** the results are compared to the `LiteratureConsensusList` (derived from independent experimental studies), **Then** the system generates a report discussing the alignment or divergence of the model's findings against the consensus list, explicitly noting any novel drivers discovered or established drivers that were not selected by the model.
4. **Given** the top 3 features identified by mean absolute SHAP value, **When** a reduced-feature model is trained using only these features, **Then** the system reports the R² of this reduced model and compares it to a null model baseline (predicting the geometric mean of the target).

---

### Edge Cases

- **What happens when** the dataset contains adsorbates with identical molecular descriptors but different isotherm parameters? The system must flag these as potential outliers or measurement errors rather than forcing a fit.
- **How does the system handle** adsorbents with missing pore volume data in the metadata? The system must either impute the value using a defined method (e.g., mean of similar materials) or exclude the entry, logging the exclusion reason.
- **What happens when** the test set performance is poor (R² < 0.5)? The system must output a diagnostic report suggesting potential causes (e.g., "Non-linear effects not captured by descriptors", "Data leakage", "Feature collinearity") rather than silently failing.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST calculate a configurable set of molecular descriptors (including but not limited to molecular weight, polar surface area, polarizability, H-bond donors/acceptors, van der Waals volume, **kinetic diameter**, and **Lennard-Jones energy parameter**) for all adsorbates using RDKit. (See US-1)
- **FR-002**: The system MUST filter the raw dataset to include only Type I isotherms (identified by `isotherm_type` column equals "Type I" or "I", case-insensitive, or `isotherm_class` column matching "I"). If the filtered dataset contains fewer than 500 entries, the system MUST automatically relax the filter to include Type II isotherms OR apply an automated shape-fitting heuristic (R² > 0.9 against a standard Type I model) to identify Type I entries, logging the fallback method used. If the 'isotherm_type' column is missing, the system MUST apply the shape-fitting heuristic or relax to Type II to ensure the dataset is non-empty. (See US-1)
- **FR-003**: The system MUST split the dataset into training and test sets such that no single adsorbent material appears in both sets to prevent data leakage. The split MUST be stratified by adsorbate type to ensure representative distribution. If the dataset is sparse (one adsorbate per material), the system MUST switch to leave-one-adsorbate-out cross-validation. (See US-2)
- **FR-004**: The system MUST train at least three distinct regression models (Linear Regression, Random Forest, Gradient Boosting) and select the best performer based on cross-validated R². (See US-2)
- **FR-005**: The system MUST generate SHAP summary plots and partial dependence plots for the top-ranked features of the best-performing model. The SHAP analysis MUST use a representative background dataset and include permutation importance with confidence intervals as a validation step. (See US-3)
- **FR-006**: The system MUST perform **group permutation testing** for feature importance, where features with a correlation coefficient > 0.8 are permuted together as a group. The system MUST use **leave-one-adsorbent-out (LOCO)** cross-validation (where `adsorbent_id` defines the cluster) to test generalizability across materials. The system MUST run **1000 permutations** and apply a **False Discovery Rate (FDR) correction (alpha=0.05)** to the resulting p-values. The system MUST also perform a **global permutation test** by shuffling adsorbate IDs across adsorbents (breaking the physical pairing) to generate a valid null distribution for feature importance. (See US-1.5, US-2, US-3)
- **FR-007**: The system MUST generate a final report that compares the identified top descriptors against the `LiteratureConsensusList` (loaded from `data/config/consensus_list.json`, sourced from independent experimental studies or distinct theoretical frameworks) and explicitly discusses the alignment or divergence of findings, rather than requiring a strict match. The report MUST highlight any novel descriptors identified by the model that are not on the consensus list, and any consensus descriptors that the model failed to identify as significant. **Note**: This comparison is for **qualitative discussion and hypothesis generation** only, not for pass/fail validation. The `LiteratureConsensusList` MUST be sourced from independent experimental studies, not from the same dataset or theoretical assumptions as the descriptors. (See US-3)
- **FR-008**: The system MUST generate and persist a runtime log artifact at `data/benchmarks/runtime_log.json` containing the start time, end time, total duration, and status of the full pipeline execution. (See US-2)
- **FR-009**: The system MUST flag adsorbates with identical molecular descriptors but different isotherm parameters as potential outliers and log them to `data/validation/outlier_log.json`. (See US-1, Edge Cases)
- **FR-010**: The system MUST impute missing pore volume data using the mean of similar materials (based on surface area and functional group counts) or exclude the entry, logging the exclusion reason to `data/validation/exclusion_log.json`. (See US-1, Edge Cases)
- **FR-011**: The system MUST generate a diagnostic report when test set performance is poor (R² < 0.5), including a checklist of at least 5 potential causes (e.g., "Non-linear effects", "Data leakage", "Feature collinearity", "Insufficient data", "Model mismatch") with a pass/fail status for each. (See US-2, Edge Cases)
- **FR-012**: The system MUST train a reduced-feature model using only the top 3 descriptors (selected by mean absolute SHAP value from the best-performing model in FR-004) and compare its R² to the null model baseline. (See US-2, SC-003)

### Key Entities

- **Adsorbate**: Represents the gas molecule being adsorbed; key attributes include molecular structure, polarizability, kinetic diameter, and van der Waals volume.
- **Adsorbent**: Represents the porous material; key attributes include surface area, pore volume, functional group counts, and crystal structure metadata. The `adsorbent_id` is the unique identifier for this entity.
- **IsothermParameter**: Represents the target thermodynamic values; attributes include Henry's constant (K_H), Langmuir capacity (Q_max), and Freundlich exponent (n).
- **ModelPerformance**: Represents the evaluation metrics; attributes include R², RMSE, MAE, and cross-validation scores.
- **LiteratureConsensusList**: A configurable list of known dominant drivers (e.g., polarizability, kinetic diameter, Lennard-Jones energy parameter, quadrupole moment, molecular volume) used for comparative analysis and discussion. **This list MUST be sourced from independent experimental studies or distinct theoretical frameworks, not from the same dataset or theoretical assumptions as the descriptors.** (See FR-007)

## Success Criteria

### Measurable Outcomes

- **SC-001**: The R-squared value of the best-performing model on the independent test set is measured against a null model baseline (predicting the geometric mean of the target); the observed value and 95% confidence interval are reported (threshold ≥ 0.2 improvement over null). The improvement MUST be validated by a **paired t-test on 5-fold CV scores (p < 0.05)**. (See US-2)
- **SC-002**: The feature importance ranking derived from SHAP analysis is compared against the `LiteratureConsensusList` (sourced from independent experimental studies); the report MUST discuss the alignment or divergence of findings, explicitly identifying at least one point of convergence or divergence. **Alignment is defined as overlap of the top 3 SHAP features with the top 3 entries in the LiteratureConsensusList.** (See US-3)
- **SC-003**: The R² of a model trained *only* on the top 3 molecular descriptors (selected by mean absolute SHAP value from the best-performing model in SC-001) is measured against a null model baseline (predicting the geometric mean); the observed value and 95% confidence interval are reported (threshold ≥ 0.2 improvement over null). (See US-2, FR-012)
- **SC-004**: The computational runtime of the full pipeline (data curation to SHAP analysis) is measured against a fixed duration of ≤ 4 hours on a **GitHub Actions 2-core runner, 7GB RAM, Ubuntu 22.04**. (See US-2)
- **SC-005**: The output report MUST include the adjusted p-values or q-values for the top-ranked features, confirming the multiple-comparison correction was applied. (See US-3)
- **SC-006**: The system MUST flag potential outliers (adsorbates with identical descriptors but different parameters) and log them to `data/validation/outlier_log.json`. (See US-1, FR-009)
- **SC-007**: The system MUST persist imputed data or exclusion logs for missing pore volume data to `data/validation/exclusion_log.json`. (See US-1, FR-010)
- **SC-008**: The system MUST generate a diagnostic report with a checklist of potential causes when test set performance is poor (R² < 0.5). (See US-2, FR-011)

## Assumptions

- The NIST Adsorption Database (via Zenodo mirror or QMOF) and MOF-1000 Zenodo repository contain sufficient entries (N > 500) with complete metadata (surface area, pore volume) to train a robust machine learning model without severe overfitting. If the initial Type I filter yields < 500 entries, the fallback to Type II isotherms or shape-fitting heuristic is assumed to provide sufficient data.
- The molecular descriptors calculable via RDKit (polarizability, van der Waals volume, kinetic diameter, Lennard-Jones energy) are sufficient proxies for the complex electronic interactions governing adsorption, or that their correlation with experimental parameters is strong enough for screening purposes.
- The GitHub Actions free-tier runner (multi-core CPU, sufficient RAM) is sufficient to process the dataset and train Random Forest/Gradient Boosting models on the sampled data without exceeding memory limits or the designated time budget (≤ 4 hours).
- The "Type I" isotherm classification in the source data is consistent and reliable; if the column is missing, the fallback to shape-fitting or Type II is assumed to be valid.
- The relationship between molecular descriptors and isotherm parameters is sufficiently captured by the selected regression models (Linear, RF, GB) without requiring deep learning architectures or GPU acceleration.
- The dataset contains distinct adsorbent structure IDs (`adsorbent_id`) that can be used as the clustering key for permutation testing (LOCO).
- The `LiteratureConsensusList` is sourced from an independent, external dataset or study to avoid circular validation.