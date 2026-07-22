# Feature Specification: Predicting Glass Formation Tendency with Machine Learning on Public Data

**Feature Branch**: `001-predict-glass-formation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Glass Formation Tendency with Machine Learning on Public Data"

## User Scenarios & Testing

### User Story 1 - Data Aggregation and Descriptor Computation (Priority: P1)

The researcher needs to automatically download metallic glass composition data from public repositories (Materials Project, Zenodo) and compute atomic descriptors (atomic size mismatch, mixing enthalpy, electronegativity) for each composition using `pymatgen` to create a unified, analysis-ready dataset.

**Why this priority**: Without a clean, computed dataset, no modeling or analysis can occur. This is the foundational step that enables all downstream research.

**Independent Test**: Can be fully tested by running the data processing script against a small subset of known compositions and verifying that the output CSV contains the expected columns (composition, target variable, computed descriptors) with no missing values for the primary predictors.

**Acceptance Scenarios**:

1. **Given** a list of public repository URLs for metallic glass data, **When** the data ingestion script executes, **Then** it successfully downloads and merges at least 80% of available records into a single DataFrame without crashing.
2. **Given** a valid chemical composition string (e.g., "Zr50Cu40Al10"), **When** the descriptor computation module processes it, **Then** it returns a dictionary containing atomic size mismatch, mixing enthalpy, and electronegativity with no null values.
3. **Given** the merged dataset, **When** the data validation step runs, **Then** it reports the count of records dropped due to missing critical variables (target or predictors) and ensures the final dataset contains ≥ 500 samples.

---

### User Story 2 - CPU-Constrained Model Training and Validation (Priority: P2)

The researcher needs to train a Gradient Boosting Classifier (XGBoost) on the computed dataset to predict glass formation (binary: glass vs. crystal) using only CPU resources, ensuring the entire training and cross-validation process completes within 6 hours on a standard CI runner (2 CPU, 7GB RAM).

**Why this priority**: This delivers the core predictive capability. The constraint of CPU-only execution is critical for the project's feasibility in academic/small-industry settings.

**Independent Test**: Can be fully tested by executing the training script in a Docker container mimicking the CI environment (2 CPU, 7GB RAM) and verifying the model converges and outputs a pickled model file and performance metrics without memory errors or timeout.

**Acceptance Scenarios**:

1. **Given** the prepared training dataset ([deferred] split), **When** the XGBoost model is trained with default CPU parameters, **Then** the training process completes in < 30 minutes on a 2-core CPU environment.
2. **Given** a trained model, **When** 5-fold cross-validation is executed, **Then** the system outputs mean AUC and RMSE scores with a standard deviation < 0.05, indicating model stability.
3. **Given** the test set ([deferred] holdout), **When** predictions are generated, **Then** the model achieves a classification accuracy of ≥ 70% (baseline) without triggering "Out of Memory" errors.

---

### User Story 3 - Interpretability and Descriptor Ranking (Priority: P3)

The researcher needs to extract feature importance scores from the trained model and visualize decision boundaries for the top 2-3 descriptor pairs to understand which thermodynamic properties most strongly influence glass formation.

**Why this priority**: This provides the scientific insight (answering the research question) rather than just a black-box prediction, fulfilling the "interpretability" goal of the idea.

**Independent Test**: Can be fully tested by running the analysis script on a pre-trained model and verifying that the output includes a ranked list of descriptors and a generated PNG plot showing the decision boundary for the top two features.

**Acceptance Scenarios**:

1. **Given** a trained XGBoost model, **When** the feature importance extraction module runs, **Then** it outputs a ranked list where "Mixing Enthalpy" and "Atomic Size Mismatch" appear in the top 3 positions.
2. **Given** the top two descriptors, **When** the visualization script executes, **Then** it generates a 2D scatter plot with decision boundaries that clearly separates "glass" vs. "crystal" regions.
3. **Given** the full analysis results, **When** the summary report is generated, **Then** it explicitly states the top 3 predictors and their relative contribution percentages, matching the model's internal importance scores.

### Edge Cases

- What happens when the public repositories return incomplete data or change their API structure? (System logs the error and skips the specific record, continuing with the rest of the batch).
- How does the system handle compositions with elements not present in the `pymatgen` element database? (The system flags these as "Unknown Element" and excludes them from the training set, logging the exclusion).
- What happens if the dataset is too small for 5-fold cross-validation (e.g., < 50 samples)? (The system falls back to 3-fold cross-validation or a simple train-test split and logs a warning).
- How does the system handle extreme outliers in mixing enthalpy that might skew the model? (The system applies a robust scaling transformation and logs the range of values).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download metallic glass composition data from the Materials Project API and Zenodo repositories, merging them into a single dataset with ≥ 500 valid samples (See US-1).
- **FR-002**: System MUST compute atomic descriptors (atomic size mismatch, mixing enthalpy, electronegativity) for every composition using `pymatgen`, ensuring no null values for the primary predictors (See US-1).
- **FR-003**: System MUST train a Gradient Boosting Classifier (XGBoost) using only CPU resources, completing training and 5-fold cross-validation within 6 hours on a 2-core, 7GB RAM environment (See US-2).
- **FR-004**: System MUST output a ranked list of feature importances and generate a 2D visualization of the decision boundary for the top two descriptors (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis on the classification threshold by sweeping the cutoff value over {0.4, 0.5, 0.6} and reporting the variation in false-positive and false-negative rates (See US-2).
- **FR-006**: System MUST validate that the dataset contains all required variables (target variable and predictors) before training; if a required variable is missing, it MUST halt and report `[NEEDS CLARIFICATION: does <dataset> contain <variable>?]` (See US-1).
- **FR-007**: System MUST frame all predictive findings as associational (not causal) in the final report, as the data is observational (See US-2).
- **FR-008**: System MUST perform a collinearity diagnostic (e.g., Variance Inflation Factor) on the top predictors to ensure no two descriptors are definitionally redundant (See US-3).

### Key Entities

- **CompositionRecord**: Represents a single alloy sample, containing the chemical formula, target variable (critical casting thickness or binary glass/crystal label), and computed atomic descriptors.
- **DescriptorSet**: A collection of computed thermodynamic properties (atomic size mismatch, mixing enthalpy, electronegativity) derived from the elemental composition.
- **ModelArtifact**: The trained XGBoost model object, containing hyperparameters, feature importances, and performance metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the requirement of ≥ 500 valid samples with non-null predictors (See FR-001, FR-006).
- **SC-002**: Model training time is measured against the 6-hour CPU-only constraint on a 2-core, 7GB RAM environment (See FR-003).
- **SC-003**: Classification accuracy is measured against the baseline of random guessing ([deferred]) and the project goal of >80% (See FR-003, US-2).
- **SC-004**: Feature importance stability is measured against the standard deviation of scores across 5-fold cross-validation (See FR-004, US-3).
- **SC-005**: Threshold sensitivity is measured by the variation in false-positive rates across the swept cutoff values {0.4, 0.5, 0.6} (See FR-005).
- **SC-006**: Collinearity diagnostics are measured by the Variance Inflation Factor (VIF) for the top predictors, ensuring VIF < 5 (See FR-008).

## Assumptions

- The public repositories (Materials Project, Zenodo) will provide access to at least 500 metallic glass compositions with both composition and target variable (glass/crystal or casting thickness) data.
- The `pymatgen` library will contain the necessary elemental properties (atomic radius, electronegativity) for all elements present in the collected datasets.
- The "Glass Data Repository" and similar public datasets use consistent formatting for chemical compositions (e.g., Hill notation or standard elemental percentages).
- The target variable "critical casting thickness" will be available in a binary format (glass vs. crystal) or can be reliably binarized using a standard threshold (e.g., >1mm).
- The XGBoost library will run efficiently on CPU without requiring GPU acceleration or quantization (8-bit/4-bit).
- The "mixing enthalpy" and "atomic size mismatch" descriptors can be computed accurately from the elemental composition alone without needing complex structural data.
- The dataset is observational; therefore, no causal claims will be made about the effect of descriptors on glass formation, only associations.
- The 6-hour runtime limit on a GitHub Actions free-tier runner is sufficient for training a Gradient Boosting model on a dataset of ≤ 1,000 samples.
- The top 3-5 descriptors identified by the model will align with established materials science theories (e.g., Inoue's rules).
- The public data sources do not require authentication tokens that expire within the 6-hour window of the CI job.
