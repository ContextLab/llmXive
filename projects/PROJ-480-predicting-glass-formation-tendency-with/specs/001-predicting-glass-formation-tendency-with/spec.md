# Feature Specification: Predicting Glass Formation Tendency with Machine Learning on Public Data

**Feature Branch**: `001-predict-glass-formation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Glass Formation Tendency with Machine Learning on Public Data"

## User Scenarios & Testing

### User Story 1 - Data Aggregation, Target Detection, and Descriptor Computation (Priority: P1)

The researcher needs to automatically download metallic glass composition data from a verified public repository (Zenodo DOI: 10.5281/zenodo.5778205), detect the available target variable (continuous critical casting thickness $D_c$ or binary glass/crystal label), and compute atomic descriptors (atomic size mismatch, mixing enthalpy, electronegativity) for each composition using `pymatgen` to create a unified, analysis-ready dataset.

**Why this priority**: Without a clean, computed dataset with the correct target variable detected, no modeling or analysis can occur. This is the foundational step that enables all downstream research.

**Independent Test**: Can be fully tested by running the data processing script against a small subset of known compositions and verifying that the output CSV contains the expected columns (composition, detected_target_type, target_value, computed descriptors) with no missing values for the primary predictors.

**Acceptance Scenarios**:

1. **Given** the verified Zenodo dataset URL (DOI: 10.5281/zenodo.5778205), **When** the data ingestion script executes, **Then** it successfully downloads and merges at least 30 valid samples from the specified source URL into a single DataFrame without crashing.
2. **Given** a valid chemical composition string (e.g., "Zr50Cu40Al10"), **When** the descriptor computation module processes it, **Then** it returns a dictionary containing atomic size mismatch, mixing enthalpy, and electronegativity with no null values.
3. **Given** the merged dataset, **When** the data validation step runs, **Then** it reports the count of records dropped due to missing critical variables and ensures the final dataset contains ≥ 30 valid samples for model training (with a target of ≥ 500 for research validity). A sample is 'valid' if it has non-null values for composition, target variable, and all computed descriptors, and is chemically balanced (sum of atomic percentages within ± 1%).
4. **Given** the raw data, **When** the target detection logic runs, **Then** it correctly identifies whether the dataset supports regression (continuous $D_c$) or classification (binary label) and sets the `target_type` flag accordingly.
5. **Given** the dataset contains < 30 valid samples, **When** the validation step runs, **Then** it halts execution and raises a `DataValidationError` with the message 'Insufficient valid samples: {count} found, minimum required is 30'.
6. **Given** the dataset contains a missing variable for the *entire* dataset (e.g., no $D_c$ column exists), **When** the validation step runs, **Then** it halts execution and raises a `DataValidationError` with the message 'Missing required variable: {variable_name} in {dataset_name}'. If the missing variable is only in specific rows, those rows are dropped and the process continues, logging the count of dropped records.

---

### User Story 2 - CPU-Constrained Model Training, Validation, and Power Analysis (Priority: P2)

The researcher needs to train a Gradient Boosting model (XGBoost) on the computed dataset. If the target is continuous $D_c$, the system trains a regressor; if binary, a classifier. The entire training and cross-validation process must complete within 6 hours on a standard CI runner (limited CPU, 7GB RAM), using deterministic splitting for reproducibility. The system MUST use 'Cluster-Aware Cross-Validation' (stratified by chemical family, e.g., Zr-based, Cu-based) to prevent data leakage and ensure generalization. Additionally, the system MUST perform a post-hoc power analysis or calculate the Minimum Detectable Effect Size (MDES) to justify the sample size, reporting the results without blocking execution if power is low.

**Why this priority**: This delivers the core predictive capability. The constraint of CPU-only execution is critical for the project's feasibility in academic/small-industry settings. The dual-mode support ensures the scientific question (predicting $D_c$) is addressed directly where data allows. The fallback to binary classification is scientifically valid provided labels are empirically observed and not derived from the descriptors. The power analysis ensures statistical rigor.

**Independent Test**: Can be fully tested by executing the training script in a Docker container mimicking the CI environment (2 CPU, 7GB RAM) and verifying the model converges, outputs a pickled model file, performance metrics, and a power analysis report without memory errors or timeout.

**Acceptance Scenarios**:

1. **Given** the prepared training dataset with a fixed random seed of 42, **When** the model is trained with default CPU parameters, **Then** the training process completes in ≤ 6 hours on a 2-core CPU environment (target: < 30 minutes).
2. **Given** a trained model, **When** 5-fold Cluster-Aware Cross-Validation is executed, **Then** the system outputs the primary metric (mean AUC for classification, mean R² for regression) and its standard deviation is less than 10% of the mean metric value, indicating model stability.
3. **Given** the test set (held out with seed=42), **When** predictions are generated, **Then** the system reports the achieved accuracy (classification) or R² (regression) against the baseline (majority class frequency for classification, or intercept-only model for regression), without triggering "Out of Memory" errors.
4. **Given** the final model and dataset size, **When** the power analysis module runs, **Then** it calculates the Minimum Detectable Effect Size (MDES) and reports the achieved power at α=0.05. The process completes successfully regardless of the power value.

---

### User Story 3 - Interpretability and Descriptor Ranking (Priority: P3)

The researcher needs to extract feature importance scores from the trained model, perform collinearity diagnostics, and visualize decision boundaries (or partial dependence plots) for the top 2-3 descriptor pairs to understand which thermodynamic properties most strongly influence glass formation.

**Why this priority**: This provides the scientific insight (answering the research question) rather than just a black-box prediction, fulfilling the "interpretability" goal of the idea.

**Independent Test**: Can be tested by running the analysis script on a pre-trained model and verifying that the output includes a ranked list of all descriptors, VIF scores, and a generated PNG plot showing the relationship for the top two features.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** the feature importance extraction module runs, **Then** it outputs a ranked list of ALL computed descriptors with their importance scores.
2. **Given** the top two descriptors, **When** the visualization script executes, **Then** it generates a 2D plot (decision boundary for classification, partial dependence for regression) that shows a monotonic trend with p < 0.05 in a 1000-iteration permutation test or an AUC > 0.6 for the top two features.
3. **Given** the full analysis results, **When** the summary report is generated, **Then** it explicitly states the top 3 predictors and their relative contribution percentages, matching the model's internal importance scores.
4. **Given** the top predictors, **When** the collinearity diagnostic runs, **Then** it calculates Variance Inflation Factor (VIF) scores for all top predictors and writes them to the `ModelArtifact` JSON file with a 'comment' field.

---

### User Story 4 - Threshold Sensitivity Analysis (Priority: P3)

The researcher needs to perform a sensitivity analysis on the classification threshold (if the task is binary classification) to determine the optimal operating point for high-recall screening.

**Why this priority**: In screening applications, the cost of false negatives may differ from false positives. A fixed threshold (0.5) may not be optimal. This analysis ensures the model is robust across different operating points.

**Independent Test**: Can be tested by running the sensitivity analysis script on a pre-trained classifier and verifying that the output includes a table of false-positive and false-negative rates for the swept cutoff values.

**Acceptance Scenarios**:

1. **Given** a trained binary classifier, **When** the sensitivity analysis module runs, **Then** it sweeps the classification threshold (probability of 'glass') over the continuous range [0.0, 1.0] in steps of 0.05 (21 points).
2. **Given** the swept thresholds, **When** the analysis completes, **Then** it reports the variation in false-positive and false-negative rates for each cutoff value.
3. **Given** the results, **When** the report is generated, **Then** it identifies the threshold that maximizes the F1-score.

---

### User Story 5 - Report Generation and Causal Framing (Priority: P3)

The researcher needs to generate a final report that frames all predictive findings as associational (not causal) and includes a 'Limitations' section.

**Why this priority**: The data is observational. Misrepresenting associations as causation would be scientifically invalid. This ensures the report adheres to scientific rigor.

**Independent Test**: Can be tested by running the report generation script and verifying that the output includes the required 'Limitations' section and passes a keyword scan for causal verbs.

**Acceptance Scenarios**:

1. **Given** the model results, **When** the report generation script runs, **Then** it produces a report that explicitly frames all findings as associational.
2. **Given** the generated report, **When** a keyword scan for causal verbs (e.g., "causes", "determines", "leads to") is run, **Then** the scan returns zero matches for causal language in the results section.
3. **Given** the report, **When** the 'Limitations' section is reviewed, **Then** it explicitly states the observational nature of the data and the lack of causal inference.

---

### User Story 6 - Collinearity, Circularity, and Provenance Diagnostics (Priority: P3)

The researcher needs to verify that binary labels are empirically observed (not derived from descriptors), test for circularity (target not a function of descriptors), and perform collinearity diagnostics (VIF). Additionally, the system must check for selection bias related to "Inoue's Rules".

**Why this priority**: Circular validation (where the target is defined by the features) invalidates the model. Collinearity can inflate feature importance. Ensuring data provenance and independence is critical for scientific validity.

**Independent Test**: Can be tested by running the diagnostics script on the dataset and model and verifying that VIF scores are reported, circularity tests are passed, and label provenance is verified.

**Acceptance Scenarios**:

1. **Given** the dataset, **When** the circularity test runs, **Then** it checks if the target variable can be perfectly reconstructed from the descriptors (e.g., R² > 0.99 for a simple linear model) and raises a `CircularDataError` if detected.
2. **Given** binary labels, **When** the provenance check runs, **Then** it verifies that labels are empirically observed outcomes or, if derived from $D_c$, that the threshold used is a physically meaningful value (e.g., 1mm) and not an arbitrary statistical split.
3. **Given** the top predictors, **When** the collinearity diagnostic runs, **Then** it calculates Variance Inflation Factor (VIF) scores for all top predictors and writes them to the `ModelArtifact` JSON file with a 'comment' field.
4. **Given** the dataset, **When** the selection bias check runs, **Then** it verifies that the distribution of descriptors does not show a bias towards known "Inoue's Rules" regions that would trivialize the prediction task, and reports any detected bias.

### Edge Cases

- What happens when the public repositories return incomplete data or change their API structure? (System logs the error and skips the specific record, continuing with the rest of the batch).
- How does the system handle compositions with elements not present in the `pymatgen` element database? (The system flags these as "Unknown Element" and excludes them from the training set, logging the exclusion).
- What happens if the dataset is too small for 5-fold cross-validation (e.g., < 30 samples)? (The system halts execution and raises a `DataValidationError` with the message 'Insufficient samples for training: {count} found, minimum required is 30').
- How does the system handle extreme outliers in mixing enthalpy that might skew the model? (The system applies a robust scaling transformation and logs the range of values).
- What happens if the target variable $D_c$ is missing for all samples? (The system automatically falls back to binary classification mode if a binary label is available, otherwise halts. The binary labels MUST be verified as empirically observed outcomes, not calculated from descriptors).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download metallic glass composition data from the verified Zenodo dataset (DOI: 10.5281/zenodo.5778205), merging them into a single dataset with ≥ 30 valid samples (target ≥ 500) (See US-1).
- **FR-002**: System MUST compute atomic descriptors (atomic size mismatch, mixing enthalpy, electronegativity) for every composition using `pymatgen`, ensuring no null values for the primary predictors (See US-1).
- **FR-003**: System MUST detect the target variable type: if continuous critical casting thickness ($D_c$) is available, train a regressor; otherwise, train a binary classifier (glass vs. crystal). Training must complete within 6 hours on a 2-core, 7GB RAM environment. The system MUST use '5-fold Cluster-Aware Cross-Validation' (stratified by chemical family) to prevent data leakage (See US-2).
- **FR-004**: System MUST output a ranked list of feature importances and generate a 2D visualization of the relationship for the top two descriptors (decision boundary for classification, partial dependence for regression) (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis on the classification threshold (probability of 'glass') by sweeping the cutoff value over the continuous range from the minimum to the maximum probability in regular steps (21 points) and reporting the variation in false-positive and false-negative rates to determine the optimal operating point (maximizing F1-score). This requirement applies ONLY when the target is binary (See US-4).
- **FR-006**: System MUST validate that the dataset contains all required variables (target variable and predictors) before training. If a required variable is missing for the entire dataset, the system MUST halt execution and raise a `DataValidationError` with the message 'Missing required variable: {variable_name} in {dataset_name}'. If missing only in specific rows, those rows are dropped and the count is logged. (See US-1).
- **FR-007**: System MUST frame all predictive findings as associational (not causal) in the final report, as the data is observational. The final report MUST include a 'Limitations' section explicitly stating this, and the report generation script MUST verify this via a keyword scan for causal verbs (See US-5).
- **FR-008**: System MUST perform a collinearity diagnostic (Variance Inflation Factor) on the top predictors and report VIF scores, noting that high correlation may be physically expected in thermodynamic descriptors. VIF scores MUST be written to the `ModelArtifact` JSON file with a 'comment' field (See US-3).
- **FR-009**: System MUST verify that binary labels (if used) are empirically observed outcomes or, if derived from $D_c$, that the threshold used is a physically meaningful value (e.g., 1mm) and not an arbitrary statistical split. If a circular relationship is detected (see FR-013), the system MUST halt execution (See US-6).
- **FR-010**: System MUST perform a post-hoc power analysis or calculate the Minimum Detectable Effect Size (MDES) for the final model and report the achieved power at α=0.05. The process must complete successfully regardless of the power value (See US-2).
- **FR-011**: System MUST filter or document cooling rate/processing conditions if available in the dataset. If data is missing, the system MUST explicitly state this as a potential confounder in the final report (See US-2).
- **FR-012**: System MUST verify that the target variable (GFA/$D_c$) is an empirical observation distinct from the calculated descriptors to avoid circular validation (See US-6).
- **FR-013**: System MUST test for circularity by checking if the target variable can be perfectly reconstructed from the descriptors (e.g., R² > 0.99 for a simple linear model, configurable default 0.99). If detected, the system MUST halt execution and raise a `CircularDataError` (See US-6).
- **FR-014**: System MUST compute a SHA-256 checksum of the processed dataset and record it in the `state/` directory to ensure data integrity and reproducibility (See US-1).
- **FR-015**: System MUST check for selection bias related to "Inoue's Rules" by verifying that the dataset distribution of descriptors does not trivialize the prediction task, and report any detected bias in the final report (See US-6).

### Key Entities

- **CompositionRecord**: Represents a single alloy sample (a row in the `DataFrame`), containing the chemical formula, target variable (critical casting thickness or binary glass/crystal label), detected target type, and computed atomic descriptors. This entity maps to the operational "samples" mentioned in User Stories.
- **DescriptorSet**: A collection of computed thermodynamic properties (atomic size mismatch, mixing enthalpy, electronegativity) derived from the elemental composition (columns in the `DataFrame`). This entity maps to the "computed descriptors" used in the analysis.
- **ModelArtifact**: The trained XGBoost model object (regressor or classifier), containing hyperparameters, feature importances, VIF scores, and performance metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the requirement of ≥ 30 valid samples (target ≥ 500) with non-null predictors, where 'valid' means non-null composition, target, descriptors, and chemically balanced (See FR-001, FR-006).
- **SC-002**: Model training time is measured against the 6-hour CPU-only constraint on a 2-core, 7GB RAM environment (See FR-003).
- **SC-003**: Classification accuracy (or regression R²) is measured against the baseline of majority class frequency (classification) or intercept-only model (regression), with a post-hoc power analysis or MDES justification reported (See FR-003, FR-010, US-2).
- **SC-004**: Feature importance stability is measured against the standard deviation of scores across 5-fold Cluster-Aware Cross-Validation (See FR-004, US-3).
- **SC-005**: Threshold sensitivity is measured by the variation in recall and precision across the swept cutoff values [0.0, 1.0] in steps of 0.05 (21 points) (See FR-005).
- **SC-006**: Collinearity diagnostics are measured by the Variance Inflation Factor (VIF) for the top predictors, with a report generated for all scores and a 'comment' field in the `ModelArtifact` (See FR-008).

## Assumptions

- The verified Zenodo dataset (DOI: 10.5281/zenodo.5778205) will provide access to at least 500 metallic glass compositions with either critical casting thickness ($D_c$) or a binary glass/crystal label.
- The `pymatgen` library will contain the necessary elemental properties (atomic radius, electronegativity) for all elements present in the collected datasets.
- The "Glass Data Repository" and similar public datasets use consistent formatting for chemical compositions (e.g., Hill notation or standard elemental percentages).
- The target variable "critical casting thickness" ($D_c$) is the primary research goal; if available, the system defaults to regression. Binary classification is a fallback if $D_c$ is missing, provided labels are empirically observed.
- The XGBoost library will run efficiently on CPU without requiring GPU acceleration or quantization (8-bit/4-bit).
- The "mixing enthalpy" and "atomic size mismatch" descriptors can be computed accurately from the elemental composition alone without needing complex structural data.
- The dataset is observational; therefore, no causal claims will be made about the effect of descriptors on glass formation, only associations.
- The 6-hour runtime limit on a GitHub Actions free-tier runner is sufficient for training a Gradient Boosting model on a dataset of ≤ 1,000 samples.
- **Hypothesis**: A small set of top descriptors identified by the model will align with established materials science theories. (e.g., Inoue's rules), specifically highlighting "Mixing Enthalpy" and "Atomic Size Mismatch" as dominant predictors. (Note: This is a research hypothesis, not a functional requirement).
- The public data sources do not require authentication tokens that expire within the 6-hour window of the CI job.
- If the dataset contains < 500 samples but ≥ 30, the project proceeds with a warning and reduced statistical power, as defined in FR-010.
- The binary labels in the fallback dataset are empirically observed outcomes and not derived from the input descriptors.
- Cooling rate/processing conditions may be missing from the dataset; if so, this is explicitly documented as a potential confounder (FR-011).
- High collinearity among thermodynamic descriptors is physically expected and will be reported via VIF scores (FR-008).