# Feature Specification: Predicting Molecular Permeability of Polymers via Graph Neural Networks

**Feature Branch**: `001-predicting-molecular-permeability`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Permeability of Polymers via Graph Neural Networks"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

A researcher needs to load raw polymer data from the NIST Polymer Database and PubChem, convert SMILES strings into valid PolymerGraph objects with node/edge features, and verify that the resulting dataset contains no missing values for critical permeability measurements.

**Why this priority**: Without a clean, structured dataset, no model can be trained. This is the foundational step that validates the "Dataset-variable fit" requirement. If the source data lacks necessary variables (e.g., specific gas permeability coefficients), the project cannot proceed.

**Independent Test**: Can be fully tested by running the data ingestion script and verifying the output HDF5/Parquet file contains the expected number of records, valid PolymerGraph objects for the count of input rows, and a non-zero count of permeability values for the target gas (e.g., CO2).

**Acceptance Scenarios**:

1. **Given** a raw NIST CSV file containing polymer SMILES and CO2 permeability values, **When** the ingestion script processes the file, **Then** the output dataset must contain a PolymerGraph object for every row where the permeability value is ≥ 1.0 × 10⁻¹⁰ Barrer, and the log-transformed permeability must be stored as a float.
2. **Given** a PubChem entry with a polymer SMILES but missing permeability data, **When** the ingestion script processes the entry, **Then** the entry must be excluded from the final training set, and a warning log must record the exclusion reason.
3. **Given** a SMILES string that represents a non-polymer molecule (e.g., a small drug), **When** the script attempts to parse it, **Then** the system must flag it for manual review or exclusion based on a defined molecular weight threshold (e.g., < 1000 Da).

---

### User Story 2 - Model Training and Baseline Comparison (Priority: P2)

A data scientist needs to train a Graph Neural Network (GNN) with 2–3 layers and 64 hidden dimensions on the processed polymer graphs and compare its performance against a Random Forest baseline using Morgan fingerprints, ensuring the entire process runs within the CPU-only CI constraints.

**Why this priority**: This validates the core hypothesis that graph topology predicts permeability. The comparison against a baseline (Random Forest) is necessary to determine if the GNN adds value over simpler descriptors, addressing the "What is known" gap.

**Independent Test**: Can be fully tested by executing the training pipeline and verifying that the GNN achieves an R² > 0.0 (better than a dummy predictor) and that the Random Forest baseline is successfully computed on the same scaffold-split test set.

**Acceptance Scenarios**:

1. **Given** a scaffold-split dataset with [deferred] training and [deferred] testing, **When** the GNN is trained for 50 epochs on a CPU-only runner, **Then** the loss at epoch 50 must be strictly less than the loss at epoch 5, and the final validation loss must be lower than the initial loss.
2. **Given** the trained GNN and the Random Forest baseline, **When** both are evaluated on the held-out test set, **Then** the system must output a JSON report containing R², MAE, and Pearson correlation for both models.
3. **Given** a test set containing polymers with novel scaffolds not seen in training, **When** the models make predictions, **Then** the system must calculate the performance degradation (drop in R²) compared to the training set performance.

---

### User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

A reviewer needs to verify that the reported performance difference between the GNN and the baseline is statistically significant and that any decision thresholds (specifically the R² threshold used to define a "successful prediction") are robust to small perturbations.

**Why this priority**: This addresses the "Multiplicity & power" and "Threshold justification" methodological soundness requirements. Without statistical validation, the results are merely descriptive and not scientifically defensible.

**Independent Test**: Can be fully tested by running the statistical analysis script which performs a Wilcoxon signed-rank test on cross-validation folds and a sensitivity sweep on the R² threshold, outputting a p-value and a sensitivity curve.

**Acceptance Scenarios**:

1. **Given** 5-fold cross-validation results for both GNN and Random Forest, **When** the Wilcoxon signed-rank test is executed, **Then** the output must include a p-value, and if p < 0.05, the system must flag the GNN as statistically superior.
2. **Given** a defined success threshold for permeability prediction (e.g., R² > 0.3), **When** the sensitivity analysis sweeps the threshold across {0.25, 0.30, 0.35}, **Then** the system must report how the false-positive rate of "successful prediction" changes across these values.
3. **Given** a dataset with potentially collinear descriptors (e.g., molecular weight and number of heavy atoms) used in the Random Forest baseline, **When** the collinearity diagnostic runs, **Then** the system must report the Variance Inflation Factor (VIF) for all input descriptors of the baseline and flag any pair with VIF > 5.

### Edge Cases

- What happens when the NIST database contains duplicate entries for the same polymer with conflicting permeability values? (System must average values or flag for manual resolution).
- How does the system handle polymers with undefined stereochemistry in the SMILES string? (System must treat undefined bonds as single or exclude the entry if stereochemistry is critical for the specific gas).
- How does the system handle a scenario where the GNN training diverges due to numerical instability? (System must implement a gradient clipping mechanism with a fixed max norm of 1.0 and log the event).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load polymer data from NIST and PubChem, parse SMILES into molecular graphs using RDKit, and extract node features (atom type, hybridization) and edge features (bond type) for every entry with a valid permeability measurement (See US-1).
- **FR-002**: System MUST split the dataset using Murcko scaffold similarity to ensure that the test set contains polymer scaffolds not present in the training set, preventing data leakage (See US-2).
- **FR-003**: System MUST implement a message-passing GNN with 2–3 layers and 64 hidden dimensions, aggregating node embeddings via mean-pooling to predict log-permeability (See US-2).
- **FR-004**: System MUST train a Random Forest baseline using ECFP4 Morgan fingerprints and a linear regression baseline using RDKit descriptors on the exact same scaffold-split dataset for direct comparison (See US-2).
- **FR-005**: System MUST perform a Wilcoxon signed-rank test (α = 0.05) on the R² scores from 5-fold cross-validation to determine if the GNN performance is statistically significantly different from the Random Forest baseline (See US-3).
- **FR-006**: System MUST execute a sensitivity analysis sweeping the permeability prediction threshold across values {0.25, 0.30, 0.35} to report the stability of the "successful prediction" rate (See US-3).
- **FR-007**: System MUST compute Variance Inflation Factors (VIF) for all input descriptors used in the Random Forest baseline and report any pairs with VIF > 5 to ensure predictor collinearity does not invalidate the baseline's coefficient estimates (See US-3).

### Key Entities

- **PolymerGraph**: Represents a polymer molecule with nodes (atoms) and edges (bonds), containing features like atom type, hybridization, bond order, and conjugation.
- **PermeabilityRecord**: A data point linking a PolymerGraph to an experimental permeability coefficient (log-scaled) for a specific gas (e.g., CO2, O2).
- **ModelArtifact**: The serialized weights and architecture definition of a trained GNN or Random Forest model, including the training configuration and validation metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation (R²) between predicted and experimental log-permeability must exceed 0.0 on the held-out test set (See FR-003, US-2).
- **SC-002**: The statistical significance (p-value) of the performance difference between the GNN and the Random Forest baseline is measured against the Wilcoxon signed-rank test results from 5-fold cross-validation (See FR-005, US-3).
- **SC-003**: The stability of the prediction success rate is measured against the sensitivity sweep of the R² threshold across {0.25, 0.30, 0.35} (See FR-006, US-3).
- **SC-004**: The degree of predictor collinearity in the Random Forest baseline is measured against the Variance Inflation Factor (VIF) calculated for all input descriptors (See FR-007, US-3).
- **SC-005**: The computational feasibility is measured against the GitHub Actions free-tier job timeout limit (≤ 6 hours) and the constraint of running the full training and evaluation pipeline on a CPU-only runner with ≤ 7 GB RAM (See FR-002, US-2).

## Assumptions

- The NIST Polymer Database and PubChem contain a sufficient number of entries (≥ 500) with complete SMILES strings and at least one permeability measurement for a common gas (e.g., CO2) to train a basic GNN.
- The relationship between polymer graph structure and permeability is primarily associational (observational study), not causal, as the data is derived from historical experimental measurements without random assignment of polymer structures.
- The "graph topology" derived from 2D SMILES is a sufficient proxy for the 3D chain connectivity and free volume required to predict permeability, as 3D conformers are not available in the source databases.
- The computational resources of the GitHub Actions free-tier (2 CPU cores, ~7 GB RAM) are sufficient to train a small GNN (2-3 layers, 64 dims) on a dataset of ≤ 2,000 polymers within 6 hours.
- The permeability data in the source databases is normalized to a standard temperature or can be corrected to a standard temperature without significant loss of accuracy.
- The GNN architecture will use standard floating-point precision (float32) and will not utilize quantization or mixed-precision training, as these require GPU hardware not available in the target environment.