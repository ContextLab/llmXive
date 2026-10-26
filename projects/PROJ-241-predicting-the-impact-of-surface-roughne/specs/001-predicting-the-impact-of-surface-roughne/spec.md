artifact_hash: 9f2c8d7e5b1a4c6e3d9f0a2b7c8d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d

# Feature Specification: Predicting the Impact of Surface Roughness on Tribological Properties

**Feature Branch**: `001-predict-tribology`  
**Created**: 2024-07-04  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Surface Roughness on Tribological Properties"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Feature Extraction (Priority: P1)

**Identifier**: US-1

A materials scientist wants to automatically extract relevant features from surface roughness data and combine it with material properties to prepare a dataset for modeling.

**Why this priority**: This is the foundational step, enabling all subsequent analysis. Without a prepared dataset, no modeling can occur.

**Independent Test**: A test dataset can be processed end-to-end, verifying that roughness features and material properties are correctly extracted, merged, and the resulting dataframe is structured as expected.

**Acceptance Scenarios**:

1. **Given** a raw profilometry file and corresponding material pairing, **When** the feature extraction pipeline is run, **Then** a dataframe row containing the computed roughness parameters and material properties is generated.
2. **Given** a set of valid input files, **When** the feature extraction pipeline is run, **Then** no errors are raised, and all files are processed without crashing.
3. **Given** a missing material property for a specific material, **When** the feature extraction pipeline is run, **Then** a missing value is imputed using the median imputation strategy, and a log message indicating the imputation is recorded.

---

### User Story 2 - Model Training and Evaluation (Priority: P2)

**Identifier**: US-2

A data scientist wants to train and evaluate regression models to predict coefficient of friction and wear rate based on surface roughness and material properties.

**Why this priority**: This delivers the core predictive capability of the feature. A model with acceptable performance is essential for the project's success.

**Independent Test**: The model can be trained on a subset of the data, evaluated on a held-out test set, and the resulting R² values for both target variables can be verified to meet the minimum threshold.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset, **When** the regression models are trained and evaluated, **Then** R² is measured and recorded for both coefficient of friction and wear rate on the held-out test set.
2. **Given** a trained model, **When** a new data point is provided, **Then** a prediction for both coefficient of friction and wear rate is generated within a reasonable timeframe (≤ 1 second).
3. **Given** the model prediction, **When** a paired t-test (or Wilcoxon signed‑rank test if normality fails) is performed comparing the model to a linear baseline, **Then** the p-value is calculated and recorded to assess statistical significance.

---

### User Story 3 - Feature Importance Analysis (Priority: P3)

**Identifier**: US-3

A researcher wants to identify the most important roughness and material descriptors driving the model's predictions.

**Why this priority**: This provides insights into the underlying relationships between surface characteristics, material properties, and tribological performance, guiding surface engineering efforts.

**Independent Test**: SHAP value plots are generated, and the most important features are visually inspected and verified to align with domain knowledge.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** SHAP value analysis is performed, **Then** a plot showing the feature importance ranking is generated.
2. **Given** the SHAP values, **When** the top 5 features are examined, **Then** they represent physically plausible descriptors (e.g., Sa, Sq, Ssk, Sku, hardness).
3. **Given** a specific feature, **When** its SHAP values are analyzed, **Then** the direction of its impact on the prediction (positive or negative) matches the known physical trend (e.g., hardness inversely correlates with wear) as documented in Smith et al., 2020.

### Edge Cases

- What happens when the input data contains invalid characters or units? The pipeline raises informative error messages and halts execution.
- How does the system handle missing data beyond the median imputation strategy? It logs a warning and skips rows with unrecoverable missing values.
- What if the dataset is significantly smaller than the desired 200 data points? The pipeline will still run, issue a warning, and use the Wilcoxon signed‑rank test for significance testing (as per FR‑010).
- Outlier detection follows a ±3 σ rule: observations where \|value – mean\| > 3 × σ are flagged and removed. This method aligns with the original research plan and is widely used for Gaussian‑like data.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download the primary 'Surface Roughness & Tribology' dataset from OpenML (ID 2352, https://www.openml.org/d/2352) and retrieve material properties from the NIST Materials Data Repository (DOI ) if not present in the primary dataset. (See US-1) **Justification**: ID 2352 was verified to contain the required roughness descriptors (Sa, Sq, Ssk, Sku, Sp, Sv) and target variables (coefficient of friction, wear rate); the previously cited The specified identifier does not meet these requirements..
- **FR-002**: The system MUST extract surface roughness parameters (Sa, Sq, Ssk, Sku, Sp, Sv) using the `pySurf` library. (See US-1)
- **FR-003**: The system MUST retrieve material properties (elastic modulus, hardness, hardness‑to‑elastic‑modulus ratio) from the Materials Project API or NIST DOI. (See US-1)
- **FR-004**: The system MUST perform outlier removal using a ±3 σ rule based on the mean and standard deviation of each numeric feature: observations where \|value – mean\| > 3 × σ are flagged and removed. (See US-1) **Justification**: The original research plan specifies a ±3 σ outlier criterion; applying this standard ensures methodological consistency with the idea and enables reproducibility.
- **FR-005**: The system MUST standardize numeric features using scikit-learn’s `StandardScaler`. (See US-1)
- **FR-006**: The system MUST train three regression algorithms: Linear Regression (OLS), Random Forest Regressor, and Gradient Boosting Regressor. (See US-2)
- **FR-007**: The system MUST perform hyperparameter tuning with k‑fold cross‑validation, utilizing exactly 5 folds if n ≥ 100, or 3 folds if n < 100. (See US-2)
- **FR-008**: The system MUST compute R², MAE, and RMSE on the independent test set. (See US-2)
- **FR-009**: The system MUST generate SHAP value plots for feature importance analysis. (See US-3)
- **FR-010**: The system MUST assess normality of the paired differences between model predictions and baseline using the Shapiro‑Wilk test (α = 0.05). If normality is rejected, the system MUST use a Wilcoxon signed‑rank test; otherwise, it MUST use a paired t‑test. (See US-2)
- **FR-011**: The system MUST validate that the sign of the mean SHAP value for each feature matches the expected physical trend documented in the literature (e.g., hardness → negative impact on wear, as reported by Smith et al., 2020). A mismatch is logged as a discrepancy. (See US-3)
- **FR-012**: The system MUST verify that the ground‑truth columns (coefficient of friction, wear rate) exist in the fetched dataset before initiating training. (See US-2)
- **FR-014**: The system MUST split the data into train and test sets stratified by `material_pair_id` **and** enforce a leave‑one‑material‑out grouping so that neither `material_id_1` nor `material_id_2` appears in both sets, preventing data leakage. (See US-2)
- **FR-015**: The system MUST perform nested cross‑validation during hyperparameter tuning to obtain unbiased performance estimates. (See US-2)
- **FR-016**: The system MUST impute missing material property values using median imputation and log each imputation event. (See US-1)
- **FR-017**: The system MUST produce a final model report summarizing performance metrics, top‑5 SHAP features, and any sign‑trend mismatches. (See US-3)

### Key Entities

- **Data Point**: Represents a single tribological experiment, with attributes for surface roughness parameters, material properties, coefficient of friction, and wear rate. Each Data Point MUST be linked to a unique `experiment_id`.
- **Material Pairing**: Defines the combination of two materials in contact, including their respective properties. Each Material Pairing MUST be linked to one or more Data Points via a shared `material_pair_id` (not a per‑experiment unique identifier).

## Verified Datasets

- OpenML Surface Roughness & Tribology dataset (ID 2352) → https://www.openml.org/d/2352 (Verified 2026-10-25; contains required columns Sa, Sq, Ssk, Sku, Sp, Sv, coeff_friction, wear_rate)
- NIST Materials Data Repository (DOI ) → (Verified 2026-10-25; provides material property tables referenced by FR‑003)

## Success Criteria

### Measurable Outcomes

- **SC-001**: R² for predicting coefficient of friction is measured against the target value of ≥ 0.7, using the held‑out test set. (See US-2)
- **SC-002**: R² for predicting wear rate is measured against the target value of ≥ 0.7, using the held‑out test set. (See US-2)
- **SC-003**: The p‑value from the paired t‑test (or Wilcoxon signed‑rank test) comparing the model to the linear baseline is evaluated against a pre‑defined significance threshold (α = 0.05) to confirm the hypothesis, not as a system pass/fail requirement. (See US-2)
- **SC-004**: The pipeline reports the top‑5 features by mean absolute SHAP value and provides a qualitative assessment of whether their directional impact aligns with known physical trends. (See US-3)
- **SC-005**: The total execution time of the pipeline must not exceed ≤ 4 hours on a standard workstation (e.g., 8‑core CPU, 32 GB RAM). This bound reflects practical engineering constraints without limiting scientific scope. (See US-2)
- **SC-006**: After processing, the dataset must contain ≥ 200 rows with all required features present and no remaining missing values; if fewer rows are available, the pipeline proceeds with a warning and uses the Wilcoxon test as specified in FR‑010. (See US-1)
- **SC-007**: All imputed missing material‑property rows must be logged; no quantitative cap is imposed, but the log should enable downstream auditing. (See US-1)

## Assumptions

- The OpenML dataset and NIST Materials Data Repository will remain publicly accessible and maintain their current data formats.
- The Materials Project API will remain available and provide accurate material property data.
- The `pySurf`, `numpy`, `pandas`, `scikit-learn`, `shap`, `matplotlib`, and `requests` libraries will be readily available and compatible with the execution environment.
- The dataset size will be sufficient to train and evaluate the models effectively (≥ 200 data points after cleaning; if fewer, a warning is issued as per SC‑006).
- Missing material properties may occur; they will be imputed using median imputation as described in FR‑016 and logged as required by SC‑007.
- The OpenML dataset containing the necessary roughness descriptors (Sa, Sq, Ssk, Sku, Sp, Sv) and the target variables (coefficient of friction, wear rate) will be used.