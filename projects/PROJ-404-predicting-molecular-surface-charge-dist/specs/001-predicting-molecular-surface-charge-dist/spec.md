# Feature Specification: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

**Feature Branch**: `001-predict-molecular-surface-charge`  
**Created**: 2026-07-20  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations"

## User Scenarios & Testing

### User Story 1 - Data Pipeline Construction and Validation (Priority: P1)

The system MUST ingest a defined sample of the QM9 dataset (specifically the subset containing Merz-Kollman charges), extract atomic coordinates, bond connectivity, and ESP-derived partial charges, and validate that the data fits within the 7 GB RAM constraint of the free-tier runner.

**Why this priority**: Without a validated, memory-efficient dataset pipeline, no model training or evaluation can occur. This is the foundational step for the entire research question.

**Independent Test**: The system can be fully tested by executing the data loading script on the free-tier runner, confirming the dataset loads into memory without OOM errors, and verifying that the extracted features (atomic number, coordinates, charges) match the expected schema and value ranges.

**Acceptance Scenarios**:

1. **Given** the QM9 dataset (subset with Merz-Kollman charges) is available in the repository, **When** the data loading script executes on a CPU-only runner with 7 GB RAM, **Then** the script must load the defined sample into memory without triggering an Out-Of-Memory (OOM) error, and output a summary of the loaded feature dimensions.
2. **Given** the loaded dataset, **When** a validation check is performed, **Then** every molecule must have a non-null Merz-Kollman charge value for every atom, and the number of atoms per molecule must align with the provided connectivity graph.

---

### User Story 2 - Geometric Graph Neural Network Training (Priority: P2)

The system MUST implement a Geometric Message Passing Neural Network (e.g., SchNet or DimeNet) using PyTorch Geometric, train it on the processed dataset using CPU-only constraints, and output the trained model weights and training logs.

**Why this priority**: This is the core mechanism to answer the research question. It tests whether structural descriptors can learn the structure-to-charge mapping. It is independent of the final evaluation metrics but relies on the data pipeline.

**Independent Test**: The system can be tested by running the training script for a fixed number of epochs and verifying that the loss decreases, the model weights are saved to disk, and the process completes within the 6-hour wall-clock limit.

**Acceptance Scenarios**:

1. **Given** a pre-processed dataset and a defined model architecture, **When** the training script runs on a CPU-only runner, **Then** the training loop must complete at least 10 epochs within 6 hours, and the final epoch loss must be strictly less than the initial epoch loss.
2. **Given** the training process, **When** the model is saved, **Then** the output artifact must be a valid PyTorch state dictionary containing all learned parameters, and the file size must be less than 500 MB to ensure storage feasibility.

---

### User Story 3 - Evaluation and Baseline Comparison (Priority: P3)

The system MUST evaluate the trained model against a held-out test set and a connectivity-only GNN baseline (2D graph without 3D coordinates), calculating MAE, RMSE, and Pearson correlation ($R$) to determine if the 3D GNN outperforms the 2D baseline.

**Why this priority**: This delivers the final answer to the research question. It validates the hypothesis that structural features (specifically 3D geometry) are predictive of ESP distributions beyond simple connectivity.

**Independent Test**: The system can be tested by loading the trained model and test set, running inference, and generating a report containing the MAE, RMSE, and $R$ values, comparing them directly to the baseline performance.

**Acceptance Scenarios**:

1. **Given** a trained model and a held-out test set, **When** the evaluation script runs, **Then** it must output a report containing the Mean Absolute Error (MAE) and Pearson correlation coefficient ($R$) for the GNN predictions.
2. **Given** the same test set, **When** the connectivity-only GNN baseline is computed, **Then** the 3D GNN's MAE must be lower than the baseline's MAE to confirm the model learned structural context from 3D geometry. If the GNN's MAE is not lower than the baseline, the system must log a failure code (EXIT_CODE_BASELINE_LOSS) and terminate without generating a final report.

---

### Edge Cases

- What happens when a molecule in the dataset has an undefined bond order or missing coordinates? (System must filter or impute with a defined strategy).
- How does the system handle molecules that exceed the 7 GB RAM limit when loaded in full? (System must implement chunking or sampling).
- How does the system handle a scenario where the model fails to converge (loss increases or plateaus immediately)? (System must trigger early stopping and report the failure).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load a defined sample of the QM9 dataset (specifically the subset containing Merz-Kollman charges) and extract atomic coordinates, bond connectivity, and ESP-derived partial charges for all molecules, ensuring the total memory footprint remains ≤ 7 GB during execution. The system must approximate the DFT-derived charge fit (regression task), acknowledging that the ground truth is a deterministic function of the input geometry in the DFT framework (See US-1).
- **FR-002**: System MUST implement a Geometric Message Passing Neural Network (GNN) architecture (e.g., SchNet or DimeNet) capable of processing 3D molecular graphs and outputting a scalar charge prediction for each atom (See US-2).
- **FR-003**: System MUST train the GNN using a CPU-only environment, utilizing the Adam optimizer with a learning rate of 1e-3, for a maximum of 100 epochs with early stopping based on validation MAE with a patience of 10 epochs (See US-2).
- **FR-004**: System MUST perform a scaffold-based split (Bemis-Murcko) using RDKit's Bemis-Murcko scaffold extraction with a fixed random seed of 42 to partition the data into [deferred] train, [deferred] validation, and [deferred] test sets to ensure generalization to unseen molecular topologies (See US-2).
- **FR-005**: System MUST calculate and report the Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Pearson correlation coefficient ($R$) between predicted and ground-truth charges on the test set (See US-3).
- **FR-006**: System MUST implement a connectivity-only GNN baseline (2D graph without 3D coordinates) that assigns charges based on graph connectivity and compare its performance against the 3D GNN (See US-3).
- **FR-007**: System MUST report if the GNN's test MAE is ≤ 0.05 e to validate the research hypothesis (See US-3).

### Key Entities

- **Molecule**: Represents a chemical entity with attributes including atomic numbers, 3D coordinates, bond connectivity, and a ground-truth ESP-derived partial charge vector.
- **Model**: Represents the trained GNN instance, including architecture configuration and learned parameters.
- **Prediction**: Represents the output of the model, a vector of predicted scalar charges corresponding to the atoms in a molecule.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the GNN predictions is measured against the ground-truth ESP-derived partial charges derived from the DFT calculations in the QM9 dataset (See FR-005, US-3).
- **SC-002**: The Pearson correlation coefficient ($R$) between predicted and actual charges is measured against the theoretical maximum of 1.0 to assess linear relationship strength (See FR-005, US-3).
- **SC-003**: The performance improvement of the 3D GNN over the connectivity-only GNN baseline is measured by the difference in MAE between the two models on the test set (See FR-006, US-3).
- **SC-004**: The total wall-clock training time is measured against the 6-hour limit of the free-tier GitHub Actions runner to ensure feasibility (See FR-003, US-2).
- **SC-005**: The peak memory usage during data loading and training is measured against the 7 GB RAM constraint of the free-tier runner (See FR-001, US-1).
- **SC-006**: The generalization capability is measured by the difference in MAE between the test set and the validation set to detect generalization error to unseen scaffolds (See FR-004, US-2).
- **SC-007**: Generalization error to unseen scaffolds is measured by the difference in MAE between the training set and the validation set to detect overfitting to the training distribution (See FR-004, US-2).
- **SC-008**: The research hypothesis is validated if the GNN's test MAE is ≤ 0.05 e (See FR-007, US-3).

## Assumptions

- The QM9 dataset subset used must contain pre-computed Merz-Kollman charges; if the standard release lacks this, a secondary DFT calculation step is required to generate the ground truth, impacting the 'CPU-only' feasibility constraint.
- The free-tier GitHub Actions runner (multiple CPU cores, adequate RAM) is sufficient to process the QM dataset (a substantial collection of molecules) if the dataset is loaded efficiently or sampled, without requiring GPU acceleration.
- The relationship between molecular geometry and ESP-derived partial charges is sufficiently learnable by a GNN without requiring explicit electron density inputs, relying on the assumption that 3D coordinates and bond types encode the necessary electronic environment.
- The "scaffold-based split" implementation (e.g., using RDKit) will correctly identify Bemis-Murcko scaffolds and partition the dataset without introducing data leakage between train and test sets.
- The GNN architecture (SchNet/DimeNet) available in PyTorch Geometric will run in default precision (float32) on CPU without requiring CUDA-specific optimizations or quantization libraries.
- The goal is to approximate the DFT-derived charge fit (regression task), acknowledging that the ground truth is a deterministic function of the input geometry in the DFT framework, and the model is evaluated on its ability to reproduce this fit efficiently.