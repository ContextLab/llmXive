# Feature Specification: Predicting Glass Formation Tendency with Machine Learning on Public Data

**Feature Branch**: `001-predict-glass-formation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Glass Formation Tendency with Machine Learning on Public Data"

## User Scenarios & Testing

### User Story 1 - Data Aggregation, Target Detection, and Descriptor Computation (Priority: P1)

The researcher needs to automatically download metallic glass composition data from public repositories (Materials Project, Zenodo), detect the available target variable (continuous critical casting thickness $D_c$ or binary glass/crystal label), and compute atomic descriptors (atomic size mismatch, mixing enthalpy, electronegativity) for each composition using `pymatgen` to create a unified, analysis-ready dataset.

**Why this priority**: Without a clean, computed dataset with the correct target variable detected, no modeling or analysis can occur. This is the foundational step that enables all downstream research.

**Independent Test**: Can be fully tested by running the data processing script against a small subset of known compositions and verifying that the output CSV contains the expected columns (composition, detected_target_type, target_value, computed descriptors) with no missing values for the primary predictors.

**Acceptance Scenarios**:

1. **Given** a list of public repository URLs for metallic glass data, **When** the data ingestion script executes, **Then** it successfully downloads and merges at least 30 valid samples from the specified source URLs into a single DataFrame without crashing.
2. **Given** a valid chemical composition string (e.g., "Zr50Cu40Al10"), **When** the descriptor computation module processes it, **Then** it returns a dictionary containing atomic size mismatch, mixing enthalpy, and electronegativity with no null values.
3. **Given** the merged dataset, **When** the data validation step runs, **Then** it reports the count of records dropped due to missing critical variables and ensures the final dataset contains ≥ 30 valid samples for model training (with a target of ≥ 500 for research validity).
4. **Given** the raw data, **When** the target detection logic runs, **Then** it correctly identifies whether the dataset supports regression (continuous $D_c$) or classification (binary label) and sets the `target_type` flag accordingly.

---

### User Story 2 - CPU-Constrained Model Training and Validation (Priority: P2)

The researcher needs to train a Gradient Boosting model (XGBoost) on the computed dataset. If the target is continuous $D_c$, the system trains a regressor; if binary, a classifier. The entire training and cross-validation process must complete within 6 hours on a standard CI runner (limited CPU, 7GB RAM), using deterministic splitting for reproducibility.

**Why this priority**: This delivers the core predictive capability. The constraint of CPU-only execution is critical for the project's feasibility in academic/small-industry settings. The dual-mode support ensures the scientific question (predicting $D_c$) is addressed directly where data allows.

**Independent Test**: Can be fully tested by executing the training script in a Docker container mimicking the CI environment (2 CPU, 7GB RAM) and verifying the model converges and outputs a pickled model file and performance metrics without memory errors or timeout.

**Acceptance Scenarios**:

1. **Given** the prepared training dataset with a fixed random seed of 42, **When** the model is trained with default CPU parameters, **Then** the training process completes in ≤ 6 hours on a 2-core CPU environment (target: < 30 minutes).
2. **Given** a trained model, **When** stratified 5-fold cross-validation (random seed=42) is executed, **Then** the system outputs mean AUC (for classification) or R² (for regression) and RMSE (for regression only) scores with a standard deviation < 0.05, indicating model stability.
3. **Given** the test set (held out with seed=42), **When** predictions are generated, **Then** the system reports the achieved accuracy (classification) or R² (regression) against the baseline, without triggering "Out of Memory" errors.

---

### User Story 3 - Interpretability and Descriptor Ranking (Priority: P3)

The researcher needs to extract feature importance scores from the trained model and visualize decision boundaries (or partial dependence plots) for the top 2-3 descriptor pairs to understand which thermodynamic properties most strongly influence glass formation.

**Why this priority**: This provides the scientific insight (answering the research question) rather than just a black-box prediction, fulfilling the "interpretability" goal of the idea.

**Independent Test**: Can be tested by running the analysis script on a pre-trained model and verifying that the output includes a ranked list of all descriptors and a generated PNG plot showing the relationship for the top two features.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** the feature importance extraction module runs, **Then** it outputs a ranked list of ALL computed descriptors with their importance scores.
2. **Given** the top two descriptors, **When** the visualization script executes, **Then** it generates a 2D plot (decision boundary for classification, partial dependence for regression) that clearly separates or trends the target variable.
3. **Given** the full analysis results, **When** the summary report is generated, **Then** it explicitly states the top 3 predictors and their relative contribution percentages, matching the model's internal importance scores.

### Edge Cases

- What happens when the public repositories return incomplete data or change their API structure? (System logs the error and skips the specific record, continuing with the rest of the batch).
- How does the system handle compositions with elements not present in the `pymatgen` element database? (The system flags these as "Unknown Element" and excludes them from the training set, logging the exclusion).
- What happens if the dataset is too small for 5-fold cross-validation (e.g., < 30 samples)? (The system halts execution and raises a `DataValidationError` with the message 'Insufficient samples for training: {count} found, minimum required is 30').
- How does the system handle extreme outliers in mixing enthalpy that might skew the model? (The system applies a robust scaling transformation and logs the range of values).
- What happens if the target variable $D_c$ is missing for all samples? (The system automatically falls back to binary classification mode if a binary label is available, otherwise halts).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download metallic glass composition data from the Materials Project API and Zenodo repositories, merging them into a single dataset with ≥ 30 valid samples (target ≥ 500) (See US-1).
- **FR-002**: System MUST compute atomic descriptors (atomic size mismatch, mixing enthalpy, electronegativity) for every composition using `pymatgen`, ensuring no null values for the primary predictors (See US-1).
- **FR-003**: System MUST detect the target variable type: if continuous critical casting thickness ($D_c$) is available, train a regressor; otherwise, train a binary classifier (glass vs. crystal). Training must complete within 6 hours on a 2-core, 7GB RAM environment (See US-2).
- **FR-004**: System MUST output a ranked list of feature importances and generate a 2D visualization of the relationship for the top two descriptors (decision boundary for classification, partial dependence for regression) (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis on the classification threshold (if applicable) by sweeping the cutoff value over a range of thresholds and reporting the variation in false-positive and false-negative rates (See US-2).
- **FR-006**: System MUST validate that the dataset contains all required variables (target variable and predictors) before training. If a required variable is missing, the system MUST halt execution and raise a `DataValidationError` with the message 'Missing required variable: {variable_name} in {dataset_name}'. The system MUST log the count of missing records and the specific missing fields. (See US-1).
- **FR-007**: System MUST frame all predictive findings as associational (not causal) in the final report, as the data is observational (See US-2).
- **FR-008**: System MUST perform a collinearity diagnostic (Variance Inflation Factor) on the top predictors and report VIF scores, noting that high correlation may be physically expected in thermodynamic descriptors (See US-3).

### Key Entities

- **CompositionRecord**: Represents a single alloy sample, containing the chemical formula, target variable (critical casting thickness or binary glass/crystal label), detected target type, and computed atomic descriptors.
- **DescriptorSet**: A collection of computed thermodynamic properties (atomic size mismatch, mixing enthalpy, electronegativity) derived from the elemental composition.
- **ModelArtifact**: The trained XGBoost model object (regressor or classifier), containing hyperparameters, feature importances, and performance metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the requirement of ≥ 30 valid samples (target ≥ 500) with non-null predictors (See FR-001, FR-006).
- **SC-002**: Model training time is measured against the 6-hour CPU-only constraint on a 2-core, 7GB RAM environment (See FR-003).
- **SC-003**: Classification accuracy (or regression R²) is measured against the baseline of chance performance ([deferred] for balanced binary classification or the majority class frequency for imbalanced data) (See FR-003, US-2).
- **SC-004**: Feature importance stability is measured against the standard deviation of scores across 5-fold cross-validation (See FR-004, US-3).
- **SC-005**: Threshold sensitivity is measured by the variation in false-positive rates across the swept cutoff values {0.4, 0.5, 0.6} (See FR-005).
- **SC-006**: Collinearity diagnostics are measured by the Variance Inflation Factor (VIF) for the top predictors, with a report generated for all scores (See FR-008).

## Assumptions

- The public repositories (Materials Project, Zenodo) will provide access to at least 500 metallic glass compositions with either critical casting thickness ($D_c$) or a binary glass/crystal label.
- The `pymatgen` library will contain the necessary elemental properties (atomic radius, electronegativity) for all elements present in the collected datasets.
- The "Glass Data Repository" and similar public datasets use consistent formatting for chemical compositions (e.g., Hill notation or standard elemental percentages).
- The target variable "critical casting thickness" ($D_c$) is the primary research goal; if available, the system defaults to regression. Binary classification is a fallback if $D_c$ is missing.
- The XGBoost library will run efficiently on CPU without requiring GPU acceleration or quantization (8-bit/4-bit).
- The "mixing enthalpy" and "atomic size mismatch" descriptors can be computed accurately from the elemental composition alone without needing complex structural data.
- The dataset is observational; therefore, no causal claims will be made about the effect of descriptors on glass formation, only associations.
- The 6-hour runtime limit on a GitHub Actions free-tier runner is sufficient for training a Gradient Boosting model on a dataset of ≤ 1,000 samples.
- **Hypothesis**: The top 3-5 descriptors identified by the model will align with established materials science theories (e.g., Inoue's rules), specifically highlighting "Mixing Enthalpy" and "Atomic Size Mismatch" as dominant predictors. (Note: This is a research hypothesis, not a functional requirement).
- The public data sources do not require authentication tokens that expire within the 6-hour window of the CI job.