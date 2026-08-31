# Feature Specification: Predicting Amine Reactivity Using Graph Neural Networks and Public Databases

**Feature Branch**: `001-predicting-amine-reactivity`  
**Created**: 2026-07-09  
**Status**: Draft  
**Input**: User description: "Predicting Amine Reactivity Using Graph Neural Networks and Public Databases"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

The researcher must be able to download SN2 reaction data for primary and secondary amines from public repositories (ChEMBL, PubChem), filter for kinetic data, normalize kinetic values to standard conditions, and convert these molecules into heterogeneous graphs with atom/bond features and calculated partial charges.

**Why this priority**: This is the foundational step; without a clean, structured dataset of molecular graphs linked to experimental rates (normalized for temperature/solvent), no modeling or analysis can occur. It validates the "Dataset-variable fit" by ensuring the raw data contains the necessary variables (reactant structure, rate constant).

**Independent Test**: The pipeline can be run end-to-end on a subset of data to produce a JSON/CSV file containing molecular graphs (node/edge attributes), normalized log(rate) values, and calculated pKa values, with no missing values for required fields.

**Acceptance Scenarios**:

1. **Given** the ChEMBL and PubChem APIs are accessible, **When** the ingestion script runs with filters for "primary/secondary amines" and "SN2 reactions with kinetic data", **Then** the output dataset contains at least 500 valid reaction records with complete SMILES, normalized kinetic constants, and calculated partial charges.
2. **Given** a dataset containing reactions with missing kinetic data or missing temperature for normalization, **When** the ingestion script filters the data, **Then** those records are excluded, and a log reports the count of excluded records without crashing the pipeline.
3. **Given** a valid SMILES string for a primary amine, **When** the graph construction module processes it, **Then** the output graph includes node features for atom type, hybridization, Gasteiger partial charge, and pKa, and edge features for bond order.

---

### User Story 2 - Baseline and GNN Model Training (Priority: P2)

The researcher must be able to train a baseline linear model (using traditional descriptors including pKa) and a Graph Neural Network (GNN) on the constructed dataset, ensuring both models run to completion within the CPU-only compute limits and produce predictions on a held-out test set.

**Why this priority**: This delivers the core predictive capability. It allows for the initial comparison of GNN vs. traditional methods and validates the "Compute feasibility" constraint (CPU-only, <6h runtime).

**Independent Test**: The training script executes successfully on a standard CPU environment, producing two model artifacts (baseline and GNN) and a test set prediction file with Mean Absolute Error (MAE) and R² metrics for both.

**Acceptance Scenarios**:

1. **Given** a pre-processed dataset of molecular graphs, **When** the training pipeline runs with a 70/15/15 split and a scaffold-based split strategy, **Then** both the baseline (Random Forest/Linear) and GNN models complete training within 6 hours on a 2-core CPU environment.
2. **Given** a trained GNN model, **When** it predicts log(rate) for the test set, **Then** the output includes a prediction for every test sample without NaN values or shape mismatches.
3. **Given** the test set predictions, **When** the evaluation script runs, **Then** it outputs the R² and MAE for both the GNN and the baseline model, formatted for immediate comparison.

---

### User Story 3 - Interpretability and Feature Analysis (Priority: P3)

The researcher must be able to apply interpretability methods (SHAP or attention weights) to the GNN predictions to rank atomic/subgraph features by their contribution to reactivity and visualize the top contributors against established chemical benchmarks.

**Why this priority**: This addresses the "Research Question" directly (identifying *which* features determine reactivity) rather than just predicting the rate. It transforms the model from a black box into a scientific tool.

**Independent Test**: The interpretability script runs on the trained GNN, producing a ranked list of features (e.g., "alpha-carbon steric bulk", "nitrogen hybridization") and a visualization file (e.g., SVG/PNG) highlighting the most influential substructures.

**Acceptance Scenarios**:

1. **Given** a trained GNN model and a test set, **When** the SHAP analysis runs, **Then** it produces a ranked list of atomic features where the top 5 features show a Pearson correlation coefficient (r) ≥ 0.6 with the independent descriptor vector composed of: Hammett σ_p, Hammett σ_m, Hammett σ+, Hammett σ-, Taft Es, Taft Es_s, Charton ν, Verloop B1, Verloop B5, and Molar Refractivity (MR).
2. **Given** the SHAP values, **When** the visualization module generates a plot, **Then** it highlights the specific atoms in the molecular graph that contribute most positively or negatively to the predicted rate.
3. **Given** the feature rankings, **When** the correlation analysis runs, **Then** it calculates the Pearson correlation coefficient between the aggregated SHAP importance score per reaction (sum of absolute SHAP values for the reaction center) and the independent descriptor vector across the dataset, ensuring the correlation is statistically significant (p < 0.05) and greater than the random baseline (shuffled labels).

---

### Edge Cases

- **What happens when the dataset is too large?** If the raw data exceeds available RAM, the system MUST automatically sample a subset (e.g., a representative number of reactions) to fit the memory constraints, logging the sampling strategy.
- **How does the system handle heterophilous graphs?** If the GNN fails to converge on graphs with high heterophily (reactants vs. transition states), the system MUST fallback to a heterophily-aware variant architecture (e.g., GAT with edge-type awareness or a dedicated heterophily layer) and log the switch.
- **What happens if a SMILES string is invalid?** The ingestion script MUST skip invalid SMILES strings, log the error with the record ID, and continue processing without halting the entire pipeline.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download reaction data from ChEMBL and PubChem APIs, filtering for primary/secondary amines and SN2 reactions with reported kinetic data (k or t1/2). The system MUST normalize all kinetic data to a standard state (e.g., standard temperature and pressure, 1M) using the Arrhenius or Eyring equation where temperature data is available. If activation energy (Ea) is missing, the system MUST use a reaction-class-specific average Ea (derived from the subset of records with Ea data) for normalization; if the class average is unavailable, the record MUST be flagged and excluded. (See US-1)
- **FR-002**: The system MUST construct heterogeneous molecular graphs using RDKit, including node features (atom type, hybridization, Gasteiger partial charge, and pKa calculated via RDKit or fetched from ChEMBL) and edge features (bond order). (See US-1)
- **FR-003**: The system MUST implement a multi-layer GNN (GraphSAGE or GAT) that trains on CPU without GPU acceleration, using a 70/15/15 scaffold-based split. The architecture MUST include a heterophily-aware aggregation mechanism (e.g., GAT with edge-type awareness) as the primary or fallback method. (See US-2)
- **FR-004**: The system MUST train a baseline model using traditional descriptors (pKa, MW, steric parameters like Taft Es) for performance comparison against the GNN. (See US-2)
- **FR-005**: The system MUST apply SHAP analysis to the GNN predictions to rank atomic features and subgraphs by their contribution to the predicted reaction rate. (See US-3)
- **FR-006**: The system MUST perform a permutation test or a bootstrap-based 95% confidence interval on the absolute errors of the GNN vs. the baseline model to determine statistical significance, accounting for scaffold-induced correlation. (See US-2)
- **FR-007**: The system MUST log all data exclusions (e.g., missing kinetic data, invalid SMILES, missing temperature for normalization, missing Ea with no class average) to a separate audit file for reproducibility. (See US-1)
- **FR-008**: The system MUST enforce a maximum training time and a memory limit per job, triggering a graceful exit or sampling if exceeded. (See US-2)

### Key Entities

- **ReactionRecord**: Represents a single SN2 reaction, containing reactant SMILES, product SMILES, kinetic constant (k) normalized to standard conditions, experimental temperature, and calculated pKa.
- **MolecularGraph**: A heterogeneous graph representation of a reactant, with nodes (atoms) and edges (bonds) containing feature vectors.
- **ModelArtifact**: A serialized representation of a trained model (baseline or GNN) including hyperparameters and training metrics.
- **FeatureImportance**: A ranked list of atomic or subgraph features derived from SHAP analysis, linked to specific reaction predictions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The GNN model's R² score on the test set is measured against the baseline linear model's R² score (See FR-004, US-2).
- **SC-002**: The statistical significance of the GNN's improvement over the baseline is measured against a permutation test or bootstrap CI p-value threshold of p < 0.05. (See FR-006, US-2).
- **SC-003**: The correlation between GNN-derived feature importance (aggregated per reaction) and the independent descriptor vector (Hammett/Taft/Charton/Verloop/MR) is measured against a statistical significance threshold of p < 0.05 and a requirement that the correlation coefficient is significantly greater than the random baseline (shuffled labels). (See FR-005, US-3).
- **SC-004**: The memory usage of the training pipeline is measured against the standard RAM limit of the GitHub Actions free-tier runner.. (See FR-008, US-2).
- **SC-005**: The total training time for both baseline and GNN models is measured against the job limit of the GitHub Actions free-tier runner.. (See FR-008, US-2).
- **SC-006**: The completeness of the dataset is measured against the requirement that all retained records have valid SMILES, normalized kinetic data, and a calculated pKa that is a finite float value (not NaN or Inf), with the calculation method logged. (See FR-001, US-1).

## Assumptions

- The ChEMBL and PubChem REST APIs will remain accessible and rate-limited sufficiently to allow data download within the 6-hour window.
- The RDKit library will be available in the GitHub Actions environment with pre-installed dependencies for Gasteiger partial charge and pKa calculation.
- The "heterophily" in reaction graphs (differences between reactants and transition states) can be adequately modeled by a heterophily-aware GNN variant (e.g., GAT with edge-type awareness) without requiring specialized, GPU-accelerated architectures.
- The experimental kinetic data (k or t1/2) in public databases contains sufficient temperature metadata to allow normalization to a standard state

The research question is to determine the thermodynamic properties of the system. The method involves normalization to a standard state. References include [Citation]. using the Arrhenius or Eyring equation, or sufficient data exists to calculate a reliable reaction-class-specific average Ea.
- The sample size of available SN reactions with kinetic data in public databases is sufficient for GNN training; If the retrieved count is insufficient, the system will rely on data augmentation or transfer learning strategies as a fallback., rather than halting.
- The SHAP analysis on the GNN model will be computationally feasible on a 2-core CPU within the remaining time budget after model training.
- The "primary and secondary amines" scope is well-defined by the SMILES patterns in the dataset, and no manual curation of reaction mechanisms is required beyond the automated filtering.
- The independent descriptor vector (Hammett σ, Taft Es, etc.) used for validation is derived from established chemical literature and does not require real-time calculation during the validation step.