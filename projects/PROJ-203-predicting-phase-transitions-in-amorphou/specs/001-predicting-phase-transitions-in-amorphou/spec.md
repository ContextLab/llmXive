# Feature Specification: Predicting Phase Transitions in Amorphous Solids Using Machine Learning

**Feature Branch**: `001-predicting-phase-transitions`  
**Created**: 2026-07-15  
**Status**: Draft  
**Input**: User description: "Predicting Phase Transitions in Amorphous Solids Using Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Pipeline Execution & Descriptor Generation (Priority: P1)

The researcher MUST be able to execute the full data generation pipeline to produce a structured dataset of short-range structural descriptors (RDF, bond angles, coordination numbers) and compositional features for a curated list of amorphous compositions, with experimental glass-transition temperatures (Tg) and crystallization labels attached.

**Why this priority**: This is the foundational step; without a valid, independent dataset linking simulation-derived structural features to experimental thermal properties, no modeling or analysis can occur. It addresses the core "Dataset-variable fit" and "Independence" requirements.

**Independent Test**: The pipeline can be run end-to-end on a CPU-only environment, producing a single CSV/Parquet file where every row contains composition, structural descriptors, and experimental Tg/crystallization labels, with no missing values for the required predictors.

**Acceptance Scenarios**:

1. **Given** a list of 500 compositions across oxides, sulfides, and organics, **When** the pipeline executes the MD simulation and feature extraction steps, **Then** the output dataset contains a sufficient number of rows with valid values for RDF peaks, bond-angle variance, and experimental Tg.
2. **Given** a composition where the MD simulation exceeds the 30-minute CPU cap, **When** the pipeline triggers the truncation logic, **Then** the simulation is cut to the final steps, and the resulting descriptors are flagged as "truncated" in the output metadata without halting the job.
3. **Given** a composition lacking an experimental Tg in the source databases, **When** the data curation step runs, **Then** the row is excluded from the final training set, and a log entry records the specific composition ID and missing source.

---

### User Story 2 - Model Training & Performance Validation (Priority: P2)

The researcher MUST be able to train Random Forest regression and classification models on the generated dataset to predict Tg and crystallization propensity, achieving a Root-Mean-Square Error (RMSE) of ≤15 K on the held-out test set for Tg, while ensuring the models are trained using only CPU resources within the 6-hour job limit.

**Why this priority**: This validates the core hypothesis that local structural order contains sufficient signal for accurate prediction. It directly addresses the "Compute feasibility" constraint (CPU-only, no GPU) and the expected result of RMSE ≤15 K. The 15 K target is justified as the experimental noise floor (±5-10 K) plus a safety margin, and the model must outperform a composition-only baseline.

**Independent Test**: The training script can be executed on a standard GitHub Actions runner (2 CPU, 7GB RAM) and completes within 6 hours, outputting a model file and a performance report showing RMSE ≤15 K and ROC-AUC > 0.7 for the classification task.

**Acceptance Scenarios**:

1. **Given** the training dataset split into a majority training set and a held-out test set, stratified by chemical family, **When** the Random Forest regressor is trained with a sufficient ensemble of trees, **Then** the model achieves an RMSE of ≤15 K on the test set without requiring GPU acceleration or 8-bit quantization.
2. **Given** the 6-hour compute budget, **When** the hyperparameter grid search is executed, **Then** the search completes within 2 hours, leaving 4 hours for cross-validation and reporting, ensuring the job does not timeout.
3. **Given** the classification task for crystallization propensity, **When** the model is evaluated, **Then** the ROC-AUC score is reported, and the confusion matrix is saved to verify the "low stability" (T_x within 50 K of Tg) labeling logic.

---

### User Story 3 - Interpretability & Cross-Family Analysis (Priority: P3)

The researcher MUST be able to generate SHAP (SHapley Additive exPlanations) values to rank the contribution of structural descriptors and visualize how feature importance differs across oxide, sulfide, and organic families, identifying a core set of universal predictors.

**Why this priority**: This addresses the "Literature gap" of moving beyond black-box prediction to interpretable science. It allows the researcher to answer "which features determine the property" and identify family-specific vs. universal drivers.

**Independent Test**: The analysis script generates SHAP summary plots and partial dependence plots that clearly distinguish the top 3–5 predictors for each chemical family, with the output saved as static images or interactive HTML files.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model, **When** SHAP values are computed, **Then** the output includes a ranked list of the top features for each chemical family, showing systematic variation (e.g., RDF width vs. bond-angle skewness).
2. **Given** the top-ranked descriptor (e.g., first-peak RDF width), **When** a partial dependence plot is generated, **Then** the plot shows a monotonic or distinct non-linear relationship with Tg, confirming the physical driver.
3. **Given** the comparison across families, **When** the results are aggregated, **Then** the report explicitly identifies at least one descriptor that is a universal predictor across all three families and at least one that is family-specific.

### Edge Cases

- **What happens when** the experimental Tg data is missing for a specific composition in the "Glass Data" dataset?
  - The pipeline must exclude the composition and log the event, ensuring no imputation is performed that could bias the structural-thermal relationship.
- **How does the system handle** a composition where the pre-trained interatomic potential (e.g., SNAP/GAP) fails to converge or produces NaN values during the MD trajectory?
  - The simulation step must catch the error, discard the trajectory, and mark the composition as "failed simulation" in the metadata, preventing the model from training on corrupted data.
- **What happens when** the dataset size is insufficient to achieve the target RMSE of ≤15 K after 5-fold cross-validation?
  - The analysis must report the achieved RMSE and explicitly note the power limitation, rather than artificially inflating performance or ignoring the metric.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate short-range structural descriptors (RDF peak position/width, bond-angle variance, coordination numbers) from MD trajectories for at least 500 valid compositions across oxide, sulfide, and organic families. A composition is "valid" only if the MD simulation converges without NaNs and produces descriptors within physically realistic bounds (See US-1).
- **FR-002**: System MUST label crystallization propensity as binary (1 if experimental T_x is within 50 K of Tg, 0 otherwise) using independent experimental thermal analysis data (See US-1).
- **FR-003**: System MUST train a Random Forest regression model on the generated dataset using only CPU resources, completing the training and k-fold cross-validation within a 6-hour wall-clock time limit (See US-2).
- **FR-004**: System MUST compute SHAP values to rank feature importance and generate partial dependence plots for the top predictors, stratified by chemical family (See US-3).
- **FR-005**: System MUST enforce a multiple-comparison correction (e.g., Bonferroni or False Discovery Rate) when evaluating the statistical significance of feature importance differences across families to control family-wise error (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis on the crystallization threshold using a range of specific cutoff values. The analysis must report how classification accuracy, false-positive rate, and class balance vary across these cutoffs to distinguish model instability from threshold arbitrariness (See US-2).
- **FR-007**: System MUST verify that no predictor variable is definitionally derived from the target variable (e.g., ensuring structural descriptors do not implicitly encode Tg) and report collinearity diagnostics (VIF) for correlated predictors (See US-1).
- **FR-008**: System MUST implement a timescale matching protocol to align the MD simulation cooling rate with the experimental DSC cooling rate (~10 K/min) to ensure structural descriptors reflect the experimental thermal history, preventing circular validation (See US-1).

### Key Entities

- **Composition**: Represents a specific chemical formula (e.g., SiO2, Li2S-P2S5) with attributes: element fractions, average atomic radius, electronegativity variance.
- **StructuralDescriptor**: Represents a quantitative metric derived from MD (e.g., RDF_peak_width, bond_angle_variance) with attributes: value, uncertainty, element_pair, chemical_family.
- **ThermalProperty**: Represents the experimental ground truth with attributes: Tg (K), T_x (K), crystallization_label (0/1), source_database.
- **ModelPerformance**: Represents the outcome of training with attributes: RMSE, ROC_AUC, feature_importance_ranking, cross_validation_fold_scores.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Root-Mean-Square Error (RMSE) of the Tg prediction model is measured against the experimental Tg values in the held-out test set (See US-2).
- **SC-002**: The Area Under the Receiver Operating Characteristic Curve (ROC-AUC) for the crystallization propensity classifier is measured against the binary labels derived from experimental T_x and Tg (See US-2).
- **SC-003**: The stability of the top 3 structural descriptors across the three chemical families is measured by comparing their SHAP importance rankings and confidence intervals (See US-3).
- **SC-004**: The sensitivity of the crystallization classification to the threshold definition is measured by the variation in False Positive Rate and class balance across a set of cutoffs. (See US-2).
- **SC-005**: The computational feasibility is measured by the total wall-clock time of the end-to-end pipeline (simulation + training) against a limit of ≤ 6 hours on a 2-CPU runner (See US-2).

## Assumptions

- **Assumption about data availability**: The "Glass Data" dataset (Zenodo) and NIST Chemistry WebBook contain sufficient experimental Tg and T_x values for at least 500 distinct compositions total (approx. 167 per family) in the oxide, sulfide, and organic categories.
- **Assumption about simulation feasibility**: Pre-trained interatomic potentials (SNAP/GAP) from OpenKIM are available and accurate enough for the specific element sets in the target compositions, and the nanoscale cubic cell size (~500 atoms) is sufficient to capture the relevant short-range order without requiring larger supercells.
- **Assumption about compute constraints**: The Random Forest training and SHAP calculation for a representative sample set and a moderate number of features will complete within the 6-hour limit on a 2-CPU, 7GB RAM runner without requiring GPU acceleration or model quantization.
- **Assumption about threshold justification**: The 50 K cutoff for "low stability" (crystallization propensity = 1) is based on a community-standard approximation for the "fragility" of glass formers in thermal analysis, and the sensitivity analysis will confirm robustness within ±25 K.
- **Assumption about independence**: The experimental Tg and T_x values are measured via Differential Scanning Calorimetry (DSC). The MD simulation cooling rate (targeting a rate comparable to the experimental protocol via scaling) will be matched to the experimental rate to ensure the structural descriptors reflect the same thermal history, eliminating circular validation risks.
- **Assumption about collinearity**: While compositional features (e.g., average atomic radius) and structural descriptors (e.g., coordination number) may be correlated, they are not definitionally identical, allowing for the joint modeling of their effects provided collinearity diagnostics (VIF) are reported.