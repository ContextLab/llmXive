# Feature Specification: Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks

**Feature Branch**: `001-predict-molecular-permeability-gnn`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to automatically download, filter, and convert the CoRE MOF 2019, IZA Zeolite, and gas permeability datasets into a unified graph format so that I can begin training models without manual data wrangling.

**Why this priority**: Without a clean, unified dataset of gas‑framework pairs, no modeling can occur. This is the foundational step that enables all subsequent analysis.

**Independent Test**: The pipeline can be executed end‑to‑end, producing a single CSV or JSON file containing a set of pre‑filtered gas‑framework pairs with corresponding graph structures, and this file can be loaded by a simple verification script.

**Acceptance Scenarios**:

1. **Given** the raw dataset URLs are accessible, **When** the preprocessing script runs, **Then** it outputs up to 500 highest‑quality gas‑framework pairs (selected by completeness of experimental permeability) and logs the count of filtered pairs. (See FR‑001)
2. **Given** a raw framework structure file, **When** the script converts it to a graph, **Then** the resulting graph contains atom nodes with correct atomic numbers, valence, partial charge, hybridization, orbital information, and edge attributes for bond distances. (See FR‑002)
3. **Given** a molecule SMILES string, **When** the script encodes it, **Then** the resulting molecular graph includes stereochemistry, hybridization, partial charge, valence, and orbital attributes. (See FR‑002)

---

### User Story 2 - Heterogeneous GNN Training and Evaluation (Priority: P2)

As a researcher, I want to train a simplified heterogeneous GNN on the prepared dataset and evaluate its performance against baseline models so that I can determine if joint encoding improves permeability prediction accuracy.

**Why this priority**: This is the core research activity that addresses the primary research question regarding structural determinants of permeability.

**Independent Test**: The training script runs to completion within the time limit, produces a model checkpoint, and generates a metrics report comparing the heterogeneous GNN against three baselines: (i) linear regression on handcrafted descriptors, (ii) a standard GCN on the combined graph, and (iii) separate GCNs for gas and framework with late fusion.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** the training script executes, **Then** training completes within 100 epochs or stops early if validation loss does not improve for patience = 10, and outputs a test set RMSE and Pearson r value. (See FR‑004)
2. **Given** the trained heterogeneous GNN, **When** compared to the linear regression baseline, **Then** the report explicitly states whether the GNN achieved a lower RMSE. (See FR‑005)
3. **Given** the k‑fold stratified cross‑validation procedure (stratified by gas type) defined in FR‑009, **When** predictions are generated, **Then** the model does not use any information from the held‑out test folds in the final evaluation. (See FR‑009)

---

### User Story 3 - Ablation Study, Feature Attribution, and Sensitivity Analysis (Priority: P3)

As a researcher, I want to conduct an ablation study by removing heterogeneous cross‑edges, analyze feature contributions, and sweep the non‑covalent contact distance threshold so that I can quantify the specific value of joint molecule‑framework encoding and assess robustness.

**Why this priority**: This provides the mechanistic insight required to answer “how” structural features determine permeability, distinguishing between simple correlation and joint interaction effects.

**Independent Test**: The ablation script runs the model without cross‑edges, compares performance to the full model, generates a sensitivity analysis of the contact threshold, and produces a ranked list of the top molecular and framework features contributing to permeability variance.

**Acceptance Scenarios**:

1. **Given** the trained heterogeneous model, **When** the ablation study runs, **Then** it produces a performance delta metric showing the drop in accuracy when cross‑edges are removed. (See FR‑006, SC‑003)
2. **Given** a specific cutoff for non‑covalent contacts, **When** the sensitivity analysis sweeps the threshold across the set {0.30, 0.50, 0.70} nm, **Then** the report shows how the variance in RMSE varies across these values, thereby **characterizing** sensitivity to the threshold. (See FR‑007, SC‑004)
3. **Given** the model predictions, **When** feature importance is calculated using GNNExplainer node‑importance scores aggregated per node type, **Then** the output lists the top five molecular and top five framework atom‑level features with SHAP‑like values. (See FR‑010, SC‑007)

### Edge Cases

- What happens when a specific gas‑framework pair in the raw data has missing permeability values? (System must filter this pair out and log the count).
- How does the system handle framework structures with periodic boundary conditions that exceed the 7 GB RAM limit during graph construction? (System must sample or chunk the structure as defined in FR‑019).
- How does the system handle molecules with undefined stereochemistry in the input SMILES? (System must use a default representation or skip the molecule).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and parse the CoRE MOF 2019, IZA Zeolite, and the Figshare “Permeability of gases in MOFs” dataset (DOI:), filtering to **up to 500** gas‑framework pairs with complete experimental permeability data. (See US‑1)
- **FR-002**: The system MUST construct heterogeneous graphs where nodes represent atoms in both the gas molecule and the framework, and edges represent (a) covalent bonds, (b) distance‑based neighbor edges with a cutoff of 0.35 nm, and (c) non‑covalent cross‑contact edges defined by a sweepable distance threshold (see FR‑007). Node attributes MUST include atomic number, valence, partial charge, hybridization, and orbital information for both gas‑molecule and framework atoms. (See US‑1)
- **FR-003**: The system MUST implement a heterogeneous GNN with a small number of convolution layers, global mean‑pooling, and a regression head, operating strictly in CPU‑only mode. (See US‑2)
- **FR-004**: The system MUST train the model using an Adam optimizer (lr = 1e‑3, weight decay = 1e‑5) with early stopping (patience = 10) and a maximum of 100 epochs, ensuring the total runtime is ≤ 4 hours. (See US‑2)
- **FR-005**: The system MUST evaluate performance using Pearson r, R², MAE, and RMSE, comparing the heterogeneous GNN against three baselines: (i) linear regression on the exact descriptor set {surface area, pore volume, largest cavity diameter, accessible surface area}, (ii) a standard GCN on the combined graph, (iii) separate GCNs for gas and framework with late fusion. (See US‑2)
- **FR-006**: The system MUST perform an ablation study removing cross‑edges to quantify the contribution of joint encoding to prediction accuracy. (See US‑3)
- **FR-007**: The system MUST execute a sensitivity analysis on the non‑covalent contact distance threshold, sweeping values across the set {0.30, 0.50, 0.70} nm and reporting the variance in prediction error. (See US‑3)
- **FR-008**: The system MUST frame all reported correlations as associational, explicitly avoiding causal claims unless the dataset includes randomized assignment. (See US‑2)
- **FR-009**: The system MUST perform stratified k‑fold cross‑validation (stratified by gas type) and report the mean and standard deviation of metrics across folds to validate generalization on small datasets. (See US‑2)
- **FR-010**: The system MUST compute feature‑importance scores using GNNExplainer node‑importance values, aggregate them per node type (molecular vs. framework), and produce a ranked list of the top five molecular and top five framework atom‑level features with SHAP‑like values. (See US‑3)
- **FR-011**: The system MUST implement a late‑fusion baseline consisting of separate GCNs for gas and framework whose latent representations are concatenated before the regression head. (See FR‑005)
- **FR-012**: The system MUST adopt the stratification rule defined in FR‑009 (by gas type) for all cross‑validation splits. (See SC‑008)
- **FR-014**: The system MUST use a fixed distance cutoff of 0.35 nm for constructing distance‑based neighbor edges between atoms of the same component. (See SC‑009)
- **FR-015**: The linear‑regression baseline MUST use exactly the four descriptors {surface area, pore volume, largest cavity diameter, accessible surface area}; no other descriptors are permitted. (See SC‑010)
- **FR-016**: The system MUST verify that the experimental permeability dataset is a peer‑reviewed, publicly available source (Simon et al., 2022,) by checking the DOI metadata (journal, peer‑review status) and confirming that the downloaded file contains a citation field matching this DOI; any entry lacking this provenance is rejected as simulated. (See SC‑013)
- **FR-017**: The system MUST perform a statistical power analysis on the ΔRMSE between the heterogeneous GNN and the linear‑regression baseline using a two‑sided paired t‑test across the 5 CV folds, with α = 0.05 and targeting a medium effect size (Cohen’s d = 0.5); the achieved power must be reported and if < 0.8 the result is flagged as exploratory. (See SC‑012)
- **FR-018**: The system MUST report the runtime of the entire pipeline (download → evaluation) and verify it does not exceed the ≤ 4 hour bound defined in FR‑004. (See SC‑005)
- **FR-019**: When a framework structure’s periodic representation would require > 7 GB of RAM for graph construction, the system MUST either (a) randomly sample a subset of atoms preserving connectivity up to the memory limit, or (b) chunk the structure into overlapping sub‑graphs that are processed sequentially, ensuring full coverage of the original structure. (See Edge Cases)
- **FR-020**: The system MUST generate a feature‑importance report file named `feature_importance.json` that lists the top five molecular and top five framework atom‑level features with SHAP‑like values as computed by GNNExplainer. (See US‑3)
- **FR-021**: The system MUST NOT use computed geometric transport proxies as the prediction target; the target variable is the experimentally measured permeability (log₁₀ transformed) from the verified dataset. (See US‑2)

### Key Entities

- **Gas‑Framework Pair**: A unique combination of a permeant molecule (SMILES/graph) and a porous framework (crystal/graph) with an associated **experimental** permeability coefficient (log₁₀ transformed). (See FR‑016)
- **Heterogeneous Graph**: A graph structure containing two node types (gas‑molecule atoms, framework atoms) and three edge types (covalent, neighbor with 0.35 nm cutoff, cross‑contact with sweepable threshold).
- **Permeability Coefficient**: The target variable (log₁₀ transformed) representing the experimentally measured rate of gas transport through the material.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The prediction error (RMSE) of the heterogeneous GNN is measured against the RMSE of each baseline (linear regression, standard GCN, late‑fusion GCN) to determine the improvement from joint encoding. (See FR‑005)
- **SC-002**: The Pearson correlation coefficient (r) between predicted and experimental log₁₀(permeability) is measured and reported for interpretation of model utility relative to each baseline. (See FR‑005)
- **SC-003**: The performance delta (ΔRMSE) between the full heterogeneous model and the ablated model (no cross‑edges) is measured to quantify the value of joint graph representation. (See FR‑006)
- **SC-004**: The variance in RMSE across the sensitivity sweep {0.30, 0.50, 0.70} nm is measured to **characterize** the sensitivity of model performance to the contact threshold. (See FR‑007)
- **SC-005**: The total wall‑clock time for the entire pipeline (download to evaluation) is measured and must be ≤ 4 hours. (See FR‑018)
- **SC-006**: The standard deviation of RMSE and Pearson r across the 5 cross‑validation folds is measured to assess model stability on small datasets. (See FR‑009)
- **SC-007**: The feature‑importance report must list at least the top five molecular and top five framework atom‑level features with SHAP‑like values, generated via GNNExplainer aggregation as specified in FR‑020, and be reproducible. (See FR‑020)
- **SC-008**: The stratified CV must use gas‑type stratification as defined in FR‑012; verification is performed by checking that each fold contains a proportional representation of each gas type. (See FR‑012)
- **SC-009**: The neighbor‑edge construction must use a 0.35 nm cutoff; verification is performed by sampling 100 random graphs and confirming no neighbor edge exceeds this distance. (See FR‑014)
- **SC-010**: The linear‑regression baseline must be built using exactly the four specified descriptors; verification is performed by asserting the descriptor matrix shape matches (n_samples × 4). (See FR‑015)
- **SC-011**: The late‑fusion baseline must be trained and reported; its RMSE is compared to the other baselines. (See FR‑011)
- **SC-012**: The power analysis must report achieved statistical power for the paired t‑test on ΔRMSE; if < 0.8, the result is flagged as exploratory. (See FR‑017)
- **SC-013**: The dataset used for training and evaluation must be the verified experimental dataset (Simon et al., 2022,); any simulated target triggers a failure. (See FR‑016)

## Assumptions

- The CoRE MOF 2019 and IZA Zeolite databases are accessible via public URLs and contain valid crystallographic information files (CIFs) for the required structures.
- The verified experimental permeability dataset compiled in the Figshare “Permeability of gases in MOFs” collection (DOI ) contains at least 50 unique gas‑framework pairs with measured permeability values; if fewer than 50 valid pairs are found, the pipeline must fail with a clear error message.
- The simplified heterogeneous GNN architecture (a shallow number of layers) is sufficient to capture the relevant structural interactions without requiring deep stacking that would exceed RAM limits.
- The non‑covalent contact distance thresholds {0.30, 0.50, 0.70} nm are derived from typical van der Waals contact ranges in porous materials and are therefore physically plausible.
- All required Python libraries (PyTorch, PyTorch Geometric, RDKit, pymatgen) can be installed and run within the memory constraints of the free‑tier runner.
- The permeability values in the source dataset are experimentally measured and will be log‑transformed to reduce skewness, as is standard in transport property modeling.
- Stratified 5‑fold cross‑validation is used (instead of the idea’s 3‑fold) because it provides a more reliable estimate of generalization error for the modest dataset size; this choice is documented here to maintain traceability.
- The target variable is the experimentally measured permeability from the Figshare dataset; no surrogate geometric proxies are used, satisfying FR‑016.
- The power analysis assumes a paired t‑test on ΔRMSE across folds, α = 0.05, and targets a medium effect size (Cohen’s d = 0.5), which is a conventional benchmark for detecting meaningful performance differences.
- GNNExplainer node‑importance scores can be aggregated per node type to produce SHAP‑like attribution values for molecular vs. framework features, enabling the required top‑five feature lists.
