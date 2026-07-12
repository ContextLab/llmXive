# Feature Specification: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases

**Feature Branch**: `001-corrosion-rate-prediction`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases"

## User Scenarios & Testing

### User Story 1 - Data Ingestion, Validation, and Harmonization (Priority: P1)

A researcher needs to ingest a raw tabular corrosion dataset from a public source (Zenodo/OpenML), validate the presence of all required variables (pH, salinity, temperature, material composition), harmonize corrosion rate units to mm/year, and impute missing non-target values to create a clean, analysis-ready DataFrame.

**Why this priority**: Without a validated, normalized dataset containing the specific predictors and outcome required by the research question, no modeling or analysis can proceed. This is the foundational block; if the data lacks a required variable, the project scope must be immediately adjusted or halted.

**Independent Test**: This can be fully tested by running the data ingestion script against a known sample CSV and verifying the output DataFrame contains no null values in critical columns, normalized numeric ranges, correctly encoded categorical features, and harmonized corrosion rate units.

**Acceptance Scenarios**:

1. **Given** a raw CSV file with missing pH values and unencoded metal types, **When** the preprocessing pipeline runs, **Then** missing pH values are imputed (e.g., via median) and metal types are one-hot encoded without raising errors.
2. **Given** a dataset with temperature values in Celsius and salinity in ppt, **When** normalization is applied, **Then** all numeric environmental features are scaled to a [0, 1] range or standardized (mean=0, std=1) as configured.
3. **Given** a dataset lacking a specific required column (e.g., "pH", "salinity", or "temperature"), **When** the column validation check runs, **Then** the system halts execution with a clear error message listing the missing variable and the specific dataset source. If an optional column (e.g., "crystal structure") is missing, the system logs a warning and proceeds.

---

### User Story 2 - Interaction Feature Engineering and Model Training (Priority: P2)

A researcher needs to explicitly construct interaction terms (e.g., pH × salinity) and train interpretable machine learning models (Random Forest/Gradient Boosting) on CPU-only hardware to predict corrosion rates, while comparing against a null model to validate the necessity of interaction terms via a formal statistical test.

**Why this priority**: The core research question asks for the *interaction* between factors. Simply training a model on raw features fails to address the "how do these drivers interact" aspect. This step directly enables the hypothesis testing regarding non-linear dependencies.

**Independent Test**: This can be tested by verifying that the feature matrix includes the engineered interaction columns, that the system trains both a Full Model and a Null Model, and that the system performs a statistical test to validate the incremental variance explained by interactions.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with pH and salinity columns, **When** feature engineering runs, **Then** a new column `pH_x_salinity` is created and included in the training matrix.
2. **Given** a training set of N rows, **When** the Random Forest model trains with `max_depth=5` and `n_estimators=100` on a CPU-only environment (2 vCPUs, 7 GB RAM), **Then** the training completes within 30 minutes and peak RSS memory usage remains below 7 GB without memory errors. If memory is exceeded, the system MUST trigger the stratified sampling strategy.
3. **Given** a model trained on the interaction features, **When** evaluated on the test set, **Then** the system calculates and reports the RMSE and R² metrics, and performs a permutation test to confirm the Full Model significantly outperforms the Null Model (p ≤ 0.05).

---

### User Story 3 - Interpretability Analysis and Driver Ranking (Priority: P3)

A researcher needs to generate SHAP (SHapley Additive exPlanations) values and partial dependence plots to rank the importance of environmental vs. material drivers and visualize non-linear interaction effects, specifically using SHAP Interaction Values to decompose variance and identify dominant risk factors.

**Why this priority**: This addresses the "mechanistic drivers" gap. It transforms the "black box" prediction into actionable scientific insight, identifying which specific interactions (e.g., high salinity + low pH) dominate corrosion rates, fulfilling the project's primary scientific goal.

**Independent Test**: This can be tested by running the SHAP analysis script on the trained model and verifying that the output includes a summary plot where interaction terms are explicitly flagged and their aggregate contribution is calculated.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** SHAP Interaction Values are computed, **Then** the system outputs a ranked list where interaction terms are explicitly flagged and their aggregate SHAP contribution is calculated.
2. **Given** a specific interaction feature (e.g., `temp_x_salinity`), **When** a partial dependence plot is generated, **Then** the plot visualizes the non-linear relationship between the interaction term and the predicted corrosion rate.
3. **Given** the feature importance rankings, **When** the system aggregates the results, **Then** it outputs a ranked list of drivers where environmental interactions are explicitly distinguished from static material properties.

---

### Edge Cases

- **What happens when the public dataset is too large?** If the raw dataset exceeds available RAM capacity (7 GB), the system MUST automatically sample a stratified subset of rows or filter to the most relevant metal types to fit the compute constraints, logging the sampling strategy and random seed for reproducibility.
- **How does the system handle collinear predictors?** If two predictors are definitionally related (e.g., composition ratio vs. total alloy percentage), the system MUST flag this in the diagnostics (as defined in FR-006) and avoid claiming independent predictive effects for both, instead reporting them as a joint descriptive relationship. Interaction terms are excluded from this check.
- **What happens if the dataset lacks a required variable?** If a critical variable (e.g., "pH", "salinity", "temperature") is missing from the source data, the system MUST NOT hallucinate values; it MUST halt and emit a clear error message: `Error: MISSING_VARIABLE [variable_name] in [dataset_source]`. If an optional variable (e.g., "crystal structure") is missing, the system logs a warning and proceeds.
- **What happens if the dataset is observational?** Since the data is observational, the system MUST ensure all output interpretations explicitly frame findings as **associational** correlations, never causal effects, in the final report and visualizations.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest tabular data from public repositories (Zenodo/OpenML), validate the presence of required columns (pH, salinity, temperature, material composition, corrosion rate), and harmonize corrosion rate values to a standard unit (mm/year) while flagging records with non-standard measurement methods. "Crystal structure" is treated as optional; if missing, the system logs a limitation but proceeds. (See US-1).
- **FR-002**: System MUST explicitly engineer interaction features (e.g., `pH * salinity`, `temperature * composition_ratio`) and polynomial features to capture non-linear relationships before model training. Additionally, the system MUST train a "Null Model" (additive only, no interactions) and perform a formal statistical test (permutation test or F-test) to calculate and report the variance difference (ΔR²) between the Full and Null models to validate the interaction hypothesis. (See US-2).
- **FR-003**: System MUST train interpretable regression models (Random Forest or Gradient Boosting) using `scikit-learn` with constraints: `max_depth <= 5`, `n_estimators <= 200`, and **NO** GPU acceleration or 8-bit quantization libraries. If memory constraints (>7 GB) are violated without quantization, the system MUST trigger the stratified sampling strategy defined in Edge Cases. (See US-2).
- **FR-004**: System MUST generate SHAP Interaction Values (2D matrix) and partial dependence plots to quantify and visualize the contribution of each feature and interaction term to the predicted corrosion rate. The system MUST aggregate the off-diagonal SHAP values to calculate the total variance contribution of interactions. (See US-3).
- **FR-005**: System MUST apply a multiple-comparison correction (e.g., Benjamini-Hochberg procedure) to feature importance p-values. For tree-based models, the system MUST first generate empirical p-values via a permutation test (resampling) before applying the correction. (See US-3).
- **FR-006**: System MUST detect collinear predictors (e.g., via Variance Inflation Factor > 5) and emit a diagnostic warning listing the correlated pairs, ensuring they are not interpreted as independent drivers. This check MUST exclude interaction terms from the calculation to avoid flagging structural collinearity. (See US-1).
- **FR-007**: System MUST perform a sensitivity analysis on the model's decision thresholds or hyperparameters (e.g., `max_depth` ∈ {3, 5, 7}) to assess the robustness of the identified interaction drivers, reporting how the top-ranked features change across the sweep. (See US-3).

### Key Entities

- **CorrosionRecord**: Represents a single data point containing environmental conditions, material properties, and the measured corrosion rate (harmonized to mm/year).
- **InteractionFeature**: A derived entity representing a constructed variable (e.g., `pH_x_salinity`) used to model non-linear dependencies.
- **ModelArtifact**: The trained model object, feature importance rankings, SHAP analysis results, and Null Model comparison metrics saved for reproducibility.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Predictive performance (R² and RMSE) is measured against a held-out test set to ensure generalizability. (See US-2).
- **SC-002**: The incremental variance explained by interaction terms is measured by comparing the R² of the Full Model (with interactions) against the Null Model (additive only) using a permutation test with a significance threshold of α ≤ 0.05. (See US-3).
- **SC-003**: Computational feasibility is measured against the constraint of completing the full pipeline (data download, cleaning, training, SHAP analysis, and report generation) within 6 hours on a CPU-only environment (2 vCPUs, 7 GB RAM). (See US-2).
- **SC-004**: Methodological validity is measured by the presence of a multiple-comparison correction (Benjamini-Hochberg procedure) applied to feature importance p-values derived from a permutation test. (See US-3).
- **SC-005**: Hyperparameter sensitivity is measured by the stability of the top-5 feature list when model hyperparameters (e.g., `max_depth`) are varied within a defined range, defined as a Jaccard similarity index ≥ 0.8 between the feature sets. (See US-3).
- **SC-006**: Observational framing is measured by the presence of explicit disclaimers in all visualizations and text stating that correlations are **associational** and not causal. (See US-1).

## Assumptions

- **Dataset Availability**: It is assumed that a public tabular dataset containing at least 1,000 rows with the required variables (pH, salinity, temperature, composition, corrosion rate) exists on Zenodo or OpenML. If the dataset is missing an optional variable (e.g., crystal structure), the scope is limited to the available variables, and the missing variable is recorded as a limitation.
- **Observational Nature**: The analysis assumes the data is observational (no random assignment). Therefore, all findings regarding "drivers" will be framed as **associational** correlations, not causal effects, in the final report.
- **Compute Constraints**: The analysis assumes the entire dataset can be processed in memory (≤7 GB RAM) or via sampling. If the raw data is larger, a stratified sampling strategy (maintaining class balance of metal types) will be applied.
- **Model Interpretability**: It is assumed that SHAP Interaction Values can be computed for the selected models (Random Forest/Gradient Boosting) within the 6-hour time limit on CPU.
- **Threshold Justification**: Any threshold used for feature selection (e.g., "top 10 features") is assumed to be based on a community standard (e.g., cumulative SHAP value > 90%) rather than an arbitrary number, and will be validated via the sensitivity analysis.
- **Measurement Validity**: It is assumed that the corrosion rate values in the public datasets can be harmonized to a common unit (mm/year). Records derived from non-standard measurement techniques (e.g., electrochemical polarization vs. mass loss) will be flagged and analyzed separately or excluded if harmonization is not possible, to prevent heteroscedasticity bias.
- **Variable Completeness**: The project scope is strictly limited to datasets where pH, salinity, and temperature are provided as distinct, disaggregated columns. If a source dataset aggregates these into a single 'environmental index' or lacks any of these three variables, the ingestion pipeline MUST halt execution (as defined in FR-001) and report the specific missing variable. The research question regarding 'interaction effects' requires these distinct inputs; therefore, datasets with aggregated indices are excluded from the analysis scope rather than attempting imputation or proxy derivation. Crystal structure is treated as optional; if missing, the system proceeds with a logged limitation.