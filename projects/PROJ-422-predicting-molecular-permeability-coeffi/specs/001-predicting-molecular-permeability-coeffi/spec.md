# Feature Specification: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Feature Branch**: `001-molecular-permeability-gnn`  
**Created**: 2026-07-28  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully ingest public permeability datasets (SMILES strings and experimental coefficients), parse them into molecular graphs using RDKit, and compute standard molecular descriptors to create a unified, stratified training/test split.

**Why this priority**: Without a clean, reproducible dataset split and feature extraction pipeline, no model training or comparison is possible. This is the foundational block for all subsequent analysis.

**Independent Test**: The pipeline can be run end-to-end on a sample subset of the data, producing a CSV of processed features and a separate test set CSV, with a logged report confirming the stratification by polymer type.

**Acceptance Scenarios**:

1. **Given** a public dataset file containing SMILES and permeability coefficients, **When** the ingestion script runs, **Then** the system outputs a processed dataset where every molecule has both a graph representation and a vector of standard descriptors (MW, logP, TPSA, etc.).
2. **Given** the processed dataset, **When** the split operation executes, **Then** the data is divided into training and testing sets using a standard split ratio, with stratification ensuring that the distribution of polymer types is preserved in both sets (absolute percentage point difference < 5%).
3. **Given** a dataset with missing values, **When** the pipeline processes it, **Then** the system either imputes missing descriptor values using a defined method (e.g., median) or excludes the row with a logged warning, ensuring no NaN values remain in the final input matrices.

---

### User Story 2 - Comparative Model Training and Evaluation (Priority: P2)

The system must train a CPU-optimized Graph Neural Network (MPNN) and a Random Forest baseline on the prepared data, then evaluate both models using RMSE, MAE, and R² metrics to determine if the GNN provides a statistically significant improvement over a strictly non-topological baseline.

**Why this priority**: This addresses the core research question: whether graph-based representations capture non-linear nuances missed by standard descriptors. It delivers the primary quantitative result.

**Independent Test**: The training script runs to completion, outputs performance metrics for both models, and performs a paired t-test on prediction errors, returning a p-value indicating statistical significance.

**Acceptance Scenarios**:

1. **Given** the stratified training set, **When** the GNN model trains for up to 50 epochs with early stopping, **Then** the model converges to a validation loss minimum without exceeding a reasonable CPU time budget or memory footprint.
2. **Given** the trained models and the held-out test set, **When** predictions are generated, **Then** the system calculates RMSE, MAE, and R² for both the GNN and Random Forest, and stores these metrics in a results log.
3. **Given** the prediction errors from both models, **When** the statistical analysis runs, **Then** a paired t-test is performed, and the system reports whether the GNN's reduction in error is statistically significant (p < 0.05) compared to the Random Forest baseline trained on graph-derived features only.

---

### User Story 3 - Feature Attribution and Interpretability Analysis (Priority: P3)

The system must apply GNNExplainer to the GNN and SHAP analysis to the Random Forest to identify and rank the specific topological features or substructures that drive permeability predictions.

**Why this priority**: This fulfills the "mechanistic" aspect of the research question, moving beyond "black box" predictions to identify *which* substructures account for the performance gap.

**Acceptance Test**: The analysis generates a ranked list of top features/substructures and a visualization (e.g., heatmap or bar chart) showing their contribution to the prediction variance.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model, **When** SHAP analysis is executed, **Then** the system outputs a ranked list of standard molecular descriptors by their absolute mean SHAP value.
2. **Given** the trained GNN model, **When** GNNExplainer is executed, **Then** the system identifies and reports the top most influential node-level substructures (e.g., specific aromatic rings or functional groups) across the test set.
3. **Given** the results from both models, **When** the comparison report is generated, **Then** the system highlights any specific substructures that the GNN identifies as critical but are absent or low-ranked in the descriptor-based model.

### Edge Cases

- **What happens when** the public dataset contains SMILES strings that RDKit cannot parse (invalid chemistry)?
  - **System handles**: The pipeline logs the invalid SMILES, excludes them from the dataset with a count, and proceeds with the valid subset.
- **How does system handle** a scenario where the GNN fails to converge or overfits significantly on the small dataset?
  - **System handles**: Early stopping triggers, and the model reverts to the epoch with the lowest validation loss; if performance is worse than the baseline, the result is flagged as "No significant improvement" rather than forcing a false positive.
- **What happens when** the dataset size is too small to support a meaningful stratified split (e.g., < 50 samples)?
  - **System handles**: The system falls back to a simple random split but logs a warning about potential data leakage and reduced statistical power, requiring manual review of the results.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest public permeability datasets (SMILES + coefficients) and parse them into molecular graphs using RDKit to support feature extraction (See US-1).
- **FR-002**: System MUST compute a standard set of molecular descriptors (MW, logP, TPSA, etc.) for every molecule to serve as the baseline input (See US-1).
- **FR-003**: System MUST split the dataset into [deferred] training and [deferred] testing sets with stratification by polymer type to prevent data leakage (See US-1).
- **FR-004**: System MUST train a Message Passing Neural Network (MPNN) using PyTorch Geometric on CPU-only hardware with early stopping based on validation loss (See US-2).
- **FR-005**: System MUST train a Random Forest regressor using the computed standard descriptors as a baseline for comparison (See US-2).
- **FR-006**: System MUST evaluate both models using RMSE, MAE, and R² metrics on the held-out test set (See US-2).
- **FR-007**: System MUST perform a paired t-test on prediction errors between the GNN and the Random Forest baseline (trained on graph-derived features only) to assess statistical significance (See US-2).
- **FR-008**: System MUST apply GNNExplainer to the GNN and SHAP analysis to the Random Forest to identify predictive features (See US-3).
- **FR-009**: System MUST generate a comparative report highlighting specific topological features identified by the GNN but missed by the descriptor baseline (See US-3).
- **FR-010**: System MUST handle invalid SMILES strings by logging and excluding them without crashing the pipeline (See Edge Cases).
- **FR-011**: System MUST ensure that at least 95% of valid molecules are retained after preprocessing; if retention falls below this threshold, the pipeline must halt and report the cause (See US-1).
- **FR-012**: System MUST perform a descriptor ablation study by training a Random Forest baseline on graph-derived features only (excluding standard descriptors) to isolate the incremental value of topology (See US-2).
- **FR-013**: System MUST perform a descriptor curation bias check by calculating the correlation between target values and input descriptors; if the absolute correlation exceeds a substantial threshold, the system must flag the results as potentially confounded (See US-1).

### Key Entities

- **Molecule**: A chemical entity defined by its SMILES string, containing attributes for graph representation, standard descriptors, and the target permeability coefficient.
- **Dataset**: A collection of molecules partitioned into training and testing sets, stratified by polymer type.
- **Model**: An instance of a machine learning algorithm (GNN or Random Forest) trained on the dataset to predict permeability.
- **Feature**: A specific molecular descriptor or topological substructure used as an input variable for the models.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in RMSE of the GNN model compared to the Random Forest baseline (trained on graph-derived features) is measured against the null hypothesis of no difference (See FR-007) (See US-2).
- **SC-002**: The statistical significance of the performance gap is measured against a conventional significance threshold using a paired t-test. (See FR-007) (See US-2).
- **SC-003**: The interpretability of the GNN is measured by the ability to rank specific topological substructures by GNNExplainer, compared to the ranked standard descriptors from SHAP (See FR-008) (See US-3).
- **SC-004**: The computational feasibility is measured by the total training time (must be ≤ 6 hours) and peak memory usage (must be ≤ 7 GB) on a CPU-only runner (See FR-004) (See US-2).
- **SC-005**: The data integrity is measured by the percentage of valid molecules retained after preprocessing (See FR-011) (See US-1).

## Assumptions

- Publicly available datasets (e.g., from NIST or Zenodo) contain sufficient samples (≥ 200 molecules) with both valid SMILES strings and experimental permeability coefficients for polymeric membranes to allow for a stratified A standard train-test split will be employed..
- For datasets with 50 ≤ N < 200 samples, the system will attempt stratified splitting; if stratification fails due to class imbalance, it will fall back to a random split with a warning logged.
- The PyTorch Geometric library and RDKit can be installed and run within the free-tier GitHub Actions environment (CPU cores, limited RAM) without requiring GPU acceleration or CUDA.
- The "standard molecular descriptors" computed by RDKit (MW, logP, TPSA, etc.) are sufficient to represent the baseline model's capability for comparison.
- The dataset does not require complex imputation for missing values; any missing data can be handled by median imputation or row exclusion without biasing the results significantly.
- The experimental permeability coefficients in the source datasets are independent measurements, and any potential circularity with structural descriptors will be detected by the bias check (FR-013).
- The GNN model architecture (3 layers) is sufficiently simple to avoid overfitting on the available dataset size, provided early stopping is used.
- GNNExplainer provides a scientifically valid approximation of feature importance for the specific MPNN architecture used.