# Feature Specification: Predicting Molecular Reactivity Using Graph Neural Networks

**Feature Branch**: `001-predict-molecular-reactivity`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Reactivity Using Graph Neural Networks and Reaction Datasets"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

The system MUST ingest raw reaction data (SMILES strings), parse them into molecular graphs using RDKit, and extract atom/bond features to create a CPU-tractable dataset for analysis.

**Why this priority**: This is the foundational step; without a valid, structured dataset derived from the USPTO repository, no modeling or analysis can occur. It delivers the raw material for all subsequent research steps.

**Independent Test**: Can be fully tested by executing the data pipeline script on a subset of the USPTO dataset and verifying that the output is a valid graph dataset (e.g., PyG Data objects) with non-null node/edge features and no parsing errors.

**Acceptance Scenarios**:

1. **Given** a raw SMILES string from the USPTO dataset representing a valid organic reaction, **When** the parsing module processes it, **Then** the system generates a molecular graph with correctly assigned atom types, bond orders, and reaction center annotations.
2. **Given** a batch of input SMILES strings, **When** the ingestion pipeline runs, **Then** at least 95% of the strings are successfully converted to graph structures, and the remaining failures are logged with the specific error reason.
3. **Given** a parsed graph, **When** the feature extraction module runs, **Then** the resulting node features include atomic number, formal charge, and hybridization, and edge features include bond type, all formatted for CPU-based matrix operations.

---

### User Story 2 - Baseline and GNN Model Training (Priority: P2)

The system MUST train a lightweight Message Passing Neural Network (MPNN) and a Random Forest baseline on the constructed dataset to predict reaction yield, ensuring the process completes within the CPU-only resource limits.

**Why this priority**: This implements the core comparative analysis. It allows the research to determine if GNN-derived embeddings offer any advantage over traditional descriptors, which is the primary hypothesis.

**Independent Test**: Can be tested by running the 5-fold cross-validation training loop on the [deferred] training partition; the test passes if both models converge (loss decreases) and produce predictions within the valid yield range (0-100%) without crashing or exceeding memory limits, completing within 4 hours.

**Acceptance Scenarios**:

1. **Given** a training dataset split ([deferred] for 5-fold CV, [deferred] held-out test), **When** the MPNN model trains for 50 epochs across 5 folds, **Then** the validation loss decreases monotonically after the initial epochs, and the model completes the 5-fold CV training phase within 4 hours on a 2-core CPU runner.
2. **Given** the same training data, **When** the Random Forest baseline (using Morgan fingerprints) trains across 5 folds, **Then** it completes the 5-fold CV training phase within 30 minutes and produces a baseline R² score for comparison.
3. **Given** the trained models, **When** evaluated on the held-out test set, **Then** the system outputs R², MAE, and RMSE metrics for both the GNN and the baseline, formatted in a structured JSON report.

---

### User Story 3 - Statistical Comparison and Sensitivity Analysis (Priority: P3)

The system MUST perform a statistical comparison between the GNN and baseline models, including a sensitivity analysis on the noise tolerance and a subgraph-level attribution test to identify key structural features.

**Why this priority**: This addresses the research question directly by quantifying the "improvement" and identifying "which structural features" matter. It validates the scientific contribution of the GNN approach.

**Independent Test**: Can be tested by running the analysis script on the test set predictions; the test passes if it generates a report showing the R² improvement (or lack thereof), a sensitivity sweep result, and a ranked list of important features.

**Acceptance Scenarios**:

1. **Given** the test set predictions from both models, **When** the comparison module runs, **Then** it calculates the relative error reduction and reports if the GNN improvement exceeds the [deferred] relative error reduction target defined in Assumptions (or flags if it does not).
2. **Given** the GNN model weights, **When** the GNNExplainer attribution analysis runs, **Then** it outputs a ranked list of the top subgraph patterns contributing to prediction accuracy.
3. **Given** a noise tolerance parameter for yield prediction, **When** the sensitivity analysis runs, **Then** it sweeps the tolerance over a range of values of the target yield and reports how the Mean Absolute Error (MAE) varies across these values.

### Edge Cases

- What happens when the USPTO dataset contains SMILES strings with stereochemistry that RDKit cannot parse? (System logs the error and skips the entry, maintaining the [deferred] success rate target defined in FR-001).
- How does the system handle reactions with missing yield data (NaN values)? (System excludes these entries from the training set before splitting).
- What happens if the training loss does not decrease after 10 epochs? (System triggers an early stopping mechanism to prevent wasted compute).
- How does the system handle the scenario where the GNN model performs worse than the baseline? (System reports this as a null result, documenting the R² difference and potential causes).

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse SMILES strings into molecular graphs using RDKit, extracting atom/bond features and reaction center annotations, ensuring at least 95% of a reproducible random sample of reactions from the USPTO dataset is successfully processed (See US-001).
- **FR-002**: System MUST implement a Message Passing Neural Network (MPNN) architecture compatible with CPU-only execution (no CUDA/GPU), training for a maximum of 50 epochs with early stopping enabled, and training the 5-fold CV models must complete within 4 hours total (See US-002).
- **FR-003**: System MUST train a Random Forest baseline model using Morgan fingerprints and molecular descriptors (MW, logP, TPSA) to serve as a comparative benchmark (See US-002).
- **FR-004**: System MUST compute and report R², MAE, and RMSE metrics for both the GNN and baseline models on a held-out test set ([deferred] of the dataset) (as defined in US-002 AS-3) (See US-002).
- **FR-005**: System MUST perform a sensitivity analysis on the noise tolerance parameter by sweeping values over {[deferred], [deferred], [deferred]} of the target yield and reporting the variation in MAE, justified as essential rigor to assess robustness against experimental noise in chemical yield datasets (See US-003).
- **FR-006**: System MUST execute the entire pipeline (ingestion, 5-fold CV training, final evaluation) within 10 hours on a standard GitHub Actions free-tier runner (ubuntu-latest, CPU, ~7 GB RAM) (See US-002).
- **FR-007**: System MUST apply 5-fold cross-validation on the [deferred] training partition (excluding the [deferred] held-out test set) to assess generalization and ensure the R² improvement claim is robust, in compliance with Constitution Principle I (Reproducibility) and Principle VII (Uncertainty Quantification), reporting mean R² and standard deviation of R² scores across folds (≤ 0.05) (See US-003).
- **FR-008**: System MUST perform subgraph-level attribution using GNNExplainer to identify key structural patterns contributing to prediction accuracy (See US-003).

### Key Entities

- **MolecularGraph**: Represents a molecule with nodes (atoms) and edges (bonds), containing features like atomic number, charge, and bond type.
- **ReactionDataset**: A collection of MolecularGraphs paired with a continuous yield value (0-100) and a reaction class label.
- **PredictionResult**: A record containing the predicted yield, actual yield, error metrics, and the model type used (GNN or Baseline).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The R² improvement of the GNN model over the Random Forest baseline is measured against the [deferred] relative error reduction target defined in Assumptions to determine if the GNN approach provides value (See FR-004, US-003).
- **SC-002**: The computational cost of the entire analysis is measured against the 10-hour limit on a 2-core CPU runner to ensure feasibility (See FR-006, US-002).
- **SC-003**: The sensitivity of the prediction to noise tolerance is measured by the variation in MAE across the sweep {[deferred], [deferred], [deferred]} to validate robustness (See FR-005, US-003).
- **SC-004**: The data parsing success rate is measured against the [deferred] target defined in FR-001 to ensure dataset integrity (See FR-001, US-001).
- **SC-005**: The generalization performance is measured by the standard deviation of R² scores across the 5 folds of cross-validation to ensure stability (See FR-007, US-003).

## Assumptions

- The USPTO reaction dataset (or equivalent public source) contains sufficient reaction yield data and SMILES strings to train a model with at least 10,000 examples, allowing for a valid standard split (majority for CV, held-out).
- The "reaction yield" variable in the dataset is continuous and normalized to the 0-100 range, or can be easily normalized without losing information.
- The molecular graphs derived from SMILES strings contain all necessary chemical information (atom types, bond orders) to predict yield, without requiring 3D conformational data which is computationally expensive.
- The PyTorch Geometric library and RDKit are available and compatible with the CPU-only environment of the GitHub Actions runner.
- The "reaction class" labels in the dataset are consistent and can be used for stratified splitting.
- The correlation between molecular graph topology and reaction yield is non-zero, meaning the data contains signal that a model can learn.
- A [deferred] relative error reduction is a defensible community standard for "practical significance" in this specific sub-field of computational chemistry, as R² is dataset-dependent and relative error is a more robust metric for yield prediction.
- Typical experimental noise margins in chemical yield datasets are non-negligible., justifying the sensitivity analysis sweep values.