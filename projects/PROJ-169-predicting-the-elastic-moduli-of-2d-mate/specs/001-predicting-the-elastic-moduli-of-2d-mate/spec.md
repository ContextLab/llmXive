# Feature Specification: Predicting the Elastic Moduli of 2D Materials from Structure-Only Models

**Feature Branch**: `001-predicting-elastic-moduli`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Predicting the Elastic Moduli of 2D Materials from First-Principles Calculations" (Title updated per reviewer feedback to reflect structure-only surrogate modeling).

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

As a materials scientist, I need to download CIF files and elastic tensors from public repositories (Materials Project, AFLOW) and convert them into graph representations with node/edge features so that I can feed standardized data into the machine learning pipeline.

**Why this priority**: Without a clean, reproducible dataset of 2D materials with complete elastic tensors, no modeling or analysis can occur. This is the foundational step.

**Independent Test**: The script can be run to download a subset of materials, parse their CIFs into graphs using `pymatgen`, and output a JSON/CSV summary of node counts, edge counts, and target values without requiring any model training.

**Acceptance Scenarios**:

1. **Given** a list of valid material IDs from Materials Project and AFLOW, **When** the ingestion script runs, **Then** it successfully downloads CIFs, filters for 2D designation, and outputs a dataset file containing graph structures and elastic tensors for all valid entries.
2. **Given** a CIF file with missing elastic tensor components, **When** the script processes it, **Then** the entry is excluded from the final dataset, and a log entry records the exclusion reason (incomplete tensor).
3. **Given** a dataset of 2D materials, **When** the graph conversion runs, **Then** each node is assigned elemental and coordination features, and each edge is assigned distance and bond-type features, verified by inspecting the output graph schema.

---

### User Story 2 - Lightweight GNN Training and Evaluation (Priority: P2)

As a researcher, I need to train a lightweight Graph Neural Network on the constructed dataset to predict Young's modulus, shear modulus, and Poisson's ratio, and evaluate its performance against held-out DFT values.

**Why this priority**: This is the core research activity that tests the hypothesis that structure-only models can approximate DFT results.

**Independent Test**: The training script can be executed on a CPU-only environment, training for a specified number of epochs, and outputting a JSON report with MAPE, RMSE, and R² scores for the test set.

**Acceptance Scenarios**:

1. **Given** a pre-processed dataset split into train/val/test sets, **When** the GNN training script runs, **Then** it completes within 6 hours on a 2-core CPU runner and outputs a checkpoint file and a metrics report.
2. **Given** a trained model, **When** it is evaluated on the held-out test set, **Then** the Mean Absolute Percentage Error (MAPE) is calculated and reported for each target property (Young's, Shear, Poisson).
3. **Given** a stratified split by material family, **When** the model is tested on a family not present in the training set, **Then** the performance drop (increase in MAPE) is explicitly reported to measure generalization.

---

### User Story 3 - Feature Importance and Ablation Analysis (Priority: P3)

As a domain expert, I need to identify which structural descriptors (e.g., coordination number, bond length, symmetry) most strongly influence the predicted elastic moduli and understand the contribution of different descriptor classes.

**Why this priority**: This addresses the primary research question regarding *which* structural features determine elasticity, providing actionable design rules.

**Independent Test**: The analysis script can run on the trained model to generate SHAP values and ablation study results, outputting a ranked list of features and performance deltas.

**Acceptance Scenarios**:

1. **Given** a trained GNN model and test data, **When** the feature importance script runs, **Then** it outputs a ranked list of the top 5 structural descriptors by permutation importance and SHAP contribution.
2. **Given** the full model, **When** an ablation study removes specific descriptor classes (e.g., composition-only, coordination-only), **Then** the resulting change in MAPE is calculated and reported for each ablation.
3. **Given** the results, **When** the final report is generated, **Then** it explicitly states which material families (e.g., TMDs vs. MXenes) are most and least predictable from structure alone.

### Edge Cases

- **Data Scarcity**: What happens if a specific material family (e.g., 2D oxides) has fewer than 10 entries in the public dataset? The system must handle this by either excluding the family from stratified splits or flagging it as "insufficient data" in the generalization report.
- **Graph Disconnection**: How does the system handle a CIF file that parses into a disconnected graph (e.g., isolated atoms)? The preprocessing step must detect disconnected components and either merge them if physically justified or exclude the entry with a specific error code.
- **CPU Memory Overflow**: How does the system handle a dataset that exceeds 7GB RAM during graph construction? The pipeline must implement chunked processing or sampling to ensure it fits within the 7GB limit.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download CIF files and elastic tensors from Materials Project and AFLOW APIs, filtering strictly for entries with complete 6-component elastic tensors and 2D layer designation, using ONLY crystallographic coordinates and elemental data (See US-1).
- **FR-002**: The system MUST convert valid CIFs into graph representations where nodes contain elemental/coordination features and edges contain distance/bond-type features, strictly excluding any DFT-relaxed geometry or electronic structure data used to generate the target tensor (See US-1).
- **FR-003**: The system MUST implement a lightweight message-passing GNN with a configurable architecture supporting 2 to 3 layers and hidden dimension ≤64, capable of regression for Young's, Shear, and Poisson's ratio (See US-2).
- **FR-004**: The system MUST perform 5-fold cross-validation and stratified splitting by distinct chemical prototypes or space group + stoichiometry class, ensuring no material family appears in both train and test sets for the inter-family test (See US-2).
- **FR-005**: The system MUST compute and report permutation importance and SHAP values for all structural descriptors to rank their contribution to prediction accuracy (See US-3).
- **FR-006**: The system MUST execute an ablation study comparing full-structure models against composition-only baselines using a distinct model architecture (e.g., feed-forward network on Magpie descriptors) that cannot encode topology (See US-3).
- **FR-007**: The system MUST enforce a compute budget of ≤6 hours on a 2-core CPU runner with ≤7GB RAM, including data download, preprocessing, training, and evaluation (See US-2).

### Key Entities

- **MaterialGraph**: A graph structure representing a 2D crystal, containing nodes (atoms with element, coordination number) and edges (bonds with distance, type).
- **ElasticTensor**: A 6-component vector derived from DFT calculations, representing the material's stiffness (Young's, Shear, Poisson).
- **DescriptorSet**: A collection of computed features (Magpie composition stats, bond-angle histograms, symmetry class) associated with a MaterialGraph.
- **TMDs (Transition Metal Dichalcogenides)**: A family of 2D materials with the formula MX2 (M=transition metal, X=chalcogen).
- **MXenes**: A family of 2D transition metal carbides, nitrides, or carbonitrides with the general formula Mn+1XnTx.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Prediction accuracy (MAPE) for Young's, Shear, and Poisson's ratio is measured against the held-out DFT values from the test set (See FR-004, US-2).
- **SC-002**: Generalization performance drop is measured by comparing MAPE on intra-family test splits versus inter-family test splits (See FR-004, US-2).
- **SC-003**: Feature contribution is measured by the magnitude of SHAP values and the performance delta in ablation studies (See FR-005, FR-006, US-3).
- **SC-004**: Compute feasibility is measured by total wall-clock time and peak memory usage against the 6-hour/7GB constraints (See FR-007, US-2).
- **SC-005**: Data coverage is measured by the count of at least 5 unique material families represented in the final dataset (See FR-001, US-1).

## Assumptions

- **Dataset Completeness**: It is assumed that the Materials Project and AFLOW public repositories contain a sufficient number of 2D materials with complete elastic tensors to train a GNN without requiring synthetic data generation.
- **Structure-Only Sufficiency**: It is assumed that structural descriptors (bond topology, coordination, composition) contain enough information to predict elastic moduli with acceptable accuracy, as electronic structure effects are secondary for this specific property in the 2D regime.
- **CPU Feasibility**: It is assumed that a lightweight GNN (≤3 layers, hidden dim ≤64) trained on a sampled dataset will converge within 20 epochs on a standard 2-core CPU without GPU acceleration.
- **API Stability**: It is assumed that the Materials Project and AFLOW public APIs will remain accessible and stable during the data download phase, with no rate limits preventing bulk retrieval of CIFs.
- **No Causal Claims**: It is assumed that the study will frame all findings as associational (structure-property correlations) rather than causal, as the design is observational with no random assignment of structural features.