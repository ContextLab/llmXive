# Feature Specification: Predicting the Impact of Alloying on Creep Resistance via Public Data

**Feature Branch**: `001-predicting-impact-of-alloying-on-creep-resistance`  
**Created**: 2026-06-29  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Alloying on Creep Resistance via Public Data"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

A researcher needs to automatically download the NIMS Creep Data Center dataset, retrieve thermodynamic properties from the Materials Project API for each alloy, and generate a clean, processed CSV containing elemental fractions and derived thermodynamic descriptors (mixing enthalpy, atomic radius mismatch) ready for modeling. If NIMS and Materials Project are unreachable, the system MUST generate a synthetic dataset matching the defined schema to ensure pipeline executability.

**Why this priority**: Without a reliable, reproducible data pipeline that correctly merges experimental creep data with computational thermodynamic descriptors, no analysis can be performed. This is the foundational step for all subsequent modeling and validation.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying:
1. Pre-flight checks confirm NIMS URL returns HTTP 200 and Materials Project API key returns valid metadata.
2. If external sources fail, the system generates a synthetic dataset with the schema defined in FR-008.
3. The output CSV contains non-null values for all required columns (rupture time, temperature, stress, elemental fractions, mixing enthalpy).
4. The row count is ≥ 95% of the count of unique valid entries (after duplicate averaging) in the raw source data **that possess valid thermodynamic data**.
5. **Crucially**: The system logs the count of entries excluded due to missing thermodynamic data, confirming they are removed from the final dataset used for modeling **for both the thermodynamic and composition-only models**.

**Acceptance Scenarios**:

1. **Given** a valid NIMS dataset URL and Materials Project API key, **When** the pipeline script is executed, **Then** a processed CSV file is generated, and the system reports the percentage of original rows retained after removing entries with missing temperature, stress, rupture time, OR missing thermodynamic data from Materials Project.
2. **Given** a raw alloy composition string (e.g., "Ni-10Cr-5Al"), **When** the preprocessing module parses it, **Then** it normalizes the composition by sorting elements alphabetically, rounding stoichiometry to 2 decimal places, converting weight% to atomic% if necessary, and correctly calculates the atomic fraction for each element and computes the mixing enthalpy using pymatgen.
3. **Given** an entry with missing thermodynamic data from the Materials Project API, **When** the pipeline encounters it, **Then** the entry is EXCLUDED from the final dataset used for **BOTH the thermodynamic model and the composition-only baseline**, and a log entry is recorded with the specific missing variable.

---

### User Story 2 - Comparative Model Training and Evaluation (Priority: P2)

A materials scientist needs to train a Gradient Boosting Regressor using thermodynamic descriptors and compare its performance against a baseline Gradient Boosting Regressor using only raw elemental weight percentages, obtaining out-of-sample R² scores and RMSE values for both. The evaluation uses Nested Cross-Validation with a specific statistical test to handle small sample sizes.

**Why this priority**: This directly addresses the core research question of whether thermodynamic descriptors provide a predictive advantage over raw composition. The comparison is the primary mechanism for quantifying the "predictive ceiling" of composition-only models, now isolated from model architecture differences.

**Independent Test**: Can be fully tested by running the training script and verifying that two distinct Gradient Boosting models are trained using Nested Cross-Validation (outer loop: 10-fold if N≥50, Repeated 5-fold if N<50; inner loop: hyperparameter tuning), and a results table is printed showing R² and RMSE for both models along with the appropriate statistical test result. **The test MUST assert that the input dataframes for both models have identical row counts and indices before training begins, confirming they are drawn from the intersection of valid thermodynamic data.**

**Acceptance Scenarios**:

1. **Given** the processed dataset, **When** the model training script is executed, **Then** a Gradient Boosting Regressor is trained on the thermodynamic feature set and a separate Gradient Boosting Regressor is trained on the composition-only feature set, using Nested Cross-Validation for hyperparameter tuning. **Both models MUST be trained on the exact same subset of data (the intersection of available composition and thermodynamic data).**
2. **Given** the trained models, **When** the outer loop cross-validation is performed, **Then** the system outputs the mean R² and RMSE for each fold, ensuring stratification is applied using **rupture time quantiles** (if N≥50) or Repeated 5-fold (if N<50).
3. **Given** the cross-validation results, **When** the statistical significance test is executed, **Then** a result is calculated and printed: if N≥20, a Corrected Resampled t-test p-value is reported; if N<20, a Bootstrap 95% Confidence Interval for the difference is reported.

---

### User Story 3 - Feature Importance Analysis and Reporting (Priority: P3)

A domain expert needs to visualize the relative importance of specific alloying elements (e.g., Ta, Mo, W) and thermodynamic descriptors (e.g., mixing enthalpy) in predicting creep resistance using SHAP (SHapley Additive exPlanations) plots to interpret the model's decisions.

**Why this priority**: While the model performance (US-02) answers "if" descriptors help, this story answers "which" descriptors matter most. This interpretability is crucial for generating new material hypotheses and understanding the physical drivers of creep resistance.

**Independent Test**: Can be fully tested by generating SHAP summary plots and verifying that the analysis is performed, the top 5 features are extracted and reported, and the plot is saved as a PNG file.

**Acceptance Scenarios**:

1. **Given** a trained Gradient Boosting model, **When** the SHAP analysis script is run, **Then** a summary plot is generated showing the mean absolute SHAP value for each feature, ordered by importance.
2. **Given** the SHAP values, **When** the top 5 features are extracted, **Then** the system reports the list of the top 5 features and their corresponding SHAP values, regardless of whether they are derived thermodynamic properties or elemental fractions.
3. **Given** the analysis results, **When** the final report is generated, **Then** it includes a text summary stating the top 3 predictors and their direction of influence (positive or negative correlation with rupture time).

---

### Edge Cases

- What happens when the Materials Project API rate limits are hit during batch retrieval of thermodynamic properties? (System must implement exponential backoff and retry up to 3 times before failing the specific entry).
- How does the system handle alloys with compositions that do not exist in the Materials Project database? (The entry is logged as "unresolved thermodynamic data" and **excluded from the final dataset used for BOTH models**).
- What happens if the dataset contains duplicate entries with conflicting rupture times for the same alloy under identical conditions? (The system MUST automatically average the rupture times for the duplicate entries. This averaging is the mandatory behavior for the automated pipeline; the resulting row count will reflect this deterministic reduction, and the Independent Test in US-01 must account for this deterministic reduction).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the NIMS Creep Data Center dataset and parse it into a structured format, removing entries with missing critical variables (temperature, stress, rupture time). If NIMS and Materials Project are unreachable, the system MUST generate a synthetic dataset matching the schema defined in FR-008. (See US-01)
- **FR-002**: System MUST retrieve thermodynamic properties (mixing enthalpy, atomic radius mismatch) for each unique alloy composition from the Materials Project API using `pymatgen`. Unique composition keys MUST be generated by normalizing raw strings: sorting elements alphabetically, rounding stoichiometry to 2 decimals, and converting weight% to atomic% if necessary. **Entries with missing thermodynamic data MUST be EXCLUDED from the final dataset used for BOTH the thermodynamic model and the composition-only baseline.** This ensures both models train on the exact same subset of data (the intersection of available composition and thermodynamic data), eliminating selection bias. (See US-01)
- **FR-003**: System MUST compute derived features including average atomic radius, mixing enthalpy, and solid-solution strengthening estimates based on elemental fractions. (See US-01)
- **FR-004**: System MUST train a Gradient Boosting Regressor on the full thermodynamic feature set and a separate Gradient Boosting Regressor on the composition-only feature set, performing Nested Cross-Validation. **Both models MUST be trained on the exact same subset of data (the intersection of entries with valid thermodynamic data).** The outer loop MUST use 10-fold stratification by **rupture time quantiles** if N ≥ 50, or Repeated 5-fold (5 repeats) if N < 50. No separate hold-out test set is used due to the small dataset size. (See US-02)
- **FR-005**: System MUST perform a statistical significance test on the cross-validation RMSE scores of the two models. If N ≥ 20, the system MUST use the Corrected Resampled t-test (Nadeau & Bengio correction) to account for overlapping folds. If N < 20, the system MUST use Bootstrap confidence intervals (95%) and report no p-value. **This test is valid only because both models are evaluated on identical data splits (the intersection of valid thermodynamic data).** (See US-02)
- **FR-006**: System MUST generate SHAP (SHapley Additive exPlanations) plots to visualize and rank feature importance for the Gradient Boosting model. (See US-03)
- **FR-007**: System MUST implement Nested Cross-Validation (inner loop for hyperparameter tuning, outer loop for performance estimation) to mitigate overfitting risks given the expected small dataset size (n < 100). The outer loop strategy is defined in FR-004. (See US-02)
- **FR-008**: System MUST support a synthetic dataset generation mode. If external data sources fail, the system MUST generate a dataset with the following schema: `alloy_id` (string), `composition_str` (string), `temperature` (float), `stress` (float), `rupture_time` (float), `mixing_enthalpy` (float), `radius_mismatch` (float). The values MUST be sampled from distributions approximating the NIMS dataset statistics (mean/SD of known public data). (See US-01)

### Key Entities

- **AlloySample**: Represents a single experimental data point containing elemental composition, processing conditions (temperature, stress), and the observed rupture time.
- **ThermodynamicDescriptor**: Represents calculated physical properties (e.g., mixing enthalpy, atomic radius mismatch) derived from the alloy's composition.
- **ModelPerformance**: Represents the statistical metrics (R², RMSE, p-value or CI) resulting from the comparison between the thermodynamic and composition-only models.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The out-of-sample R² of the thermodynamic descriptor model is measured against the composition-only baseline model. A gain is considered successful if the R² improvement is ≥ 0.05; otherwise, the delta is reported as negligible. **This threshold is a hypothesis-driven reporting metric; the primary arbiter of significance is the statistical test in SC-002.** (See US-02)
- **SC-002**: The statistical significance of the performance difference between the two models is measured via the Corrected Resampled t-test (if N≥20) or Bootstrap 95% CI (if N<20) on Nested Cross-Validation RMSE scores. (See US-02)
- **SC-003**: The predictive contribution of specific alloying elements and thermodynamic descriptors is measured using SHAP values to identify the top 5 governing factors. (See US-03)
- **SC-004**: The data pipeline success rate is measured as the percentage of original dataset entries successfully processed and merged with thermodynamic data (or successfully generated in synthetic mode). (See US-01)
- **SC-005**: The computational feasibility is measured by ensuring the entire workflow (download, preprocess, train, evaluate) completes within 6 hours (GitHub Actions free tier limit). (See Assumptions)

## Assumptions

- The NIMS Creep Data Center dataset is publicly accessible and provides a sufficient number of entries (n < 100 **total raw entries**) to train and evaluate the machine learning models, requiring robust overfitting mitigation.
- The Materials Project API provides thermodynamic data for the majority of alloys in the NIMS dataset; entries without matching data are **excluded from the final dataset used for BOTH models** to ensure a fair comparison and isolate the feature effect.
- The Gradient Boosting Regressor is computationally tractable on a CPU-only environment with limited RAM., given the dataset size is limited to the public NIMS release.
- The relationship between thermodynamic descriptors and creep resistance is primarily associational; the models do not claim causal inference due to the observational nature of the dataset.
- The SHAP library is compatible with the scikit-learn Gradient Boosting implementation and can be computed within the runner time limit for the given dataset size.
- The "composition-only" baseline is defined strictly as using raw elemental weight percentages without any derived physics-based features, but using the *same* Gradient Boosting architecture as the thermodynamic model to isolate feature effects.
- Derived thermodynamic features (mixing enthalpy, radius mismatch) act as a non-linear feature transform of the raw elemental fractions. The hypothesis is that these transforms capture complex interactions more effectively than raw linear combinations, even though they are derived from the same source data.
- Nested Cross-Validation is required to provide an unbiased performance estimate given the small dataset size (n < 100) and the risk of overfitting with non-linear models.
- **Statistical Test Selection**: The Corrected Resampled t-test (Nadeau & Bengio) is used for N ≥ 20. **This is the exclusive test referenced; no other t-test variants apply.** If N < 20, only Bootstrap 95% CI are reported, and the study is considered exploratory.
- **Stratification Strategy**: If N ≥ 50, 10-fold stratification by **rupture time quantiles** is used to ensure representative distribution of the response variable. If N < 50, Repeated 5-fold (5 repeats) is used to ensure sufficient samples per fold.
- **Small Data Regime**: If N < 20, the study is exploratory; only Bootstrap 95% CI are reported, and no p-values are calculated.
- **Fair Comparison Constraint**: Both the Thermodynamic and Composition-Only models are trained on the **exact same subset of data** (the intersection of available composition and thermodynamic data) to isolate the feature effect and avoid selection bias.