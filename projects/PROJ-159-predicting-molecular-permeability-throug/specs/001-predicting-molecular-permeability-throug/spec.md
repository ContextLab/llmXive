# Feature Specification: Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks

**Feature Branch**: `001-predict-molecular-permeability-gnn`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to automatically download, filter, and convert the CoRE MOF 2019, IZA Zeolite, and gas permeability datasets into a unified graph format so that I can begin training models without manual data wrangling.

**Why this priority**: Without a clean, unified dataset of molecule-framework pairs, no modeling can occur. This is the foundational step that enables all subsequent analysis.

**Independent Test**: The pipeline can be executed end-to-end, producing a single CSV or JSON file containing a set of pre-filtered gas-MOF pairs with corresponding graph structures, and this file can be loaded by a simple verification script.

**Acceptance Scenarios**:

1. **Given** the raw dataset URLs are accessible, **When** the preprocessing script runs, **Then** it outputs all valid gas-MOF pairs found in the source data (up to a maximum of 500), and logs the count of filtered pairs.
2. **Given** a raw MOF structure file, **When** the script converts it to a graph, **Then** the resulting graph contains atom nodes with correct atomic numbers and edge attributes for bond distances.
3. **Given** a molecule SMILES string, **When** the script encodes it, **Then** the resulting molecular graph includes stereochemistry and hybridization attributes.

---

### User Story 2 - Heterogeneous GNN Training and Evaluation (Priority: P2)

As a researcher, I want to train a simplified heterogeneous GNN on the prepared dataset and evaluate its performance against baseline models so that I can determine if joint encoding improves permeability prediction accuracy.

**Why this priority**: This is the core research activity that addresses the primary research question regarding structural determinants of permeability.

**Independent Test**: The training script runs to completion within the time limit, produces a model checkpoint, and generates a metrics report comparing the heterogeneous GNN against linear regression and standard GCN baselines.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** the training script executes, **Then** training completes within 100 epochs or stops early if validation loss does not improve for 10 epochs, and outputs a test set RMSE and Pearson r value.
2. **Given** the trained heterogeneous GNN, **When** compared to the linear regression baseline, **Then** the report explicitly states whether the GNN achieved a lower RMSE.
3. **Given** a held-out test set, **When** predictions are generated, **Then** the model does not use any information from the training set in the final evaluation.

---

### User Story 3 - Ablation Study and Feature Attribution (Priority: P3)

As a researcher, I want to conduct an ablation study by removing heterogeneous cross-edges and analyze feature contributions so that I can quantify the specific value of joint molecule-framework encoding.

**Why this priority**: This provides the mechanistic insight required to answer "how" structural features determine permeability, distinguishing between simple correlation and joint interaction effects.

**Independent Test**: The ablation script runs the model without cross-edges, compares performance to the full model, and generates a sensitivity analysis of key structural thresholds.

**Acceptance Scenarios**:

1. **Given** the trained heterogeneous model, **When** the ablation study runs, **Then** it produces a performance delta metric showing the drop in accuracy when cross-edges are removed.
2. **Given** a specific cutoff for non-covalent contacts, **When** the sensitivity analysis sweeps the threshold, **Then** the report shows how the variance in RMSE varies across the set {0.01, 0.05, 0.1} nm.
3. **Given** the model predictions, **When** feature importance is calculated, **Then** the output lists the top 5 molecular and framework features contributing to permeability variance.

### Edge Cases

- What happens when a specific gas-MOF pair in the raw data has missing permeability values? (System must filter this pair out and log the count).
- How does the system handle MOF structures with periodic boundary conditions that exceed the 7GB RAM limit during graph construction? (System must sample or chunk the structure).
- How does the system handle molecules with undefined stereochemistry in the input SMILES? (System must use a default representation or skip the molecule).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and parse the CoRE MOF, IZA Zeolite, and gas permeability datasets, filtering to a representative subset of valid gas-MOF pairs with complete data. (See US-1)
- **FR-002**: The system MUST construct heterogeneous graphs where nodes represent atoms in both the molecule and the framework, and edges represent covalent bonds, distance-based neighbors, and non-covalent cross-contacts. (See US-1)
- **FR-003**: The system MUST implement a heterogeneous GNN with a small number of convolution layers, global mean-pooling, and a regression head, operating strictly in CPU-only mode. (See US-2)
- **FR-004**: The system MUST train the model using an Adam optimizer (lr=1e-3) with early stopping (patience=10) and a maximum of 100 epochs, ensuring the total runtime is ≤ 4 hours. (See US-2)
- **FR-005**: The system MUST evaluate performance using Pearson r, R², MAE, and RMSE, comparing the heterogeneous GNN against a linear regression baseline (using hand-crafted descriptors such as surface area and pore volume) and a standard GCN baseline. (See US-2)
- **FR-006**: The system MUST perform an ablation study removing cross-edges to quantify the contribution of joint encoding to prediction accuracy. (See US-3)
- **FR-007**: The system MUST execute a sensitivity analysis on the non-covalent contact distance threshold, sweeping values across the set {0.01, 0.05, 0.1} nm and reporting the variance in prediction error. (See US-3)
- **FR-008**: The system MUST frame all reported correlations as associational, explicitly avoiding causal claims unless the dataset includes randomized assignment. (See US-2)
- **FR-009**: The system MUST perform stratified 5-fold cross-validation and report the mean and standard deviation of metrics across folds to validate generalization on small datasets. (See US-2)

### Key Entities

- **Gas-MOF Pair**: A unique combination of a permeant molecule (SMILES/graph) and a porous framework (crystal/graph) with an associated experimental permeability coefficient.
- **Heterogeneous Graph**: A graph structure containing two node types (molecule atoms, framework atoms) and three edge types (covalent, neighbor, cross-contact).
- **Permeability Coefficient**: The target variable (log₁₀ transformed) representing the rate of gas transport through the material.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The prediction error (RMSE) of the heterogeneous GNN is measured against the RMSE of the linear regression baseline to determine the improvement from joint encoding. (See FR-005)
- **SC-002**: The Pearson correlation coefficient (r) between predicted and experimental log₁₀(permeability) is measured and reported for interpretation of model utility relative to the baseline. (See FR-005)
- **SC-003**: The performance delta (ΔRMSE) between the full heterogeneous model and the ablated model (no cross-edges) is measured to quantify the value of joint graph representation. (See FR-006)
- **SC-004**: The variance in RMSE across the sensitivity sweep {0.01, 0.05, 0.1} nm is measured to validate the robustness of the contact threshold. (See FR-007)
- **SC-005**: The total wall-clock time for the entire pipeline (download to evaluation) is measured against a predefined time limit. to ensure feasibility. (See FR-004)
- **SC-006**: The standard deviation of RMSE and Pearson r across the 5 cross-validation folds is measured to assess model stability on small datasets. (See FR-009)

## Assumptions

- The CoRE MOF 2019 and IZA Zeolite databases are accessible via public URLs and contain valid crystallographic information files (CIFs) for the required structures.
- The "Permeability of gases in MOFs" dataset on Figshare (or the NIST/ICSD fallback) contains at least 50 unique gas-MOF pairs with experimental permeability values; if fewer than 50 valid pairs are found, the pipeline must fail with a clear error message.
- The simplified heterogeneous GNN architecture (a shallow number of layers) is sufficient to capture the relevant structural interactions without requiring deep stacking that would exceed RAM limits.
- The non-covalent contact distance threshold (default) is a defensible community standard for defining molecule-framework interactions in porous materials.
- All required Python libraries (PyTorch, PyTorch Geometric, RDKit, pymatgen) can be installed and run within the memory constraints of the free-tier runner.
- The permeability values in the source dataset are already normalized or can be log-transformed to reduce skewness, as is standard in transport property modeling.
- Stratified 5-fold cross-validation is sufficient to estimate generalization error for this dataset size, provided the standard deviation is reported.