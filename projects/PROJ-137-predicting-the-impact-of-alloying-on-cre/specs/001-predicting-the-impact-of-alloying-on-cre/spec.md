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
4. **Real Data Path**: The row count is ≥ 95% of the count of rows in the raw NIMS CSV where temperature, stress, and rupture_time are non-null. **Synthetic Path**: The row count equals the number of requested synthetic records (high success rate).
5. **Crucially**: The system logs the count of entries excluded due to missing thermodynamic data, confirming they are removed from the final dataset used for modeling **for both the thermodynamic and composition-only models**.
6. **Duplicate Handling**: Given a raw dataset with duplicate entries for the same alloy/conditions, When the pipeline runs, Then the output CSV contains exactly one row for that alloy/conditions with the averaged rupture time, and the log confirms the averaging event.
7. **Schema Validation**: The output CSV MUST validate against the schema defined in `data-model.md` (specifically `dataset.schema.yaml`).

**Acceptance Scenarios**:

1. **Given** a valid NIMS dataset URL and Materials Project API key, **When** the pipeline script is executed, **Then** a processed CSV file is generated, and the system reports the percentage of original rows retained after removing entries with missing temperature, stress, rupture time, OR missing thermodynamic data from Materials Project.
2. **Given** a raw alloy composition string (e.g., "Ni-10Cr-5Al"), **When** the preprocessing module parses it, **Then** it normalizes the composition by sorting elements alphabetically, rounding stoichiometry to 2 decimal places, converting weight% to atomic% if necessary, and correctly calculates the atomic fraction for each element and computes the mixing enthalpy using pymatgen.
3. **Given** an entry with missing thermodynamic data from the Materials Project API, **When** the pipeline encounters it, **Then** the entry is EXCLUDED from the final dataset used for **BOTH the thermodynamic model and the composition-only baseline**, and a log entry is recorded with the specific missing variable.

---

### User Story 2 - Comparative Model Training and Evaluation (Priority: P2)

A materials scientist needs to train a Gradient Boosting Regressor using thermodynamic descriptors and compare its performance against a baseline Gradient Boosting Regressor using only raw elemental weight percentages, obtaining out-of-sample R² scores and RMSE values for both. The evaluation uses Nested Cross-Validation with a specific statistical test to handle small sample sizes. **The study explicitly validates the *methodology's ability to detect known physical signals* (in synthetic data) rather than claiming predictive power on real alloys until verified data is available.**

**Why this priority**: This directly addresses the core research question of whether thermodynamic descriptors provide a predictive advantage over raw composition. The comparison is the primary mechanism for quantifying the "predictive ceiling" of composition-only models, now isolated from model architecture differences. The study design distinguishes between **Methodology Validation** (synthetic data) and **Scientific Discovery** (real data).

**Independent Test**: Can be fully tested by running the training script and verifying that two distinct Gradient Boosting models are trained using Nested Cross-Validation (outer loop: 10-fold if N≥50, Repeated 5-fold if N<50; inner loop: hyperparameter tuning), and a results table is printed showing R² and RMSE for both models along with the appropriate statistical test result. **The test MUST assert that the input dataframes for both models have identical row counts and indices before training begins, confirming they are drawn from the intersection of valid thermodynamic data.** Additionally, the test must verify that excluded rows are logged with the specific missing variable. **The test must also verify that the outer loop uses stratification by temperature range (if N≥50) to prevent leakage.**

**Acceptance Scenarios**:

1. **Given** the processed dataset, **When** the model training script is executed, **Then** a Gradient Boosting Regressor is trained on the thermodynamic feature set and a separate Gradient Boosting Regressor is trained on the composition-only feature set, using Nested Cross-Validation for hyperparameter tuning. **Both models MUST be trained on the exact same subset of data (the intersection of available composition and thermodynamic data).**
2. **Given** the trained models, **When** the outer loop cross-validation is performed, **Then** the system outputs the mean R² and RMSE for each fold, ensuring stratification is applied using **temperature range** (if N≥50) or Repeated 5-fold (if N<50).
3. **Given** the cross-validation results, **When** the statistical significance test is executed, **Then** a result is calculated and printed: Bootstrap 95% Confidence Interval for the difference is reported for all N < 100. **For 20 ≤ N < 100, a Corrected Resampled t-test (Nadeau & Bengio) is also performed, accompanied by a sensitivity analysis sweeping the cutoff over {, 0.05, 0.1} to assess robustness.**

---

### User Story 3 - Feature Importance Analysis and Reporting (Priority: P3)

A domain expert needs to visualize the relative importance of specific alloying elements (e.g., Ta, Mo, W) and thermodynamic descriptors (e.g., mixing enthalpy) in predicting creep resistance using SHAP (SHapley Additive exPlanations) plots to interpret the model's decisions.

**Why this priority**: While the model performance (US-02) answers "if" descriptors help, this story answers "which" descriptors matter most. This interpretability is crucial for generating new material hypotheses and understanding the physical drivers of creep resistance.

**Independent Test**: Can be fully tested by generating SHAP summary plots and verifying that the analysis is performed, the top 5 features are extracted and reported, and the plot is saved as a PNG file.

**Acceptance Scenarios**:

1. **Given** a trained Gradient Boosting model, **When** the SHAP analysis script is run, **Then** a summary plot is generated showing the mean absolute SHAP value for each feature, ordered by importance.
2. **Given** the SHAP values, **When** the top 5 features are extracted, **Then** the system reports the list of the top 5 features and their corresponding SHAP values, regardless of whether they are derived thermodynamic properties or elemental fractions.
3. **Given** the analysis results, **When** the final report is generated, **Then** it includes a text summary stating the top 3 predictors and their direction of influence in the format: "feature_name: +value" or "feature_name: positive correlation".

---

### Edge Cases

- What happens when the Materials Project API rate limits are hit during batch retrieval of thermodynamic properties? (System must implement exponential backoff and retry up to 3 times before failing the specific entry).
- How does the system handle alloys with compositions that do not exist in the Materials Project database? (The entry is logged as "unresolved thermodynamic data" and **excluded from the final dataset used for BOTH models**).
- What happens if the dataset contains duplicate entries with conflicting rupture times for the same alloy under identical conditions? (The system MUST automatically average the rupture times for the duplicate entries. This averaging is the mandatory behavior for the automated pipeline; the resulting row count will reflect this deterministic reduction, and the Independent Test in US-01 must account for this deterministic reduction. **Rule**: If a duplicate entry has one valid and one invalid record, the system averages the valid records and excludes the invalid one, provided at least one valid record exists.)

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the NIMS Creep Data Center dataset and parse it into a structured format, removing entries with missing critical variables (temperature, stress, rupture time). If NIMS and Materials Project are unreachable, the system MUST generate a synthetic dataset matching the schema defined in FR-008. **The output MUST validate against the schema defined in `data-model.md` (specifically `dataset.schema.yaml`).** (See US-01)
- **FR-002**: System MUST retrieve thermodynamic properties (mixing enthalpy, atomic radius mismatch) for each unique alloy composition from the Materials Project API using `pymatgen`. Unique composition keys MUST be generated by normalizing raw strings: sorting elements alphabetically, rounding stoichiometry to 2 decimals, and converting weight% to atomic% if necessary. **Entries with missing thermodynamic data MUST be EXCLUDED from the final dataset used for BOTH the thermodynamic model and the composition-only baseline.** "Missing" is defined as a 404 error, a null value in the response, or a timeout > 30s. This ensures both models train on the exact same subset of data (the intersection of available composition and thermodynamic data), eliminating selection bias. *Note: This design intentionally restricts the baseline to the intersection to isolate the feature effect of thermodynamic descriptors by controlling for data availability bias.* (See US-01)
- **FR-003**: System MUST compute derived features including average atomic radius, mixing enthalpy, and solid-solution strengthening estimates based on elemental fractions. (See US-01)
- **FR-004**: System MUST train a Gradient Boosting Regressor on the full thermodynamic feature set and a separate Gradient Boosting Regressor on the composition-only feature set, performing Nested Cross-Validation. **Both models MUST be trained on the exact same subset of data (the intersection of entries with valid thermodynamic data).** The outer loop MUST use 10-fold stratification by **temperature range** if N ≥ 50, or Repeated 5-fold (5 repeats) if N < 50. No separate hold-out test set is used due to the small dataset size. *Note: This design intentionally restricts the baseline to the intersection to isolate the feature effect of thermodynamic descriptors by controlling for data availability bias.* **The stratification by temperature range is a mandatory constraint to satisfy Constitution Principle VII (Microstructure-Agnostic Scope) and prevent leakage.** (See US-02)
- **FR-005**: System MUST perform a statistical significance test on the cross-validation RMSE scores of the two models. **Anchored to US-02.** The system MUST use Bootstrap 95% Confidence Intervals for all N < 20. For 20 ≤ N < 100, the system MUST use the Corrected Resampled t-test (Nadeau & Bengio) **AND** perform a sensitivity analysis sweeping the cutoff over {0.01, 0.05, 0.1} to assess robustness. **The system MUST output the calculated CI bounds, the t-test p-value (if applicable), and the sensitivity analysis results to a standard output or log file.** *Note: Statistical significance on synthetic data validates the methodology's ability to detect the injected signal, not physical reality on real alloys. The improvement measured is the benefit of explicit feature engineering for the specific algorithm, not independent physical information.* (See US-02)
- **FR-006**: System MUST generate SHAP (SHapley Additive exPlanations) plots to visualize and rank feature importance for the Gradient Boosting model. (See US-03)
- **FR-007**: System MUST implement Nested Cross-Validation (inner loop for hyperparameter tuning, outer loop for performance estimation) to mitigate overfitting risks given the expected small dataset size (n < 100). This requirement explicitly serves US-02's 'Nested Cross-Validation' test case. (See US-02)
- **FR-008**: System MUST support a synthetic dataset generation mode. If external data sources fail, the system MUST generate a dataset with the following schema: `alloy_id` (string), `composition_str` (string), `temperature` (float), `stress` (float), `rupture_time` (float), `mixing_enthalpy` (float), `radius_mismatch` (float). The values MUST be sampled from distributions defined in `config/synthetic_params.yaml`. The generator MUST encode non-linear physical laws:
  - Arrhenius dependence: `log(t) = A + B/T`
  - Power-law stress: `t = C * sigma^-n`
  - Parameters (A, B, C, n) MUST be loaded from the config file.
  **The system MUST perform a Physics Consistency Check: Verify that a physics-based model trained on the synthetic set achieves R² > 0.8 before proceeding to main training.**
  **Statistical Target Constraints**: The synthetic data MUST satisfy the following statistical targets to be considered valid:
 - The mean and standard deviation of `rupture_time` must be within **[deferred]** of the mean/SD of the target NIMS dataset (or the values defined in `config/synthetic_params.yaml` if NIMS is unavailable).
  - The composition distributions must match the target NIMS histograms (or `config/synthetic_params.yaml` targets) within a **Kolmogorov-Smirnov distance of 0.05**.
  - If these targets are not met, the system MUST raise an error and halt execution.
  (See US-01)

### Key Entities

- **AlloySample**: Represents a single experimental data point containing elemental composition, processing conditions (temperature, stress), and the observed rupture time.
- **ThermodynamicDescriptor**: Represents calculated physical properties (e.g., mixing enthalpy, atomic radius mismatch) derived from the alloy's composition.
- **ModelPerformance**: Represents the statistical metrics (R², RMSE, CI) resulting from the comparison between the thermodynamic and composition-only models.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system outputs the R² delta and Bootstrap 95% CI for the comparison between the thermodynamic descriptor model and the composition-only baseline model. **Success is defined as the execution and reporting of this comparison, regardless of the delta value.** (See US-02)
- **SC-002**: The statistical significance of the performance difference between the two models is measured via Bootstrap 95% CI on Nested Cross-Validation RMSE scores. **The choice of method (Bootstrap for N < 20, Corrected Resampled t-test for 20 ≤ N < 100) is a measured outcome determined by the sample size N.** (See US-02)
- **SC-003**: The predictive contribution of specific alloying elements and thermodynamic descriptors is measured using SHAP values to identify the top 5 governing factors. **The output MUST include the direction of influence in the format: "feature_name: +value" or "feature_name: positive correlation".** (See US-03)
- **SC-004**: The data pipeline success rate is measured as: **If real data is used**, the percentage of original dataset entries successfully processed and merged with thermodynamic data; **if synthetic data is used**, the success rate is [deferred] of generated records. (See US-01)
- **SC-005**: The computational feasibility is measured by ensuring the system logs the total execution time. (See Assumptions)
- **SC-006**: The data pipeline success rate includes a mandatory metric: **The percentage of original rows retained** and **The count of entries excluded due to missing thermodynamic data** must be explicitly logged and reported as a measured outcome. (See US-01)
- **SC-007**: The synthetic data generation is validated by the **Physics Consistency Check**: A physics-based model trained on the synthetic set MUST achieve R² > 0.8. (See US-01)
- **SC-008**: The synthetic data generation is validated by statistical targets: **Mean/SD of rupture time within 10%** and **KS distance of composition distributions ≤ 0.05**. (See US-01)

## Assumptions

- The NIMS Creep Data Center dataset is **unverified** and the NIMS URL is NOT in the verified list. **The primary execution path is Synthetic Data Generation**, with real data retrieval as a secondary path if the URL becomes verified.
- The Materials Project API provides thermodynamic data for the majority of alloys in the NIMS dataset; entries without matching data are **excluded from the final dataset used for BOTH models** to ensure a fair comparison and isolate the feature effect.
- The Gradient Boosting Regressor is computationally tractable on a CPU-only environment with limited RAM., given the dataset size is limited to the public NIMS release.
- The relationship between thermodynamic descriptors and creep resistance is primarily associational; the models do not claim causal inference due to the observational nature of the dataset.
- The SHAP library is compatible with the scikit-learn Gradient Boosting implementation and can be computed within the runner time limit for the given dataset size.
- The "composition-only" baseline is defined strictly as using raw elemental weight percentages without any derived physics-based features, but using the *same* Gradient Boosting architecture as the thermodynamic model to isolate feature effects.
- Derived thermodynamic features (mixing enthalpy, radius mismatch) act as a non-linear feature transform of the raw elemental fractions. The hypothesis is that these transforms capture complex interactions more effectively than raw linear combinations, even though they are derived from the same source data. **The study tests the utility of explicit feature engineering for model convergence, not the independence of the physical information.**
- Nested Cross-Validation is required to provide an unbiased performance estimate given the small dataset size (n < 100) and the risk of overfitting with non-linear models.
- **Statistical Test Selection**: Bootstrap 95% CI is used for all N < 20. For 20 ≤ N < 100, the Corrected Resampled t-test (Nadeau & Bengio) is used, accompanied by a sensitivity analysis. **This is the exclusive test referenced; no other t-test variants apply.**
- **Stratification Strategy**: If N ≥ 50, 10-fold stratification by **temperature range** is used to ensure representative distribution of the response variable and prevent leakage (Constitution Principle VII). If N < 50, Repeated 5-fold (5 repeats) is used to ensure sufficient samples per fold.
- **Small Data Regime**: If N < 20, the study is exploratory; only Bootstrap 95% CI are reported, and no p-values are calculated.
- **Fair Comparison Constraint**: Both the Thermodynamic and Composition-Only models are trained on the **exact same subset of data** (the intersection of available composition and thermodynamic data) to isolate the feature effect and avoid selection bias.
- **Low Power Acknowledgement**: With N < 100, the statistical power to detect a specific R² improvement is low. The study goal is to **explore the methodology** and validate the **pipeline's ability to detect injected signals** in synthetic data, rather than claiming definitive results on real alloys.
- **Synthetic Data Validity**: Synthetic data is generated using physical laws (Arrhenius, Power-law) to ensure the "Thermodynamic" model has a signal to learn. The study explicitly validates this signal via the Physics Consistency Check (R² > 0.8) before proceeding. **The synthetic data is the primary execution path due to the unverified status of the NIMS source.**
- **Methodology vs. Science**: The study on synthetic data validates the *methodology's ability to detect known physical signals* (in synthetic data) rather than claiming predictive power on real alloys until verified data is available. The research question is explicitly re-framed to "Does the pipeline correctly detect known physical laws when they are present?"