# Feature Specification: Predicting Molecular Permeability Coefficients via Graph Neural Networks

**Feature Branch**: `001-predict-molecular-permeability`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Permeability Coefficients via Graph Neural Networks and Public Datasets"

## User Scenarios & Testing

### User Story 1 - Dataset Ingestion and Graph Construction (Priority: P1)

The system MUST successfully ingest public molecular permeability datasets (from NIST, PubChem, MTR), parse SMILES strings into molecular graphs using RDKit, and compute baseline physicochemical descriptors (MW, logP, PSA, rotatable bonds) for at least 500 unique compounds.

**Why this priority**: This is the foundational step. Without a clean, parsed dataset with both graph representations and baseline descriptors, no model training or comparison is possible. It delivers the primary data asset required for the research.

**Independent Test**: The pipeline can be executed end-to-end on a representative sample of SMILES strings, producing a CSV file containing the molecular graph adjacency lists and a JSON object of baseline descriptors, with no missing values for the target permeability coefficient.

**Acceptance Scenarios**:

1. **Given** a raw CSV file containing SMILES strings and permeability coefficients from a public source, **When** the ingestion script runs, **Then** it outputs a processed dataset where every row contains a valid RDKit Mol object and a dictionary of 4 baseline descriptors.
2. **Given** a SMILES string representing a molecule with no experimental permeability data, **When** the ingestion script processes it, **Then** the record is flagged or excluded, and the system logs the specific reason (e.g., "Missing target variable") without crashing.
3. **Given** a dataset with 2000 compounds, **When** the graph construction runs on a CPU-only environment with 7GB RAM, **Then** the process completes within 15 minutes and the resulting graph data structure fits within 2GB of memory.

---

### User Story 2 - GNN Model Training and Baseline Comparison (Priority: P2)

The system MUST train a 3-layer Graph Convolutional Network (GCN) with ≤500K parameters on the molecular graphs and compare its performance against Random Forest and Linear Regression models trained on the baseline descriptors using 5-fold cross-validation.

**Why this priority**: This is the core research hypothesis test. It directly addresses whether GNNs outperform traditional descriptors. It delivers the primary experimental result (R², MAE, RMSE) required to answer the research question.

**Independent Test**: The training pipeline executes on a CPU-only runner, completing 5-fold cross-validation for all three models, and outputs a summary report containing the mean and standard deviation of R², MAE, and RMSE for each model type.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset of 500+ molecules, **When** the training script runs with a fixed random seed, **Then** it produces a CSV of predictions for the test fold of each of the 5 splits, allowing calculation of performance metrics.
2. **Given** a model training run that exceeds 2 hours on the CPU, **When** the process is monitored, **Then** it is automatically terminated and flagged as a performance regression, preventing resource exhaustion.
3. **Given** the performance metrics from the GNN and the Random Forest baseline, **When** the comparison report is generated, **Then** it explicitly states whether the GNN's mean R² is statistically significantly higher (p < 0.05) than the baseline.

---

### User Story 3 - Sensitivity Analysis and Uncertainty Quantification (Priority: P3)

The system MUST perform a sensitivity analysis on the model's prediction confidence intervals by sweeping a decision threshold and applying permutation importance to identify key molecular substructures influencing permeability.

**Why this priority**: This addresses the methodological soundness requirements (threshold justification, sensitivity, and interpretability). It ensures the findings are robust and provides insight into the "why" behind the predictions, which is critical for scientific validity.

**Independent Test**: The analysis script runs on the trained GNN model, generating a plot of prediction error vs. threshold sensitivity and a ranked list of atoms/bonds by permutation importance.

**Acceptance Scenarios**:

1. **Given** a trained GNN model, **When** the sensitivity analysis runs with a threshold sweep of {0.01, 0.05, 0.1} on the prediction interval width, **Then** it outputs a table showing how the false-positive rate and false-negative rate vary across these thresholds.
2. **Given** a dataset where specific molecular substructures are known to influence permeability, **When** the permutation importance analysis runs, **Then** it correctly ranks those substructures higher than random noise in the top [deferred] of importance scores.
3. **Given** a model trained on an observational dataset, **When** the final report is generated, **Then** all conclusions regarding structure-permeability relationships are explicitly framed as "associational" rather than "causal" in the text output.

### Edge Cases

- What happens when the public dataset contains duplicate SMILES strings with conflicting permeability values? (System must average values or flag for manual review).
- How does the system handle molecules with SMILES strings that RDKit cannot parse (e.g., invalid valency)? (System must log the error and exclude the molecule, reporting the exclusion rate).
- How does the system handle a dataset where the target variable (permeability) has a highly skewed distribution? (System must apply a log-transform or use a robust loss function as specified in Assumptions).
- What happens if the GNN training loss fails to converge after a predefined number of epochs? (System must flag the run as unstable and report the final loss value).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest public datasets (NIST, PubChem, MTR) containing SMILES strings and permeability coefficients, parsing them into molecular graphs and baseline descriptors (See US-1).
- **FR-002**: System MUST implement a 3-layer Graph Convolutional Network (GCN) with a parameter count not exceeding 500,000 to ensure CPU feasibility (See US-2).
- **FR-003**: System MUST execute 5-fold cross-validation for both the GNN and baseline models (Random Forest, Linear Regression) to generate performance metrics (R², MAE, RMSE) (See US-2).
- **FR-004**: System MUST perform a sensitivity analysis by sweeping the prediction interval threshold over the set {0.01, 0.05, 0.1} and report the variation in error rates (See US-3).
- **FR-005**: System MUST compute and rank permutation importance scores for molecular substructures to identify features influencing permeability predictions (See US-3).
- **FR-006**: System MUST explicitly frame all reported structure-permeability relationships as "associational" rather than "causal" in the final output, given the observational nature of the data (See US-3).

### Key Entities

- **Molecule**: Represents a chemical compound with attributes: SMILES string, molecular graph (nodes/edges), baseline descriptors (MW, logP, etc.), and target permeability coefficient.
- **ModelRun**: Represents a single training instance with attributes: model type (GNN/RF/LR), hyperparameters, fold ID, performance metrics, and training duration.
- **SensitivityResult**: Represents the output of the threshold sweep with attributes: threshold value, false-positive rate, false-negative rate, and confidence interval width.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The GNN model's mean R² on the 5-fold cross-validation test set is measured against the Random Forest baseline R² to determine if the graph-based approach provides a statistically significant improvement (See FR-003).
- **SC-002**: The false-positive and false-negative rates are measured against the baseline error rates across the threshold sweep {0.01, 0.05, 0.1} to validate the robustness of the uncertainty estimates (See FR-004).
- **SC-003**: The total training and inference time for the 5-fold cross-validation process is measured against the 2-hour CPU time limit to ensure compute feasibility (See FR-002).
- **SC-004**: The permutation importance scores are measured against known chemical heuristics (e.g., high polarity usually reduces permeability) to validate the interpretability of the learned features (See FR-005).

## Assumptions

- The public datasets (NIST, PubChem, MTR) contain sufficient overlap between SMILES strings and experimentally measured permeability coefficients to form a training set of at least 500 unique compounds.
- The molecular graphs derived from SMILES strings capture all necessary structural information for permeability prediction, and missing variables (e.g., specific polymer-solute interaction parameters) are not the primary drivers of variance.
- The observational nature of the dataset (no random assignment of molecular structures) precludes causal inference; therefore, all findings will be interpreted as associations.
- The dataset size (500-2000 compounds) is sufficient to train a small GNN (≤500K parameters) without severe overfitting, given the use of 5-fold cross-validation and regularization.
- The `RDKit` library and `PyTorch Geometric` (CPU-only version) are available in the GitHub Actions free-tier environment and can be installed within the job limit.
- The permeability coefficient values in the public datasets are consistent in units (e.g., Barrer) or can be reliably converted to a single unit for training.
