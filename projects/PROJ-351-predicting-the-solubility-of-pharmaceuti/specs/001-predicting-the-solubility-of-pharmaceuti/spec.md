# Feature Specification: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

**Feature Branch**: `001-predict-solubility-gnn`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Pipeline and Baseline Establishment (Priority: P1)

The researcher MUST be able to download the ESOL dataset, preprocess SMILES strings into molecular graphs using RDKit, and train a Random Forest baseline model using Morgan fingerprints to establish a performance floor.

**Why this priority**: This is the foundational step. Without a validated data pipeline and a robust baseline (Random Forest), any GNN results cannot be interpreted as an improvement. It ensures the data is accessible and the experimental setup is functional before introducing complex model architectures.

**Independent Test**: The pipeline can be fully tested by running the data download, preprocessing, and Random Forest training script, verifying that a model is saved with an RMSE value < 5.0 on the test set.

**Acceptance Scenarios**:

1. **Given** the ESOL dataset URL is accessible, **When** the pipeline script is executed, **Then** the system downloads the CSV, splits it into 80/10/10 sets stratified by logS, and outputs a trained Random Forest model file.
2. **Given** the SMILES strings are loaded, **When** the RDKit preprocessor runs, **Then** it successfully converts all valid SMILES into molecular graph objects and logs the count of invalid entries (if any) without crashing.
3. **Given** the training set is prepared, **When** the Random Forest model is trained with Morgan fingerprints, **Then** the model achieves a test set R-squared value > 0.5 within 10 minutes of CPU time.

---

### User Story 2 - GNN Model Training and Evaluation (Priority: P2)

The researcher MUST be able to implement and train a Message Passing Neural Network (MPNN) configured strictly for CPU execution and evaluate its performance against the Random Forest baseline using RMSE and R-squared metrics.

**Why this priority**: This is the core research contribution. It tests the hypothesis that graph topology captures solubility drivers better than fixed descriptors. It must be independent of the baseline but relies on the data pipeline from US-1.

**Independent Test**: The GNN training script can be run independently (assuming data exists), and the resulting model must produce a test set RMSE that is recorded and compared to the baseline.

**Acceptance Scenarios**:

1. **Given** the preprocessed molecular graphs exist, **When** the MPNN model is trained for 100 epochs with early stopping, **Then** the training completes within 6 hours on a standard CPU runner without GPU errors.
2. **Given** the trained GNN model, **When** evaluated on the held-out test set, **Then** the system outputs the RMSE and R-squared metrics in a standardized JSON report.
3. **Given** both baseline and GNN predictions exist, **When** the comparison script runs, **Then** it calculates the difference in RMSE and flags whether the GNN outperforms the baseline by at least 0.1 RMSE units.

---

### User Story 3 - Statistical Significance and Interpretability (Priority: P3)

The researcher MUST be able to perform a paired t-test on prediction errors to determine statistical significance and generate feature importance visualizations to interpret topological contributions.

**Why this priority**: This provides the scientific validation. A lower RMSE alone is insufficient; the improvement must be statistically significant (p < 0.05). Interpretability validates the "mechanism" aspect of the research question.

**Independent Test**: The analysis script takes the prediction files from US-1 and US-2, runs the t-test, and generates a plot or table of feature importance.

**Acceptance Scenarios**:

1. **Given** the absolute prediction errors for both models, **When** the paired t-test is executed, **Then** the system outputs a p-value and explicitly states whether the null hypothesis (no difference) can be rejected at alpha = 0.05.
2. **Given** the trained GNN model, **When** the interpretability module runs, **Then** it generates a visualization (e.g., attention weight heatmap or node importance ranking) for at least 5 sample molecules showing which substructures influenced the prediction.
3. **Given** the analysis results, **When** the final report is generated, **Then** it includes a summary table comparing Baseline vs. GNN metrics and the statistical significance outcome.

### Edge Cases

- What happens when the ESOL dataset contains SMILES strings that RDKit fails to parse (e.g., malformed syntax)? The system must log these as invalid and exclude them from training, ensuring the dataset split remains consistent.
- How does the system handle a scenario where the GNN model fails to converge (validation loss increases indefinitely)? The early stopping mechanism must trigger after 10 epochs of no improvement, saving the best checkpoint rather than the final one.
- What if the Random Forest baseline already achieves near-perfect prediction (R² > 0.95)? The system must still run the GNN and report the t-test, even if the result is "no significant improvement," to validate the hypothesis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the ESOL dataset from the MoleculeNet repository and validate that the `logS` column is present and contains no NaN values. (See US-1)
- **FR-002**: System MUST convert SMILES strings into molecular graphs using RDKit, extracting atom features (atomic number, hybridization, charge) and bond features (bond type, conjugation, stereochemistry). (See US-1)
- **FR-003**: System MUST implement a Random Forest regressor using Morgan fingerprints (radius=2, 2048 bits) as the baseline model. (See US-1)
- **FR-004**: System MUST implement a Message Passing Neural Network (MPNN) using PyTorch Geometric configured to run exclusively on CPU (no CUDA/GPU calls). (See US-2)
- **FR-005**: System MUST split the dataset into [deferred] training, [deferred] validation, and [deferred] test sets, ensuring stratification based on `logS` bins to maintain distribution balance. (See US-1, US-2)
- **FR-006**: System MUST perform a paired t-test on the absolute prediction errors of the Random Forest and GNN models to determine statistical significance (alpha = 0.05). (See US-3)
- **FR-007**: System MUST generate a report containing RMSE, R-squared, and p-value metrics for both models. (See US-2, US-3)

### Key Entities

- **Molecule**: Represents a chemical compound with attributes: `smiles` (string), `logS` (float), `graph` (RDKit object), `features` (tensor).
- **Model**: Represents a trained predictor with attributes: `type` (RF/GNN), `metrics` (dict), `weights` (file path).
- **DatasetSplit**: Represents the partitioned data with attributes: `train_indices`, `val_indices`, `test_indices`, `logS_distribution`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The GNN model's RMSE is measured against the Random Forest baseline RMSE to quantify the performance delta. (See US-2)
- **SC-002**: The statistical significance of the performance difference is measured against the p-value threshold of 0.05 via paired t-test. (See US-3)
- **SC-003**: The computational feasibility is measured against the constraint of completing the full training and evaluation pipeline within 6 hours on a 2-core CPU runner. (See US-2)
- **SC-004**: The model interpretability is measured against the ability to generate valid feature importance visualizations for a representative subset of the test set. (See US-3)

## Assumptions

- The ESOL (Delaney) dataset is publicly available and accessible via the standard MoleculeNet URL without authentication.
- The RDKit library and PyTorch Geometric are compatible with the Python version used in the CI environment and can be installed without GPU dependencies.
- The ESOL dataset contains sufficient molecular diversity to support a meaningful 80/10/10 split without severe class imbalance in logS values.
- The "CPU-only" constraint implies that the GNN architecture will be simplified (e.g., fewer layers, smaller hidden dimensions) to ensure convergence within the 6-hour time limit on free-tier runners.
- The dataset variables (SMILES and logS) are sufficient for the proposed analysis; no additional experimental data (e.g., pH, temperature) is required or available in the source.
- The Random Forest baseline using Morgan fingerprints is an appropriate standard for comparison in this domain, as established by existing chemoinformatics literature.
