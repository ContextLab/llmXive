# Feature Specification: Predicting Amine Reactivity Using Graph Neural Networks and Public Databases

**Feature Branch**: `001-predicting-amine-reactivity`  
**Created**: 2026-07-09  
**Status**: Draft  
**Input**: User description: "Predicting Amine Reactivity Using Graph Neural Networks and Public Databases"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

The researcher must be able to download SN2 reaction data for primary and secondary amines from public repositories (ChEMBL, PubChem), filter for kinetic data, and convert these molecules into heterogeneous graphs with atom/bond features and calculated partial charges.

**Why this priority**: This is the foundational step; without a clean, structured dataset of molecular graphs linked to experimental rates, no modeling or analysis can occur. It validates the "Dataset-variable fit" by ensuring the raw data contains the necessary variables (reactant structure, rate constant).

**Independent Test**: The pipeline can be run end-to-end on a subset of data to produce a JSON/CSV file containing molecular graphs (node/edge attributes) and corresponding log(rate) values, with no missing values for required fields.

**Acceptance Scenarios**:

1. **Given** the ChEMBL and PubChem APIs are accessible, **When** the ingestion script runs with filters for "primary/secondary amines" and "SN2 reactions with kinetic data", **Then** the output dataset contains at least 500 valid reaction records with complete SMILES, kinetic constants, and calculated partial charges.
2. **Given** a dataset containing reactions with missing kinetic data, **When** the ingestion script filters the data, **Then** those records are excluded, and a log reports the count of excluded records without crashing the pipeline.
3. **Given** a valid SMILES string for a primary amine, **When** the graph construction module processes it, **Then** the output graph includes node features for atom type, hybridization, and Gasteiger partial charge, and edge features for bond order.

---

### User Story 2 - Baseline and GNN Model Training (Priority: P2)

The researcher must be able to train a baseline linear model (using traditional descriptors) and a Graph Neural Network (GNN) on the constructed dataset, ensuring both models run to completion within the CPU-only compute limits and produce predictions on a held-out test set.

**Why this priority**: This delivers the core predictive capability. It allows for the initial comparison of GNN vs. traditional methods and validates the "Compute feasibility" constraint (CPU-only, <6h runtime).

**Independent Test**: The training script executes successfully on a standard CPU environment, producing two model artifacts (baseline and GNN) and a test set prediction file with Mean Absolute Error (MAE) and R² metrics for both.

**Acceptance Scenarios**:

1. **Given** a pre-processed dataset of molecular graphs, **When** the training pipeline runs with a 70/15/15 split and a scaffold-based split strategy, **Then** both the baseline (Random Forest/Linear) and GNN models complete training within 4 hours on a 2-core CPU environment.
2. **Given** a trained GNN model, **When** it predicts log(rate) for the test set, **Then** the output includes a prediction for every test sample without NaN values or shape mismatches.
3. **Given** the test set predictions, **When** the evaluation script runs, **Then** it outputs the R² and MAE for both the GNN and the baseline model, formatted for immediate comparison.

---

### User Story 3 - Interpretability and Feature Analysis (Priority: P3)

The researcher must be able to apply interpretability methods (SHAP or attention weights) to the GNN predictions to rank atomic/subgraph features by their contribution to reactivity and visualize the top contributors.

**Why this priority**: This addresses the "Research Question" directly (identifying *which* features determine reactivity) rather than just predicting the rate. It transforms the model from a black box into a scientific tool.

**Independent Test**: The interpretability script runs on the trained GNN, producing a ranked list of features (e.g., "alpha-carbon steric bulk", "nitrogen hybridization") and a visualization file (e.g., SVG/PNG) highlighting the most influential substructures.

**Acceptance Scenarios**:

1. **Given** a trained GNN model and a test set, **When** the SHAP analysis runs, **Then** it produces a ranked list of atomic features where the top 5 features correspond to known chemical intuition (e.g., steric hindrance, electronic effects).
2. **Given** the SHAP values, **When** the visualization module generates a plot, **Then** it highlights the specific atoms in the molecular graph that contribute most positively or negatively to the predicted rate.
3. **Given** the feature rankings, **When** the correlation analysis runs, **Then** it calculates the Pearson correlation coefficient between the GNN-derived feature importance and the known pKa values, outputting the correlation coefficient (r).

---

### Edge Cases

- **What happens when the dataset is too large?** If the raw data exceeds 7 GB RAM, the system MUST automatically sample a subset (e.g., a representative number of reactions) to fit the memory constraints, logging the sampling strategy.
- **How does the system handle heterophilous graphs?** If the GNN fails to converge on graphs with high heterophily (reactants vs. transition states), the system MUST fallback to a standard GraphSAGE architecture or log a warning that the heterophily-aware mechanism was skipped.
- **What happens if a SMILES string is invalid?** The ingestion script MUST skip invalid SMILES strings, log the error with the record ID, and continue processing without halting the entire pipeline.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download reaction data from ChEMBL and PubChem APIs, filtering for primary/secondary amines and SN2 reactions with reported kinetic data (k or t1/2). (See US-1)
- **FR-002**: The system MUST construct heterogeneous molecular graphs using RDKit, including node features (atom type, hybridization, Gasteiger partial charge) and edge features (bond order). (See US-1)
- **FR-003**: The system MUST implement a 3-layer GNN (GraphSAGE or GAT) that trains on CPU without GPU acceleration, using a 70/15/15 scaffold-based split. (See US-2)
- **FR-004**: The system MUST train a baseline model using traditional descriptors (pKa, MW, steric parameters) for performance comparison against the GNN. (See US-2)
- **FR-005**: The system MUST apply SHAP analysis to the GNN predictions to rank atomic features and subgraphs by their contribution to the predicted reaction rate. (See US-3)
- **FR-006**: The system MUST perform a paired t-test on the absolute errors of the GNN vs. the baseline model to determine statistical significance (p < 0.05). (See US-2)
- **FR-007**: The system MUST log all data exclusions (e.g., missing kinetic data, invalid SMILES) to a separate audit file for reproducibility. (See US-1)
- **FR-008**: The system MUST enforce a maximum training time of a reasonable duration per job and a memory limit of 7 GB RAM., triggering a graceful exit or sampling if exceeded. (See US-2)

### Key Entities

- **ReactionRecord**: Represents a single SN2 reaction, containing reactant SMILES, product SMILES, kinetic constant (k), and experimental conditions.
- **MolecularGraph**: A heterogeneous graph representation of a reactant, with nodes (atoms) and edges (bonds) containing feature vectors.
- **ModelArtifact**: A serialized representation of a trained model (baseline or GNN) including hyperparameters and training metrics.
- **FeatureImportance**: A ranked list of atomic or subgraph features derived from SHAP analysis, linked to specific reaction predictions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The GNN model's R² score on the test set is measured against the baseline linear model's R² score (See FR-004, US-2).
- **SC-002**: The statistical significance of the GNN's improvement over the baseline is measured against a paired t-test p-value threshold. (See FR-006, US-2).
- **SC-003**: The correlation between GNN-derived feature importance and known electronic descriptors (e.g., pKa) is measured against a substantial Pearson correlation coefficient (r) threshold. (See FR-005, US-3).
- **SC-004**: The memory usage of the training pipeline is measured against the standard RAM limit of the GitHub Actions free-tier runner. (See FR-008, US-2).
- **SC-005**: The total training time for both baseline and GNN models is measured against the job limit of the GitHub Actions free-tier runner. (See FR-008, US-2).
- **SC-006**: The completeness of the dataset is measured against the requirement that all retained records have valid SMILES and kinetic data. (See FR-001, US-1).

## Assumptions

- The ChEMBL and PubChem REST APIs will remain accessible and rate-limited sufficiently to allow data download within the 6-hour window.
- The RDKit library will be available in the GitHub Actions environment with pre-installed dependencies for Gasteiger partial charge calculation.
- The "heterophily" in reaction graphs (differences between reactants and transition states) can be adequately modeled by a standard 3-layer GNN or a GraphSAGE variant without requiring specialized, GPU-accelerated architectures.
- The experimental kinetic data (k or t1/2) in public databases is sufficiently standardized (e.g., same units, temperature) to allow direct comparison without complex normalization that exceeds CPU capabilities.
- The sample size of available SN2 reactions with kinetic data in public databases is sufficient (>500 records) to train a GNN without severe overfitting; if not, the project will rely on the `[NEEDS CLARIFICATION: does the dataset contain enough samples?]` marker.
- The SHAP analysis on the GNN model will be computationally feasible on a 2-core CPU within the remaining time budget after model training.
- The "primary and secondary amines" scope is well-defined by the SMILES patterns in the dataset, and no manual curation of reaction mechanisms is required beyond the automated filtering.
