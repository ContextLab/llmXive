# Feature Specification: Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks

**Feature Branch**: `[001-polymer-interaction-gnn]`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Pipeline Construction (Priority: P1)

As a materials researcher, I need to download molecular graph data from public benchmarks (MolNet via HuggingFace Datasets) and cross-reference it with NIST Chemistry WebBook or curated literature tables to construct a dataset of polymer-filler interface pairs with adhesion energy measurements, so that I have a valid dataset for training the predictive model.

**Why this priority**: Without a properly curated dataset containing both molecular topology data (from MolNet) and corresponding adhesion energy measurements (from NIST/Literature), no downstream analysis is possible. This is the foundational data layer.

**Independent Test**: Can be fully tested by verifying the data pipeline executes without errors, produces a dataset with ≥100 polymer-filler interface pairs (target ≥500), and confirms all required variables (node types, edge types, adhesion energy values) are present in the curated subset.

**Acceptance Scenarios**:

1. **Given** the MolNet benchmark is accessible via HuggingFace Datasets API and NIST/Literature tables are accessible, **When** the data download, filtering, and cross-referencing script executes, **Then** the output dataset `curated_dataset.csv` contains ≥100 rows where `pair_type == 'interface'` with complete molecular graph structures and adhesion energy measurements (target ≥500). If <500, the system MUST log a "Limited Power" warning and report the calculated margin of error.
2. **Given** a dataset subset, **When** the variable validation check runs, **Then** every required predictor variable (atom types, bond types, connectivity patterns) AND outcome variable (adhesion energy) are present with no missing values >5% **per column**, calculated as `missing_count / total_rows`.

---

### User Story 2 - Model Training Execution (Priority: P2)

As a computational materials scientist, I need to train a 3-layer Graph Convolutional Network (GCN) on the curated polymer-filler interface data using CPU-only execution so that I can learn the mapping from molecular topology to adhesion energy.

**Why this priority**: This delivers the core predictive capability. Without a trained model, there is no structure-property relationship to analyze or validate.

**Independent Test**: Can be fully tested by executing the training script on a CPU-only environment and confirming the model completes training within 4.5 hours (target) with a hard failure limit of approximately six hours, uses ≤6 GB RAM at peak, and achieves training loss convergence (MSE reduction ≥50% from initial epoch to final epoch).

**Acceptance Scenarios**:

1. **Given** the curated dataset and GPU-free environment, **When** the 3-layer GCN training script executes with batch size ≤32, **Then** the model completes training within 4.5 hours on CPU cores with peak memory usage ≤6 GB. If training time exceeds 4.5 hours but remains ≤6 hours, the system MUST checkpoint and resume; if >6 hours, the job MUST fail with a timeout error.
2. **Given** the 80/20 train-test split, **When** the model trains for 50 epochs, **Then** the validation loss shows monotonic decrease or plateau (no increase >10% from `min(loss_history)` observed during epochs 1-50) indicating convergence.

---

### User Story 3 - Statistical Validation & Attribution (Priority: P3)

As a peer reviewer, I need to verify that the model's predictive performance is statistically significant (not random chance) and identify which topological features drive predictions so that the structure-property relationship is scientifically defensible.

**Why this priority**: This provides scientific rigor and interpretability. Without statistical validation and feature attribution, the model's predictions lack credibility for materials design decisions.

**Independent Test**: Can be fully tested by running the permutation test (sufficient iterations for convergence) and gradient-based attribution analysis, confirming the model outperforms random chance (p < 0.05) and produces interpretable feature importance rankings.

**Acceptance Scenarios**:

1. **Given** the trained model and test set, **When** the permutation test executes with a sufficient number of iterations to ensure statistical robustness., **Then** the observed model performance exceeds the High quantile (e.g., 0.95 quantile) of permuted baseline performances (p < 0.05).
2. **Given** a trained GCN model, **When** gradient-based attribution analysis runs on a set of test samples, **Then** the output identifies ≥3 topological features (e.g., node degree, edge connectivity, graph density) with importance scores that vary meaningfully across samples, defined as a standard deviation of importance scores > 0.1.

---

### Edge Cases

- **E-DATA-001**: What happens when the MolNet dataset does not contain sufficient polymer-filler interface pairs with adhesion energy measurements? → The system MUST verify the presence of adhesion energy measurements in the source dataset (MolNet/NIST). If the specific 'adhesion energy' field is absent or the dataset contains <100 polymer-filler pairs with this metric, the pipeline MUST halt with error code E-DATA-001 and log the available outcome variables. In this event, the scope is narrowed to 'polymer-filler interaction prediction using available topological descriptors only,' and the system MUST proceed with a proxy metric (e.g., binding energy from HuggingFace `molnet` `bace` or `esol` subsets if chemically analogous) ONLY if a justification document linking the proxy to adhesion is generated; otherwise, the run fails. (See US-1)
- What happens when the 6-hour GitHub Actions runtime limit is exceeded during training? → The system MUST checkpoint model state periodically and resume from checkpoint on restart; if total time >6 hours, the job MUST fail with a timeout error.
- How does the system handle missing adhesion energy values in the curated dataset? → Records missing data count; if missing >5% per column, the system MUST flag for imputation review or dataset expansion.
- How does the system handle collinearity between graph topology predictors (e.g., node degree and connectivity patterns)? → The system MUST compute variance inflation factor (VIF) for all predictors for interpretability reporting; however, the GNN architecture MUST use attention mechanisms or feature selection layers to handle collinearity internally. The system MUST NOT halt training based on VIF > 5.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download molecular graph data from MolNet benchmark via HuggingFace Datasets API and cross-reference with NIST Chemistry WebBook or curated literature tables to construct polymer-filler interface pairs with adhesion energy measurements (See US-1)
- **FR-002**: System MUST construct heterogeneous graphs encoding atom types as nodes and bonds/interactions as edges for each polymer-filler interface pair (See US-1)
- **FR-003**: System MUST implement a 3-layer Graph Convolutional Network using PyTorch Geometric with CPU-only execution (no CUDA, no GPU device_map) (See US-2)
- **FR-004**: System MUST train the model using 80/20 train-test split with mean squared error (MSE) loss and batch size ≤32 (See US-2)
- **FR-005**: System MUST execute a permutation test with 1000 iterations to validate model performance exceeds random chance (See US-3)
- **FR-006**: System MUST perform gradient-based attribution analysis to identify topological features driving adhesion predictions (See US-3)
- **FR-007**: System MUST compute variance inflation factor (VIF) for all graph topology predictors for interpretability reporting, but MUST NOT halt training based on VIF thresholds; the GNN MUST use attention mechanisms to handle collinearity (See US-3)
- **FR-008**: System MUST apply Bonferroni or Holm correction to p-values if the count of p-values in `results.csv` > 1 (See US-3)

### Key Entities *(include if feature involves data)*

- **MolecularGraph**: Represents a polymer or filler molecule with node attributes (atom type, charge, hybridization) and edge attributes (bond type, bond order)
- **InterfacePair**: Represents a polymer-filler interface with two MolecularGraph entities and an associated adhesion energy measurement (outcome variable)
- **TrainedGCN**: The output model artifact with learned weights mapping graph topology features to adhesion energy predictions

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the requirement that all predictor variables (atom types, bond types, connectivity patterns) AND outcome variable (adhesion energy) are present with ≤5% missing values per column (See US-1)
- **SC-002**: Model training feasibility is measured against the constraint that total runtime ≤6 hours and peak memory ≤6 GB on CPU cores (See US-2)
- **SC-003**: Model statistical significance is measured against the permutation test baseline with a sufficient number of iterations, requiring p < 0.05 (See US-3)
- **SC-004**: Predictor collinearity is measured against VIF calculation for interpretability; the GNN architecture MUST demonstrate ability to handle correlated features via attention weights (See US-3)
- **SC-005**: Multiple-comparison correction is measured against family-wise error rate control; if the count of p-values in `results.csv` > 1, Bonferroni or Holm correction MUST be applied (See US-3)

## Assumptions

- The NIST Chemistry WebBook or curated literature tables contain sufficient polymer-filler interface pairs (target ≥500, minimum ≥100) with both molecular graph structures (or identifiers to link to MolNet) AND adhesion energy measurements.
- This is an observational study (no random assignment of molecular structures); therefore findings MUST be framed as ASSOCIATIONAL, not causal, in all reporting and conclusions.
- The 3-layer GCN architecture is sufficiently lightweight to execute within 6 hours on GitHub Actions free-tier (Multiple CPU, 7 GB RAM) without GPU acceleration.
- Molecular graph representations use standard chemical encodings (SMILES-to-graph conversion) with validated, citable transformation methods (e.g., RDKit).
- For any decision cutoffs introduced (e.g., feature importance threshold for topological motif identification), a sensitivity analysis MUST sweep the cutoff over a range of small threshold values and report how false-positive/false-negative rates vary across the sweep.
- If a proxy metric is used for adhesion energy, a validation step MUST confirm the proxy correlates with adhesion energy in the literature before the model is trained.