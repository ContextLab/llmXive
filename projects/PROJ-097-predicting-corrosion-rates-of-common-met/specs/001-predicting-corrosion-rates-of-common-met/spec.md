# Feature Specification: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases

**Feature Branch**: `001-predicting-corrosion-rates-of-common-met`  
**Created**: 2026-10-13  
**Status**: Draft  
**Input**: User description: “How do interaction effects between specific environmental stressors (pH, salinity, temperature) and material properties (composition, crystal structure) quantitatively determine experimentally measured corrosion rates across common metals in publicly available datasets?”  

## User Scenarios & Testing

### User Story 1 – Data Ingestion, Validation, and Harmonization (Priority: P1)

A researcher needs to ingest raw tabular corrosion datasets from public repositories, verify that all required columns (pH, salinity, temperature, material composition, corrosion rate) are present, harmonize corrosion‑rate units to mm / year, and impute missing non‑target values to produce a clean, analysis‑ready DataFrame.

**Why this priority**: Without a validated, normalized dataset containing the exact predictors and outcome required by the research question, no modeling or analysis can proceed. This is the foundational block; if a required variable is missing, the project scope must be adjusted or halted.

**Independent Test**: Run the ingestion script on a known sample CSV and verify that the output DataFrame contains no nulls in the required columns, that numeric variables are correctly scaled, that categorical material descriptors are one‑hot encoded, and that corrosion‑rate units are harmonized.

**Acceptance Scenarios**  

1. **Given** a raw CSV with missing pH values and unencoded metal types, **When** the preprocessing pipeline runs, **Then** missing pH values are imputed with the median and metal types are one‑hot encoded without raising errors. *(See FR-008)*  
2. **Given** a dataset with temperature in °C and salinity in ppt, **When** normalization is applied, **Then** all numeric environmental features are standardized (mean = 0, std = 1) as configured. *(See FR-008)*  
3. **Given** a dataset lacking a required column such as “pH”, **When** the column‑validation check runs, **Then** execution halts with a clear error message listing the missing variable and its source. If an optional column (e.g., “crystal structure”) is missing, the system logs a warning and proceeds. *(See FR-001)*  

---

### User Story 2 – Interaction Feature Engineering and Model Training (Priority: P2)

A researcher needs to construct explicit interaction features (e.g., pH × salinity) and train interpretable regression models (Random Forest and Gradient Boosting) on CPU‑only hardware, then compare performance against a baseline additive model to test whether interactions provide a statistically significant gain.

**Why this priority**: The core research question asks for the *interaction* between factors. Training a model without engineered interactions would not address this aspect. This step enables hypothesis testing about non‑linear dependencies.

**Independent Test**: Verify that the feature matrix includes engineered interaction columns, that both a Full Model (with interactions) and a Null Model (same algorithm without interaction columns) are trained, and that a permutation test confirms any performance gain.

**Acceptance Scenarios**  

1. **Given** a preprocessed dataset with pH and salinity columns, **When** feature engineering runs, **Then** a new column `pH_x_salinity` is created and included in the training matrix. *(See FR-002)*  
2. **Given** a training set of N rows, **When** the Random Forest model trains with `max_depth=5` and `n_estimators=200` on a CPU‑only environment (A modest number of vCPUs, 7 GB RAM), **Then** training completes within 30 minutes and peak RSS stays below 7 GB. If memory is exceeded, the system triggers the stratified‑sampling strategy. *(See FR-003)*  
3. **Given** a model trained on interaction features, **When** it is evaluated on the held‑out test set, **Then** RMSE and R² are reported and a permutation test shows the Full Model significantly outperforms the Null Model (p ≤ 0.05, upper‑tail). *(See FR-002, SC-002)*  

---

### User Story 3 – Interpretability Analysis and Driver Ranking (Priority: P3)

A researcher needs to generate SHAP interaction values and partial‑dependence plots to rank the importance of environmental vs. material drivers and visualize the most influential interaction effects.

**Why this priority**: This transforms the predictive model into actionable scientific insight, identifying which specific interactions (e.g., high salinity × low pH) dominate corrosion rates, thereby fulfilling the primary scientific goal.

**Independent Test**: Run the SHAP analysis script on the best‑performing model and verify that the output includes (i) a summary plot with interaction terms flagged, (ii) interaction dependence plots for the top three interactions, and (iii) partial‑dependence curves illustrating non‑linear effects.

**Acceptance Scenarios**  

1. **Given** a trained Random Forest model, **When** SHAP Interaction Values are computed, **Then** the system outputs a ranked list where interaction terms are explicitly flagged and their aggregate SHAP contribution is calculated. *(See FR-004)*  
2. **Given** a specific interaction feature such as `temp_x_salinity`, **When** a partial‑dependence plot is generated, **Then** the plot visualizes the non‑linear relationship between that interaction and predicted corrosion rate. *(See FR-004)*  
3. **Given** the feature‑importance rankings, **When** the system aggregates the results, **Then** it outputs a ranked list of drivers that distinguishes environmental interactions from static material properties. *(See FR-005, SC-005)*  

---

### Edge Cases

- **Dataset exceeds RAM (7 GB)** – The system automatically samples a stratified subset of rows or filters to the most relevant metal types, logs the sampling strategy and random seed, and proceeds. *(See FR-003)*  
- **Collinear predictors** – If two predictors are definitionally related (e.g., composition ratio vs. total alloy percentage), the system flags the pair in diagnostics and avoids claiming independent effects for both; interaction terms are excluded from this check. *(See FR-006)*  
- **Missing required variable** – Execution halts with a clear error `Error: MISSING_VARIABLE [variable_name] in [dataset_source]`. Optional variables trigger a warning only. *(See FR-001)*  
- **Observational data** – All output interpretations are explicitly framed as **associational** correlations, never causal claims. *(See SC-006)*  

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest tabular data from public repositories (Zenodo/OpenML), validate the presence of required columns (pH, salinity, temperature, material composition, corrosion rate), and harmonize corrosion‑rate values to a standard unit (mm / year) while flagging records with non‑standard measurement methods. “Crystal structure” is optional; if missing, the system logs a limitation but proceeds. *(See User Story 1)*
- **FR-002**: System MUST explicitly engineer interaction features (e.g., `pH * salinity`, `temperature * composition_ratio`) and polynomial features (of a low degree) before model training. It MUST also train a **Null Model** that uses the same Random Forest algorithm **without** the engineered interaction columns, and perform an **interaction‑column permutation test**: repeatedly shuffle only the interaction columns (keeping all other predictors and the target fixed), recompute the RMSE difference (ΔRMSE = RMSE_Null − RMSE_Full) for each shuffle, and calculate a p‑value as the proportion of shuffled ΔRMSE ≥ observed ΔRMSE. This test isolates the contribution of interaction features, unlike a target‑permutation which would shuffle the response variable. Significance is assessed at α ≤ 0.05. *(See User Story 2)*
- **FR-003**: System MUST train interpretable regression models (Random Forest or Gradient Boosting) using scikit‑learn with constraints: `max_depth ≤ 5`, `n_estimators ≤ 200`, **NO** GPU acceleration or 8‑bit quantization libraries. If peak RSS > 7 GB (detected via psutil), the system MUST trigger the stratified‑sampling strategy defined in Edge Cases. *(See User Story 2)*
- **FR-004**: System MUST generate SHAP Interaction Values (2‑D matrix) and partial‑dependence plots **for interpretation only**; these visualizations aid understanding but are not used as independent validation of interaction importance. *(See User Story 3)*
- **FR-005**: System MUST apply the Benjamini‑Hochberg (BH) multiple‑comparison correction to feature‑importance p‑values. For tree‑based models, empirical p‑values are obtained via the interaction‑column permutation test (see FR‑002) before BH correction. *(See User Story 3, SC-004)*
- **FR-006**: System MUST detect collinear predictors (Variance Inflation Factor > 5) and emit a diagnostic warning listing correlated pairs, ensuring they are not interpreted as independent drivers. This check excludes interaction terms to avoid flagging structural collinearity. *(See User Story 3)*
- **FR-007**: System MUST perform a sensitivity analysis on model hyperparameters. Specifically, it MUST sweep `max_depth` ∈ {3, 4, 5} (respecting FR‑003) and report how the top‑5 feature list changes across the sweep, using a Jaccard similarity ≥ 0.8 as the stability criterion (community‑standard for feature‑set stability). *(See User Story 3)*
- **FR-008**: System MUST impute missing non‑target values (median for numeric, mode for categorical), scale numeric predictors to standard scores (mean = 0, std = 1), and one‑hot encode categorical metal types as part of the preprocessing pipeline. *(See User Story 1)*
- **FR-009**: System MUST split the dataset into training and test folds using a **group‑aware** strategy: no samples from the same experimental batch or source study may appear in both sets. Implemented via `GroupKFold` (5 folds) based on a `source_id` column. *(See User Story 2)*
- **FR-010**: System MUST perform 5‑fold **GroupKFold** cross‑validation and conduct a constrained grid‑search over hyperparameters (`max_depth` ∈ {3, 4, 5}, `n_estimators` ∈ {50, 100, 150}) within the limits of FR‑003. The best model is selected by highest cross‑validated R². *(See User Story 2)*
- **FR-011**: System MUST record provenance for every ingested dataset: store the dataset DOI, URL, and a SHA‑256 checksum in a `metadata/` directory to ensure reproducibility. *(See User Story 1)*
- **FR-012**: System MUST perform an independent permutation‑importance test on each engineered interaction column (shuffling the column values while keeping all others fixed) and report a p‑value for its contribution to model performance; significance is assessed after Benjamini‑Hochberg correction. This provides a non‑circular validation of interaction relevance. *(See User Story 3)*

### Key Entities

- **CorrosionRecord** – A single observation containing environmental conditions, material properties, and the measured corrosion rate (harmonized to mm / year).  
- **InteractionFeature** – A derived variable representing a constructed interaction (e.g., `pH_x_salinity`).  
- **ModelArtifact** – The trained model object, feature‑importance rankings, SHAP analysis results, and Null‑Model comparison metrics saved for reproducibility.  

## Success Criteria

### Measurable Outcomes

- **SC-001**: Predictive performance (R² and RMSE) measured on a **group‑aware 5‑fold cross‑validation** must exceed the baseline mean‑only model (which predicts the training‑set mean corrosion rate for every test sample) by **≥ 0.05** in R² (or improve RMSE by **≥ 10 %**). The baseline model is trained on the identical training folds and evaluated on the same test folds as the Full Model. *(See User Story 2)*
- **SC-002**: The incremental variance explained by interaction terms must be demonstrated by the **interaction‑column permutation test** (as defined in FR‑002) comparing the Full Model to the Null Model with significance **α ≤ 0.05** (upper‑tail: proportion of shuffled ΔRMSE ≥ observed). *(See User Story 2)*
- **SC-003**: The entire pipeline (data download, cleaning, training, SHAP analysis, and report generation) must complete within **6 hours** on a free‑tier GitHub Actions runner (2 vCPUs, 7 GB RAM). *(See User Story 2)*
- **SC-004**: Benjamini‑Hochberg correction must be applied to all feature‑importance p‑values derived from the permutation test. *(See User Story 3)*
- **SC-005**: Hyperparameter sensitivity must yield a Jaccard similarity **≥ 0.8** between the top‑5 feature lists across the `max_depth` sweep, indicating stable importance rankings. *(See User Story 3)*
- **SC-006**: All visualizations and textual conclusions must contain an explicit disclaimer that findings are **associational** (not causal) because the data are observational. *(See User Story 3)*
- **SC-007**: The data ingestion, validation, and harmonization pipeline (User Story 1) is considered successful when it (a) completes without runtime errors, (b) produces a DataFrame containing **all required columns** with **zero nulls** in those columns, and (c) reports unit harmonization for corrosion rate. Success is measured on a held‑out validation CSV and must achieve **≥ 95 %** pass rate on these checks (empirical pass rate calculated over three independent validation runs). *(See User Story 1)*

## Assumptions

- **Dataset Availability** – At least one public tabular dataset with ≥ 1 000 rows containing the required variables (pH, salinity, temperature, composition, corrosion rate) exists on Zenodo or OpenML. Optional variables (e.g., crystal structure) may be absent; their absence is logged as a limitation.  
- **Observational Nature** – The data are observational; therefore, all statements about “drivers” are framed as correlational, not causal.  
- **Compute Constraints** – The dataset can be processed in memory within the 7 GB RAM limit, or a stratified sampling strategy will be applied if necessary. All modeling runs on CPU‑only hardware (2 vCPUs, 7 GB RAM) and complete within the 6‑hour wall‑time budget.  
- **Model Interpretability Feasibility** – SHAP Interaction Values for Random Forest and Gradient Boosting can be computed on the CPU within the time budget.  
- **Threshold Justification** – The Jaccard similarity threshold of 0.8 for feature‑set stability follows community practice for assessing robustness of importance rankings; the top‑5 feature selection threshold (cumulative SHAP contribution > 90 %) is also a widely used standard. Both thresholds are validated via the sensitivity analysis (FR‑007).  
- **Measurement Validity** – Corrosion‑rate values can be harmonized to a common unit (mm / year). Records derived from non‑standard measurement techniques (e.g., electrochemical polarization vs. mass loss) will be flagged and either analyzed separately or excluded to avoid heteroscedasticity bias.  
- **Variable Completeness** – Only datasets that provide pH, salinity, and temperature as distinct columns are included; datasets that aggregate these into a single index are excluded, causing the ingestion pipeline to halt with a clear error (FR‑001).  
- **Provenance Recording** – All ingested datasets will have their DOI, URL, and SHA‑256 checksum recorded as mandated by FR‑011 to satisfy reproducibility requirements.  
