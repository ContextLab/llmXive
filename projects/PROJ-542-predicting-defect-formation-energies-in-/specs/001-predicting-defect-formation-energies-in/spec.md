# Feature Specification: Predicting Defect Formation Energies in Perovskites with Machine Learning

**Feature Branch**: `001-predicting-defect-formation-energies`  
**Created**: 2026-05-14  
**Status**: Draft  
**Input**: User description: "Predicting Defect Formation Energies in Perovskites with Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Feature Engineering (Priority: P1)

The researcher MUST be able to download a dataset of perovskite defect formation energies from the Materials Project API and automatically generate a feature matrix containing atomic radii, electronegativity, oxidation states, and valence electron counts for the A, B, and X sites using `pymatgen`.

**Why this priority**: This is the foundational step; without a validated dataset and correctly engineered features, no modeling can occur. It addresses the "grounded in physical reality" concern by ensuring the input data source is explicitly defined and reproducible.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output CSV contains ≥500 rows with exactly the 12 expected feature columns (4 descriptors × 3 sites) and a valid target column, with no missing values in the target.

**Acceptance Scenarios**:

1. **Given** a valid Materials Project API key and network access, **When** the data pipeline script runs, **Then** a CSV file is generated containing at least 500 perovskite compositions with oxygen vacancy defect formation energies and the specified compositional descriptors.
2. **Given** the generated CSV, **When** a validation script checks the columns, **Then** the script confirms the presence of atomic radii, electronegativity, oxidation states, and valence electron counts for A, B, and X sites, and reports zero null values in the target energy column.

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

The researcher MUST be able to train baseline machine learning models (Random Forest and Gradient Boosting) on the engineered dataset using 5-fold cross-validation, ensuring the entire process completes on a CPU-only environment without GPU dependencies.

**Why this priority**: This validates the core hypothesis that compositional descriptors can predict defect energies. It must run on free-tier CI resources (CPU only) to ensure feasibility.

**Independent Test**: Can be fully tested by running the training script on a standard GitHub Actions runner (2 CPU, 7GB RAM) and verifying the script outputs cross-validation metrics (RMSE, MAE, R²) without triggering CUDA errors or memory overflow.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** the training script executes on a CPU-only runner, **Then** both Random Forest and Gradient Boosting models complete 5-fold cross-validation and output a JSON report containing mean RMSE, MAE, and R² for each model.
2. **Given** the training environment, **When** the script attempts to load the models, **Then** no errors related to CUDA, GPU device mapping, or bitsandbytes quantization occur, and the total execution time remains [deferred].

---

### User Story 3 - Performance Evaluation and Feature Importance (Priority: P3)

The researcher MUST be able to evaluate the best-performing model against a held-out test set ([deferred] of data) and generate a ranked list of feature importances to identify which compositional descriptors most strongly influence defect formation energy.

**Why this priority**: This delivers the scientific insight required to answer the research question and provides the "rapid screening" capability mentioned in the motivation.

**Independent Test**: Can be fully tested by running the evaluation script and verifying the output includes a scatter plot of predicted vs. actual energies, a statistical significance test result (p-value), and a sorted list of feature importances.

**Acceptance Scenarios**:

1. **Given** the trained model and the held-out test set, **When** the evaluation script runs, **Then** it outputs an RMSE < 0.5 eV (if the hypothesis holds) or a clear statement of higher error, along with a p-value from a paired t-test comparing predictions to DFT ground truth.
2. **Given** the trained model, **When** the feature importance analysis runs, **Then** it generates a bar chart and a text list ranking the 12 compositional descriptors by their contribution to the model's prediction, with the top 3 descriptors clearly identified.

---

### Edge Cases

- What happens when the Materials Project API returns an empty result set for a specific perovskite structure type? The system MUST log a warning and halt with a clear error message indicating "No data found for specified filters," rather than crashing with a generic exception.
- How does the system handle compositions with missing oxidation states in the source data? The pipeline MUST filter out any rows where oxidation states cannot be determined, logging the count of excluded samples to ensure data integrity.
- What if the dataset size is insufficient for a robust 5-fold cross-validation (e.g., < 50 samples)? The system MUST raise a `ValueError` and prevent training, requiring the user to broaden the search filters to ensure statistical power.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download defect formation energy data for perovskites from the Materials Project API, filtering specifically for oxygen vacancies, and store the raw data locally. (See US-1)
- **FR-002**: The system MUST extract and compute compositional descriptors (atomic radii, Pauling electronegativity, oxidation states, valence electron counts) for A, B, and X sites using `pymatgen` for every entry in the dataset. (See US-1)
- **FR-003**: The system MUST train Random Forest and Gradient Boosting regressors using scikit-learn with 5-fold cross-validation, ensuring all operations are performed on CPU without GPU acceleration. (See US-2)
- **FR-004**: The system MUST evaluate the trained models on a held-out [deferred] test set, calculating RMSE, MAE, and R², and performing a paired t-test against DFT ground truth values. (See US-3)
- **FR-005**: The system MUST generate a feature importance ranking and visualize the relationship between predicted and actual defect formation energies via scatter plots. (See US-3)
- **FR-006**: The system MUST explicitly flag and report any dataset-variable gaps where the Materials Project data lacks a required descriptor for a specific composition, rather than imputing or ignoring them. (See US-1)

### Key Entities

- **PerovskiteComposition**: Represents a unique material formula (ABX3) with associated structural type and defect configuration.
- **DescriptorSet**: A collection of calculated atomic properties (radii, electronegativity, etc.) for the A, B, and X sites of a composition.
- **DefectEnergy**: The target variable representing the DFT-calculated formation energy for a specific defect (e.g., oxygen vacancy).
- **ModelPerformance**: A record containing metrics (RMSE, MAE, R², p-value) for a specific model configuration on a specific dataset split.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The model's prediction error (RMSE) is measured against the threshold of 0.5 eV, which serves as the benchmark for "rapid screening" viability in materials discovery workflows. (See US-3)
- **SC-002**: The variance explained by compositional descriptors (R²) is measured against the target of ≥70% to determine if simple descriptors suffice or if complex structural representations are needed. (See US-3)
- **SC-003**: The statistical significance of the model's predictions is measured against the DFT ground truth using a paired t-test at α=0.05 to confirm the model is not performing random guessing. (See US-3)
- **SC-004**: The computational feasibility is measured against the constraint of running entirely on a CPU-only GitHub Actions runner (≤2 cores, ~7 GB RAM) within a 6-hour time limit. (See US-2)
- **SC-005**: The data coverage is measured against the requirement of having at least 500 valid perovskite compositions with complete descriptor sets to ensure sufficient statistical power for cross-validation. (See US-1)

## Assumptions

- The Materials Project API provides sufficient access to defect formation energy data for perovskites without requiring a premium subscription or exceeding rate limits during the data download phase.
- The "oxygen vacancy" is the primary defect type of interest, and the Materials Project dataset contains a representative sample of this specific defect across diverse perovskite compositions.
- The compositional descriptors (atomic radii, electronegativity, etc.) derived from `pymatgen` are consistent with the definitions used in the referenced literature (e.g., Pauling electronegativity).
- The relationship between compositional descriptors and defect formation energy is sufficiently linear or tree-learnable for Random Forest and Gradient Boosting models to capture, without requiring deep learning architectures.
- The GitHub Actions free-tier runner provides consistent CPU performance and memory availability (≥7 GB) sufficient to load the ~500-1000 sample dataset and train the models without swapping.
- The DFT-calculated defect formation energies in the Materials Project are treated as the ground truth for this study, acknowledging they are computational values rather than experimental measurements, as the project scope is to validate ML against DFT, not against wet-lab experiments.
