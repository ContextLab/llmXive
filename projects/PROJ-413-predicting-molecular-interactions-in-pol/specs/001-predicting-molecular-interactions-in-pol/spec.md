# Feature Specification: Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks

**Feature Branch**: `[001-polymer-interaction-gnn]`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Pipeline Construction (Priority: P1)

As a materials researcher, I need to download and curate molecular graph data from public benchmarks (MolNet via HuggingFace Datasets) and filter for polymer-relevant structures so that I have a valid dataset for training the predictive model.

**Why this priority**: Without a properly curated dataset containing both molecular topology data and corresponding adhesion energy measurements, no downstream analysis is possible. This is the foundational data layer.

**Independent Test**: Can be fully tested by verifying the data pipeline executes without errors, produces a dataset with ≥500 polymer-filler interface pairs, and confirms all required variables (node types, edge types, adhesion energy values) are present in the curated subset.

**Acceptance Scenarios**:

1. **Given** the MolNet benchmark is accessible via HuggingFace Datasets API, **When** the data download and filtering script executes, **Then** the output dataset contains ≥500 polymer-filler interface pairs with complete molecular graph structures and adhesion energy measurements
2. **Given** a dataset subset, **When** the variable validation check runs, **Then** every required predictor variable (atom types, bond types, connectivity patterns) AND outcome variable (adhesion energy) are present with no missing values >5%

---

### User Story 2 - Model Training Execution (Priority: P2)

As a computational materials scientist, I need to train a 3-layer Graph Convolutional Network (GCN) on the curated polymer-filler interface data using CPU-only execution so that I can learn the mapping from molecular topology to adhesion energy.

**Why this priority**: This delivers the core predictive capability. Without a trained model, there is no structure-property relationship to analyze or validate.

**Independent Test**: Can be fully tested by executing the training script on a CPU-only environment and confirming the model completes training within 4 hours, uses ≤6 GB RAM at peak, and achieves training loss convergence (MSE reduction ≥50% from initial epoch to final epoch).

**Acceptance Scenarios**:

1. **Given** the curated dataset and GPU-free environment, **When** the 3-layer GCN training script executes with batch size ≤32, **Then** the model completes training within 4 hours on 2 CPU cores with peak memory usage ≤6 GB
2. **Given** the 80/20 train-test split, **When** the model trains for 50 epochs, **Then** the validation loss shows monotonic decrease or plateau (no increase >10% from minimum) indicating convergence

---

### User Story 3 - Statistical Validation & Attribution (Priority: P3)

As a peer reviewer, I need to verify that the model's predictive performance is statistically significant (not random chance) and identify which topological features drive predictions so that the structure-property relationship is scientifically defensible.

**Why this priority**: This provides scientific rigor and interpretability. Without statistical validation and feature attribution, the model's predictions lack credibility for materials design decisions.

**Independent Test**: Can be fully tested by running the permutation test (1000 iterations) and gradient-based attribution analysis, confirming the model outperforms random chance (p < 0.05) and produces interpretable feature importance rankings.

**Acceptance Scenarios**:

1. **Given** the trained model and test set, **When** the permutation test executes with 1000 iterations, **Then** the observed model performance exceeds [deferred] of permuted baseline performances (p < 0.05)
2. **Given** a trained GCN model, **When** gradient-based attribution analysis runs on 100 test samples, **Then** the output identifies ≥3 topological features (e.g., node degree, edge connectivity, graph density) with importance scores that vary meaningfully across samples

---

### Edge Cases

- What happens when the MolNet dataset does not contain sufficient polymer-filler interface pairs with adhesion energy measurements? → The system MUST halt with a clear error message and log the missing variable count; this triggers a `[NEEDS CLARIFICATION]` review
- How does the system handle missing adhesion energy values in the curated dataset? → Records missing data count; if missing >5%, the system MUST flag for imputation review or dataset expansion
- What happens when the 6-hour GitHub Actions runtime limit is exceeded during training? → The system MUST checkpoint model state every 10 epochs and resume from checkpoint on restart; if total time >6 hours, the job MUST fail with a timeout error
- How does the system handle collinearity between graph topology predictors (e.g., node degree and connectivity patterns)? → The system MUST compute variance inflation factor (VIF) for all predictors; if VIF >5 for any predictor, the system MUST flag for joint descriptive analysis instead of independent effect claims

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download molecular graph data from MolNet benchmark via HuggingFace Datasets API and filter for polymer-relevant structures (See US-1)
- **FR-002**: System MUST construct heterogeneous graphs encoding atom types as nodes and bonds/interactions as edges for each polymer-filler interface pair (See US-1)
- **FR-003**: System MUST implement a 3-layer Graph Convolutional Network using PyTorch Geometric with CPU-only execution (no CUDA, no GPU device_map) (See US-2)
- **FR-004**: System MUST train the model using 80/20 train-test split with mean squared error (MSE) loss and batch size ≤32 (See US-2)
- **FR-005**: System MUST execute a permutation test with 1000 iterations to validate model performance exceeds random chance (See US-3)
- **FR-006**: System MUST perform gradient-based attribution analysis to identify topological features driving adhesion predictions (See US-3)
- **FR-007**: System MUST compute variance inflation factor (VIF) for all graph topology predictors and flag collinearity if VIF >5 (See US-3)

### Key Entities *(include if feature involves data)*

- **MolecularGraph**: Represents a polymer or filler molecule with node attributes (atom type, charge, hybridization) and edge attributes (bond type, bond order)
- **InterfacePair**: Represents a polymer-filler interface with two MolecularGraph entities and an associated adhesion energy measurement (outcome variable)
- **TrainedGCN**: The output model artifact with learned weights mapping graph topology features to adhesion energy predictions

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the requirement that all predictor variables (atom types, bond types, connectivity patterns) AND outcome variable (adhesion energy) are present with ≤5% missing values (See US-1)
- **SC-002**: Model training feasibility is measured against the constraint that total runtime ≤4 hours and peak memory ≤6 GB on 2 CPU cores (See US-2)
- **SC-003**: Model statistical significance is measured against the permutation test baseline with 1000 iterations, requiring p < 0.05 (See US-3)
- **SC-004**: Predictor collinearity is measured against VIF threshold of 5; if exceeded, joint descriptive framing is required instead of independent effect claims (See US-3)
- **SC-005**: Multiple-comparison correction is measured against family-wise error rate control; if >1 hypothesis test is run, Bonferroni or Holm correction MUST be applied (See US-3)

## Assumptions

- The MolNet benchmark or curated NIST Chemistry WebBook subset contains sufficient polymer-filler interface pairs (≥500) with both molecular graph structures AND adhesion energy measurements; if not, this triggers a `[NEEDS CLARIFICATION: does the dataset contain adhesion energy measurements for polymer-filler interfaces?]`
- This is an observational study (no random assignment of molecular structures); therefore findings MUST be framed as ASSOCIATIONAL, not causal, in all reporting and conclusions
- The 3-layer GCN architecture is sufficiently lightweight to execute within 6 hours on GitHub Actions free-tier (2 CPU, 7 GB RAM) without GPU acceleration
- Molecular graph representations use standard chemical encodings (SMILES-to-graph conversion) with validated, citable transformation methods (e.g., RDKit)
- Graph topology predictors (node degree, connectivity patterns) may exhibit collinearity; the analysis MUST use joint descriptive framing rather than claiming independent predictive effects for definitionally related variables
- The adhesion energy outcome variable uses validated measurement scales from experimental or simulation literature with citable sources
- For any decision cutoffs introduced (e.g., feature importance threshold for topological motif identification), a sensitivity analysis MUST sweep the cutoff over {0.01, 0.05, 0.1} and report how false-positive/false-negative rates vary across the sweep
- Power analysis sample size requirement is [deferred] pending dataset availability; the analysis MUST acknowledge power limitations if n < 200 interface pairs
