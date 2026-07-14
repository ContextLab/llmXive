# Feature Specification: Predicting Corrosion Potential from Composition and Environment

**Feature Branch**: `001-predict-corrosion-potential`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Corrosion Potential from Composition and Environment via Public Databases"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

**Description**: As a materials researcher, I want to automatically download alloy composition and corrosion records from the NIST Corrosion Database (NIST-IR), then preprocess them into a unified, clean dataset by filtering for records with complete environmental metadata, so that I have a reliable foundation for training predictive models without manual data wrangling.

**Why this priority**: This is the foundational step; without a clean, verified dataset containing the joint distribution of composition, environment, and corrosion, no modeling or analysis can occur. It directly addresses the "verified dataset" gap identified in the literature review.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output CSV/Parquet file contains non-null values for composition, environment (pH, temperature), and corrosion potential, with no duplicate alloy entries.

**Acceptance Scenarios**:

1. **Given** valid access to the NIST Corrosion Database (NIST-IR-8200), **When** the ingestion script runs, **Then** a unified dataset is produced containing at least 500 records with elemental weight fractions, environmental metadata, and corrosion potential. If the dataset is < 500 records, the system MUST halt execution and report the exact count of available records, rather than triggering a scope reduction or falling back to synthetic data.
2. **Given** a record with missing environmental pH, **When** the preprocessing step runs, **Then** the record is EXCLUDED from the primary regression analysis and logged in a diagnostic report, rather than being imputed or causing a pipeline crash.
3. **Given** the dataset is split, **When** the split occurs, **Then** the system performs a Group Split (Leave-One-Specific-Alloy-Out) where exactly one Specific Alloy Designation (e.g., SS304) is assigned to the test set and the remainder to the training set, ensuring no specific alloy designation appears in both sets to prevent data leakage. This strategy requires a minimum of 10 specific alloy designations in the dataset to be valid.

---

### User Story 2 - Model Training and Evaluation (Priority: P2)

**Description**: As a data scientist, I want to train Random Forest and Gradient Boosting regressors on the preprocessed dataset to predict corrosion potential, so that I can quantify the relationship between composition/environment and corrosion with a measurable performance metric.

**Why this priority**: This delivers the core predictive capability. It moves from raw data to actionable insight, directly addressing the research question about interaction effects.

**Independent Test**: Can be fully tested by running the training script on the split data and verifying that both models output an R² score and RMSE on the held-out test set.

**Acceptance Scenarios**:

1. **Given** the training set is loaded, **When** the Random Forest model is trained, **Then** the model completes within 30 minutes on a GitHub Actions `ubuntu-latest` runner environment.
2. **Given** the trained models, **When** evaluated on the test set, **Then** the system reports the R² score and RMSE for both algorithms.
3. **Given** the evaluation results, **When** the primary model (highest R²) is selected, **Then** the system outputs the prediction error (RMSE) in millivolts (mV) and compares it against the null baseline (mean prediction). The system MUST classify the result as "learnable" if R² > 0.0 with p < 0.05 (via permutation test), otherwise "null", and report this classification.

---

### User Story 3 - Interpretability and Feature Importance Analysis (Priority: P3)

**Description**: As a domain expert, I want to view permutation importance scores and partial dependence plots for key alloying elements and environmental factors, so that I can understand which specific components drive corrosion reduction and how they interact non-linearly.

**Why this priority**: This transforms the "black box" model into a scientific tool, addressing the need to "identify key alloying elements" and "visualize non-linear interactions" as stated in the expected results.

**Independent Test**: Can be fully tested by generating the importance report and plots; the test verifies that the top 3 features are listed and that partial dependence curves are generated for at least one element-environment pair.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** permutation importance is calculated, **Then** the system ranks features by contribution and outputs the top 5 with significance p-values < 0.05, determined via a one-sample permutation test against a null distribution of zero importance, with 1,000 permutations and Bonferroni or FDR correction applied for multiple comparisons.
2. **Given** two interacting variables (e.g., Chromium content and pH), **When** the partial dependence plot is generated, **Then** the plot clearly visualizes the non-linear interaction effect on corrosion potential.
3. **Given** the analysis is complete, **When** the results are compiled, **Then** a summary report is generated stating whether specific elements consistently reduce corrosion potential across the tested environments.

### Edge Cases

- **What happens when the NIST API returns a 429 (Too Many Requests) error?** The system MUST implement a retry mechanism with exponential backoff (a limited number of retries, base delay of a short interval, max delay of approximately one minute) and log the failure.
- **How does the system handle a corrosion record where the environmental pH is outside the standard aqueous range (e.g., > 14.0 or < 0.0)?** The record MUST be flagged as an outlier and excluded from the primary regression analysis, but included in a separate "extreme condition" diagnostic report. The standard aqueous range is defined as the full spectrum of the pH scale.
- **What happens if the dataset size is too small to support a meaningful train/test split (e.g., < 10 specific alloy designations)?** The system MUST halt execution and raise a `DataInsufficientError` with a message suggesting data augmentation or a different data source.
- **Definition of Specific Alloy Designation**: For the purpose of splitting, a "Specific Alloy Designation" is defined by the unique alloy grade (e.g., "SS304", "SS316", "Inconel625"). This definition ensures disjoint sets for the Group Split.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download alloy composition and corrosion data from the NIST Corrosion Database (NIST-IR-8200) for specified target metals (Fe, Al, Ni, Ti) and store it locally. (See US-1)
- **FR-002**: System MUST retrieve corrosion potential measurements and elemental weight fractions from the NIST Corrosion Database (NIST-IR-8200) and link them by record ID, ensuring no fuzzy matching is performed between disparate sources. (See US-1)
- **FR-003**: System MUST preprocess the merged dataset by encoding elemental compositions as weight fractions and environmental conditions as categorical or numerical variables. (See US-1)
- **FR-004**: System MUST split the dataset into a Group Split by Specific Alloy Designation (Leave-One-Specific-Alloy-Out) to prevent data leakage, ensuring no specific alloy designation appears in both training and test sets. (See US-1)
- **FR-005**: System MUST train Random Forest and Gradient Boosting regressors using CPU-optimized libraries (e.g., scikit-learn) without GPU acceleration. (See US-2)
- **FR-006**: System MUST evaluate model performance using R² and RMSE on the held-out test set and report these metrics. (See US-2)
- **FR-007**: System MUST perform permutation importance analysis on the best-performing model to quantify feature contributions. (See US-3)
- **FR-008**: System MUST conduct statistical significance testing on feature importance scores using a one-sample permutation test (null hypothesis: importance = 0) with 1,000 permutations, applying Bonferroni or FDR correction for multiple comparisons. (See US-3)
- **FR-009**: System MUST generate partial dependence plots to visualize non-linear interactions between composition and environment. (See US-3)
- **FR-010**: System MUST log all data processing steps and model hyperparameters to a reproducible log file for the GitHub Actions workflow. (See US-1)
- **FR-011**: System MUST perform a schema validation step that verifies every record in the training set contains non-null values for composition, environmental pH, temperature, and corrosion potential before training begins. (See US-1)
- **FR-012**: System MUST implement a clustering or specific-alloy-level splitting strategy (Leave-One-Specific-Alloy-Out) to ensure true generalization to new compositions, rather than relying on base metal families. (See US-1)
- **FR-013**: System MUST exclude records with missing critical environmental variables (pH, temperature) from the primary regression analysis rather than imputing them. (See US-1)
- **FR-014**: System MUST halt the pipeline and report a `SchemaMismatchError` if the NIST Corrosion Database (NIST-IR-8200) does not contain the required joint distribution (Composition + Environment + Corrosion) or if the record count is < 500. (See US-1)

### Key Entities

- **AlloyRecord**: Represents a specific metallic alloy with attributes for elemental weight fractions (Fe, Cr, Ni, etc.) and Specific Alloy Designation (e.g., "SS304").
- **EnvironmentRecord**: Represents the testing conditions with attributes for pH, temperature, and electrolyte type (saline, acidic, etc.).
- **CorrosionMeasurement**: Represents the target variable (corrosion potential in millivolts vs SHE) linked to a specific AlloyRecord and EnvironmentRecord.
- **ModelResult**: Represents the output of the training phase, containing model type, hyperparameters, R² score, and RMSE.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model predictive power (R² score) is measured against the baseline of a null model (mean prediction) to confirm a learnable relationship. (See US-2)
- **SC-002**: Prediction error (RMSE) is measured in millivolts (mV) against a tolerance defined in ASTM G59 standard practice to determine practical utility. (See US-2)
- **SC-003**: Feature importance robustness is measured against statistical significance thresholds (p < 0.05 via one-sample permutation test with 1,000 permutations) to verify that identified drivers are not random noise. (See US-3)
- **SC-004**: Data leakage is measured by checking the overlap of specific_alloy_designation_id between training and test sets; the target is zero overlap. (See US-1)
- **SC-005**: Compute feasibility is measured by ensuring the total execution time on a GitHub Actions `ubuntu-latest` runner is ≤ 6 hours. (See US-2)
- **SC-006**: Data validity is measured by the count of records passing schema validation (non-null composition, pH, temperature, corrosion); the target is ≥ 500 records. (See US-1)
- **SC-007**: Learnable pattern classification is measured by the R² score and p-value; the target is R² > 0.0 with p < 0.05. (See US-2)

## Assumptions

- **Data Availability**: It is assumed that the NIST Corrosion Database (NIST-IR-8200) contains sufficient overlapping records (composition + environment + corrosion potential) to create a dataset of at least 500 unique samples. If the intersection is < 500 samples, the project MUST halt and report the count; no scope reduction or synthetic data fallback is permitted.
- **Dataset-Variable Fit**: It is assumed that the NIST Corrosion Database (NIST-IR-8200) contains explicit numerical pH and temperature values for corrosion records. If a record only contains qualitative descriptions (e.g., "acidic"), the system MUST exclude that record from the primary regression analysis and flag it for the "extreme condition" diagnostic report.
- **Inference Framing**: Since the data is observational (no random assignment of environment), all findings regarding "effects" will be framed as associational correlations, not causal claims.
- **Compute Constraints**: The analysis assumes that Random Forest and Gradient Boosting models on the expected dataset size (≤ 10,000 rows) will run within the limited CPU and RAM constraints of the GitHub Actions free tier without requiring GPU acceleration.
- **Threshold Justification**: The target R² > 0.0 and RMSE ≤ 150 mV are based on typical variability in corrosion potential measurements reported in standard materials science literature (ASTM G59); these are treated as community-standard defaults for reporting.
- **Measurement Validity**: It is assumed that the corrosion potential values in the NIST Corrosion Database (NIST-IR-8200) are derived from standardized electrochemical testing methods (e.g., ASTM G5) and are directly comparable across records.
- **Multiplicity Correction**: When testing multiple feature importances, a Bonferroni correction or False Discovery Rate (FDR) control will be applied to the p-values to account for multiple comparisons.
- **Simulation Mode**: The use of synthetic data or simulation mode for the primary research question is explicitly FORBIDDEN. The pipeline MUST halt if real data is insufficient.