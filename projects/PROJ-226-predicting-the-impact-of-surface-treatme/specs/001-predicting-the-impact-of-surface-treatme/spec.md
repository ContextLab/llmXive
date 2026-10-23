# Feature Specification: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

**Feature Branch**: `001-predicting-adhesion-strength`
**Created**: 2026-06-28
**Status**: Draft
**Input**: User description: "Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system MUST retrieve, parse, and standardize raw adhesion data from public repositories (NIST, Zenodo, Materials Project) into a unified analysis-ready format. This includes handling missing values, encoding categorical treatment types, and scaling continuous parameters.

**Why this priority**: Without a clean, unified dataset, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: The pipeline can be executed end-to-end on a representative sample of records (using the committed synthetic fixture `fixtures/synthetic_ingestion_sample.csv`); it outputs a single CSV file with standardized columns and no missing critical values, which can be loaded into a pandas DataFrame without error.

**Acceptance Scenarios**:

1. **Given** raw CSV files from NIST and Zenodo containing mixed units and missing plasma power values, **When** the ingestion script runs, **Then** the output CSV contains a standardized `plasma_power_w` column with median imputation applied to missing entries, all units are converted to SI standards (watts, seconds, percent), and categorical treatment types are canonicalized to a single label (e.g., "Oxygen Plasma").
2. **Given** a dataset where `treatment_type` contains variations like "O2 Plasma", "Oxygen Plasma", and "O2-plasma", **When** the preprocessing step executes, **Then** these are mapped to a single canonical category "Oxygen Plasma" in the `treatment_type` column.
3. **Given** a record with a missing `substrate_roughness_nm` value, **When** the pipeline processes the data, **Then** the value is replaced with the median roughness of the specific substrate class (per‑substrate‑class median imputation), and a log entry flags the imputation.

---

### User Story 2 - Predictive Model Training and Validation (Priority: P2)

The system MUST train multiple regression models (Random Forest, Gradient Boosting, Linear Regression) on the prepared dataset using stratified cross‑validation to predict adhesion strength from surface treatment parameters.

**Why this priority**: This is the core research activity. It directly addresses the research question by attempting to quantify the relationship between inputs and outputs.

**Independent Test**: The training script completes within **≤ 3.5 hours** on a CPU‑only runner, outputs a JSON file containing the best model's hyperparameters, validation R² score, and RMSE, and saves the model artifact.

**Acceptance Scenarios**:

1. **Given** a training set of 500 records split 70/15/15 using a **grouped split by polymer‑substrate pair** (see FR-010), **When** the model training job runs with a grid search of multiple combinations, **Then** the system selects the Random Forest model (or equivalent best performer) and reports a validation R² **≥ 0.5** (meeting the scientific target) and a runtime ≤ 3.5 hours.
2. **Given** the trained models, **When** the evaluation step runs on the held‑out test set, **Then** the system outputs a `test_r2`, `test_rmse`, and `test_mae` for each model, stored in a results JSON file.
3. **Given** the best performing model, **When** a cross‑validation with multiple folds is re‑run on the full training set, **Then** the mean R² across folds is within 0.05 of the validation R² reported during grid search, confirming stability.

---

### User Story 3 - Statistical Significance and Interpretability Reporting (Priority: P3)

The system MUST perform a permutation test to establish statistical significance of the model's performance and generate SHAP values to interpret the contribution of each treatment parameter to adhesion strength.

**Why this priority**: This validates that the observed relationships are not due to chance and provides actionable insights for engineers, fulfilling the "explain variance" and "quantitative relationship" goals of the research question.

**Independent Test**: The analysis script generates a permutation p‑value < 0.05 (or reports the specific value) and a SHAP summary plot image, both saved to the artifacts directory.

**Acceptance Scenarios**:

1. **Given** the best model and the test set, **When** a permutation test with a sufficiently large number of shuffles is executed, **Then** the system calculates a p‑value and reports it in the final report; if p < 0.05, the relationship is flagged as statistically significant.
2. **Given** the best model, **When** SHAP analysis is performed, **Then** the system outputs a summary plot (PNG) and a JSON file ranking features by mean absolute SHAP value, clearly identifying the top predictors (e.g., plasma power, exposure time, chemical concentration). For linear models, the system falls back to `shap.LinearExplainer` or `shap.KernelExplainer` as specified in FR-015.
3. **Given** the full results, **When** the final report is generated, **Then** it includes a section stating the proportion of variance explained (R²) with 95 % bootstrapped confidence intervals, per‑predictor significance (p < 0.05) where applicable, and a statement on whether the R² ≥ 0.5 target was met. The report also contains the four required visualizations: predicted‑vs‑actual scatter, residual histogram, SHAP summary plot, and parameter‑response curves (see FR-014).

### Edge Cases

- **Sparse‑group handling**: If a specific polymer‑substrate pair has fewer than **5** data points, the system must **exclude** that pair from model training or **aggregate** it with chemically similar pairs, as required by FR-011.
- **Unit‑mismatch detection**: When a dataset reports `plasma_power_w` in kW instead of W, or `exposure_time` in minutes instead of seconds, the system must detect the mismatch using per‑source unit‑metadata JSON files (FR-009). It then applies the appropriate conversion factor; if metadata are missing, the pipeline raises a clear `UnitMismatchError`.
- **Null‑result reporting**: If the best model is a simple Linear Regression with R² < 0.1, the system must still produce a complete report indicating the low performance as a valid “null” finding (FR-012).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST retrieve datasets from NIST, Zenodo, and Materials Project using `wget` or `curl` and parse them into a unified pandas DataFrame structure. (See US-1)
- **FR-002**: The system MUST impute missing numeric values using the **per‑substrate‑class median** and one‑hot encode categorical treatment types **and** the polymer‑substrate pair identifier. (See US-1)
- **FR-003**: The system MUST train at least three distinct regression models (Random Forest, Gradient Boosting, Linear Regression) using scikit-learn with a maximum of 50 hyperparameter combinations. (See US-2)
- **FR-004**: **[REPLACED BY FR-010]** *(see FR-010)*
- **FR-005**: The system MUST execute a permutation test with exactly 1,000 shuffles to calculate the p‑value for the observed R² score. (See US-3)
- **FR-006**: The system MUST generate SHAP values for the best performing model to rank feature importance. (See US-3)
- **FR-007**: The system MUST output a final report containing R², its 95 % bootstrapped confidence interval, RMSE, MAE, p‑value, feature importance rankings, and per‑predictor significance (p < 0.05) in both JSON and Markdown formats. (See US-3)
- **FR-008**: The system MUST normalise all numeric units to SI (watts, seconds, percent) and canonicalise treatment‑type strings to a predefined taxonomy (e.g., “Oxygen Plasma”). (See US-1)
- **FR-009**: The system MUST validate unit consistency using per‑source unit‑metadata files; on mismatch it either converts using the metadata or raises a `UnitMismatchError`. (See Edge Cases)
- **FR-010**: The system MUST perform a **grouped** train/validation/test split (70/15/15) based on the **polymer‑substrate pair identifier** to prevent data leakage. (See US-2)
- **FR-011**: The system MUST handle sparse polymer‑substrate groups (< 5 records) by exclusion or aggregation as described in Edge Cases. (See Edge Cases)
- **FR-012**: The system MUST report low‑performing (“null”) model results without error, clearly labeling them as such. (See Edge Cases)
- **FR-013**: The system MUST compute per‑predictor significance (p < 0.05) using linear model coefficients where appropriate and include these in the final report. (See US-3)
- **FR-014**: The system MUST generate the following visualizations for the best model: (i) predicted‑vs‑actual scatter plot, (ii) residual histogram, (iii) SHAP summary plot, and (iv) parameter‑response curves. (See US-3)
- **FR-015**: The system MUST provide a fallback SHAP explainer (LinearExplainer or KernelExplainer) for non‑tree models to satisfy FR-006. (See US-3)

### Key Entities

- **TreatmentRecord**: Represents a single experimental observation. Key attributes: `treatment_type`, `plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`, `pair_id` (polymer‑substrate identifier).
- **ModelArtifact**: Represents a trained model instance. Key attributes: `model_type`, `hyperparameters`, `validation_r2`, `test_r2`, `shap_values`.
- **AnalysisResult**: Represents the aggregate outcome of the research. Key attributes: `best_model_type`, `final_r2`, `confidence_interval`, `p_value`, `top_predictors`, `per_predictor_significance`, `visualizations`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of variance in adhesion strength explained by the model is measured against the target of **R² ≥ 0.5**. (See US-2, US-3)
- **SC-002**: The statistical significance of the model's predictive power is measured against the threshold of **p < 0.05** via permutation test. (See US-3)
- **SC-003**: The model's predictive accuracy is measured against the test set using **RMSE** and **MAE** metrics. (See US-2)
- **SC-004**: The feature importance ranking is measured by the stability of SHAP values across k‑fold cross‑validation (with the number of folds to be determined during the implementation phase) (standard deviation of SHAP mean < 0.1). (See US-3)
- **SC-005**: The total compute time for the entire pipeline (ingestion to reporting) is measured against the **Short‑duration free‑tier CI limit**. (See US-1, US-2)
- **SC-006**: All four required visualizations (predicted‑vs‑actual, residual histogram, SHAP summary, parameter‑response curves) are generated and included in the final report. (See US-3)

## Assumptions

- The public datasets (NIST, Zenodo, Materials Project) contain the required variables: plasma power, exposure time, chemical concentration, polymer surface energy, substrate roughness, and adhesion strength. Because public adhesion corpora are heterogeneous, the ingestion pipeline applies the following concrete rule (community‑standard practice for heterogeneous materials data): (a) if a field is present for **≥ 80 %** of records in a source, missing values are median‑imputed **per substrate class** per FR‑002 and the imputation is logged; (b) if a field is present for **< 80 %** of records, the field is retained but flagged as low‑coverage, and the pipeline reports the per‑field coverage percentage in the final report; (c) any record missing the target `adhesion_strength_mj_m2` is excluded. This coverage‑handling policy is a documented operator‑led design default chosen to preserve the maximum usable corpus while making imputation extent explicit; it does not depend on the specific Zenodo DOI's schema.
- The relationship between treatment parameters and adhesion strength is primarily associational; causal claims will not be made without randomization data.
- The dataset size is sufficient for a 70/15/15 split (minimum **200** records) to allow for meaningful model training and testing.
- The free‑tier GitHub Actions runner (Multiple CPUs, 7 GB RAM) is sufficient for training Random Forest and Gradient Boosting models on a dataset of **< 5,000** records.
- The "best" model is selected solely based on validation R², not on model complexity or training time.
- SHAP analysis will be performed using the `shap` library's CPU‑compatible `TreeExplainer` for tree‑based models; for linear models the fallback `LinearExplainer` or `KernelExplainer` will be used as required by FR‑015 to ensure feasibility within the 6‑hour limit.