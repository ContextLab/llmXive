# Feature Specification: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Feature Branch**: `001-predicting-molecular-reactivity`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases"

## User Scenarios & Testing

### User Story 1 - CPU-Feasible Data Ingestion and Preprocessing (Priority: P1)

As a computational chemist with limited hardware access, I need to download the QM9 dataset and preprocess it into graph structures using only CPU resources, so that I can begin the analysis without requiring specialized GPU infrastructure.

**Why this priority**: This is the foundational step. Without a successfully ingested and preprocessed dataset that fits within the available RAM constraint of the GitHub Actions free tier, no modeling or analysis can occur. It directly addresses the "compute feasibility" constraint.

**Independent Test**: The pipeline can be fully tested by executing the data download and preprocessing script on a CPU-only runner and verifying that the output graph objects (node/edge features) are correctly formed and fit within memory limits.

**Acceptance Scenarios**:

1. **Given** a GitHub Actions free-tier runner (2 CPU, 7 GB RAM), **When** the system downloads the QM9 subset and converts SMILES to graphs using RDKit, **Then** the process completes without memory errors and outputs a serialized graph dataset containing node features (atomic number, hybridization, formal charge) and edge features (bond type, conjugation).
2. **Given** a raw SMILES string from the QM9 dataset, **When** the preprocessing step is applied, **Then** the resulting graph node features include the required chemical descriptors and edge features include bond types, ready for model ingestion.

---

### User Story 2 - Lightweight Model Training and Baseline Comparison (Priority: P2)

As a researcher, I need to train a lightweight Spectral GNN and a Heterophily-aware GNN on the preprocessed data and compare them against a Random Forest baseline, so that I can determine if graph-based approaches offer predictive advantages over traditional descriptors under CPU constraints.

**Why this priority**: This addresses the core research question regarding model performance and the comparison between graph-based and descriptor-based methods. It is the primary experimental engine of the project.

**Independent Test**: The training and evaluation loop can be tested independently by running the training script for a fixed number of epochs and verifying that both models converge and produce metric logs (MSE, MAE, Pearson R) that can be statistically compared.

**Acceptance Scenarios**:

1. **Given** the preprocessed QM9 dataset split via Murcko scaffolds (80/20), **When** the Spectral GNN and Heterophily-aware GNN are trained for 50 epochs with early stopping on a CPU, **Then** both models converge and generate prediction files for the test set within the 6-hour time limit.
2. **Given** the test set predictions from the GNNs and a Random Forest baseline trained on Morgan fingerprints, **When** the evaluation script runs, **Then** it outputs MSE, MAE, and Pearson correlation coefficients for all three models, enabling a direct performance comparison.

---

### User Story 3 - Feature Attribution and Interpretability Analysis (Priority: P3)

As a domain expert, I need to identify which specific structural and electronic features (e.g., bond types, orbital energies) contribute most to the model's predictions via feature attribution, so that I can gain interpretability into the drivers of molecular reactivity.

**Why this priority**: This addresses the "which features carry the most predictive signal" part of the research question. While the model can predict without this, the interpretability is the unique value proposition of this specific research design.

**Independent Test**: The attribution analysis can be tested by running the GNNExplainer (or equivalent gradient-based method) on a subset of molecules and verifying that it produces valid subgraph/node importance scores that align with the curated reference set of known reactive substructures.

**Acceptance Scenarios**:

1. **Given** a trained GNN model and a set of test molecules, **When** the feature attribution module runs, **Then** it outputs a ranked list of node/edge features (e.g., specific bond types or atomic environments) with associated importance scores.
2. **Given** the attribution results, **When** the system aggregates importance across the dataset, **Then** it identifies the top 5 structural/electronic features (e.g., frontier orbital energies, specific bond orders) as the dominant predictors of the target property.

---

### Edge Cases

- **What happens when** the QM9 dataset download fails or the HuggingFace API is unreachable? The system MUST retry up to 3 times with exponential backoff, and if all fail, MUST exit with a clear error code and log the specific failure reason.
- **How does system handle** molecules in the dataset that fail RDKit parsing (e.g., invalid SMILES)? The system MUST log these molecules, exclude them from the training set, and report the exclusion count (target: < 0.1% of total) without crashing the pipeline.
- **What happens when** the memory usage exceeds 4 GB during graph construction or training? The system MUST detect this (via monitoring) and automatically trigger a subset sampling strategy (e.g., reducing batch size or molecule count) to stay within the operational limit, logging the adjustment.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the QM9 dataset (subset of molecules) and preprocess SMILES into graph structures using RDKit on CPU, ensuring node features include atomic number, hybridization, and formal charge, and edge features include bond type and conjugation (See US-1).
- **FR-002**: System MUST implement a lightweight Spectral GNN and a Heterophily-aware GNN (based on VR-GNN principles) using PyTorch in CPU-only mode (`device='cpu'`), ensuring memory usage stays under 4 GB during training (See US-2).
- **FR-003**: System MUST train both GNN models for 50 epochs with early stopping on a scaffold-based (Murcko) 80/20 train/test split, targeting the prediction of DFT-derived properties (e.g., HOMO-LUMO gap) as a proxy for reactivity (See US-2).
- **FR-004**: System MUST implement a Random Forest baseline trained on hand-crafted molecular descriptors (Morgan fingerprints) to serve as a comparative benchmark for the GNNs (See US-2).
- **FR-005**: System MUST perform feature attribution analysis using GNNExplainer or gradient-based methods to identify subgraphs or node features contributing most to predictions (See US-3).
- **FR-006**: System MUST apply a paired t-test on the prediction errors of the GNNs vs. the Random Forest baseline using a scaffold-based split to statistically assess if the graph-based approach provides a significant improvement (See US-2).
- **FR-007**: System MUST log all artifacts (model weights, attribution maps, metrics) to the repository for reproducibility (See US-2, US-3).
- **FR-008**: System MUST include and utilize a curated reference set of 50 known reactive substructures (derived from public literature) to validate feature attribution results against an independent ground truth (See US-3).
- **FR-009**: System MUST include a curated external dataset of at least 20 molecules with experimental reaction rates to validate the HOMO-LUMO gap proxy against kinetic data (See Assumptions).

### Key Entities

- **Molecular Graph**: A graph structure representing a molecule, with nodes as atoms (features: atomic number, hybridization, formal charge) and edges as bonds (features: bond type, conjugation).
- **DFT Property**: The target variable derived from quantum-mechanical calculations (e.g., HOMO-LUMO gap, reaction yield proxy) used as the ground truth for training and evaluation.
- **Feature Attribution Map**: A data structure mapping specific subgraphs or node features to their importance scores in predicting the target property.
- **Curated Reference Set**: A static dataset of 50 known reactive substructures used for independent validation of feature importance.
- **External Kinetic Dataset**: A static dataset of ≥20 molecules with experimental reaction rates used to validate the HOMO-LUMO gap proxy.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pearson correlation coefficient (R) of the GNN predictions against DFT ground truth is measured against the target threshold: [deferred] (See US-2).
- **SC-002**: Prediction error (MSE/MAE) of the GNNs is measured against the Random Forest baseline using a paired t-test on a scaffold-based split; significance level: [deferred] (See US-2).
- **SC-003**: Feature attribution results are measured against the curated reference set of 50 known reactive substructures, requiring an alignment score ≥ 0.7 (See US-3).
- **SC-004**: Total runtime of the end-to-end pipeline (download, preprocess, train, evaluate) is measured against the constraint of Total runtime ≤ 6 hours. (See US-1, US-2).
- **SC-005**: Memory usage during graph construction and training is measured against the operational limit of Memory usage ≤ 4 GB (See US-1, US-2).
- **SC-006**: The correlation between predicted HOMO-LUMO gap and experimental reaction rates is measured against the external kinetic dataset (n ≥ 20) to validate the proxy (See Assumptions).

## Assumptions

- The QM9 dataset contains all necessary variables (atomic properties, bond types, DFT-calculated target properties) to answer the research question; if a specific reactivity metric is missing, the HOMO-LUMO gap will be used as a validated proxy for reactivity.
- The molecular graphs in QM9 exhibit low homophily (heterophily), necessitating the use of Heterophily-aware GNN architectures rather than standard message-passing networks.
- The GitHub Actions free-tier runner (standard CPU, moderate RAM, and disk capacity) is sufficient for training lightweight GNNs on a subset of [deferred] molecules without GPU acceleration.
- The Random Forest baseline using Morgan fingerprints provides a robust, standard benchmark for comparing the predictive power of graph-based methods against traditional descriptor-based methods in this domain.
- The feature attribution method (GNNExplainer) is valid for identifying chemical substructures relevant to reactivity, despite potential limitations in interpretability for graph neural networks.
- A curated reference set of 50 known reactive substructures and an external kinetic dataset of ≥20 molecules with experimental rates will be included as static assets in the repository to provide independent ground truth for validation.