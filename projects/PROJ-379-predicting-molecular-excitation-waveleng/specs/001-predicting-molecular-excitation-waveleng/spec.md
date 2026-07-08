# Feature Specification: Predicting Molecular Excitation Wavelengths from SMILES with Graph Neural Networks

**Feature Branch**: `001-predict-molecular-excitation-wavelengths`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Excitation Wavelengths from SMILES with Graph Neural Networks"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher must be able to ingest raw UV-Vis spectral data from public repositories (PubChem/SDBS), parse SMILES strings into molecular graphs using RDKit, and produce a clean, scaffold-split dataset ready for model training.

**Why this priority**: Without a validated, leakage-free dataset, no model training or evaluation is possible. This is the foundational step that ensures the scientific validity of the entire study.

**Independent Test**: The pipeline can be fully tested by running the ingestion script on a sample subset and verifying that the output CSV contains valid SMILES, corresponding λmax values, and scaffold IDs, with no duplicate structures or missing values.

**Acceptance Scenarios**:

1. **Given** a raw data file from PubChem containing SMILES and λmax values, **When** the ingestion script is executed, **Then** the output is a processed CSV where every row has a valid SMILES string, a numeric λmax value, and a scaffold identifier.
2. **Given** a dataset with duplicate molecules (same SMILES, different λmax), **When** the preprocessing runs, **Then** the system retains only the median λmax for duplicates and logs the count of resolved conflicts.
3. **Given** a dataset with >10,000 molecules, **When** the scaffold split is applied on a 2 vCPU, 7GB RAM environment, **Then** the system completes the preprocessing and split within 1 hour, ensuring no scaffold appears in more than one split.

---

### User Story 2 - Model Training and Evaluation (Priority: P2)

The researcher must be able to train a message-passing Graph Neural Network (GNN) on the processed dataset and evaluate its performance against a baseline linear model using Mean Absolute Error (MAE) and R² metrics.

**Why this priority**: This delivers the core scientific result: determining if graph structure predicts λmax. It must run on CPU-only hardware to be feasible within the project constraints.

**Independent Test**: The training job can be tested by executing the training script on a fixed random seed and verifying that the model converges (loss decreases) and produces a test MAE and R² score in the expected range.

**Acceptance Scenarios**:

1. **Given** the split dataset and a defined GNN architecture (2-3 layers, <1M parameters), **When** training is initiated on a CPU-only environment (2 vCPU, 7GB RAM), **Then** the model completes training within 4 hours and outputs a `model.pt` artifact.
2. **Given** the trained GNN model and a held-out test set, **When** evaluation is run, **Then** the system outputs MAE and R² values and compares them against a baseline ECFP+LinearRegression model.
3. **Given** a test molecule with known λmax, **When** the model predicts, **Then** the prediction error is calculated and stored in a results CSV for further analysis.

---

### User Story 3 - Feature Attribution and Sensitivity Analysis (Priority: P3)

The researcher must be able to analyze which molecular substructures (features) contribute most to the prediction for specific molecules and perform a sensitivity analysis on any introduced decision thresholds.

**Why this priority**: This provides interpretability and methodological robustness, ensuring the model isn't learning spurious correlations and that any thresholds used are justified.

**Independent Test**: The attribution script can be tested by running it on a representative subset of test molecules and verifying that it outputs a ranked list of contributing atoms/bonds for each molecule.

**Acceptance Scenarios**:

1. **Given** a trained GNN and a set of test molecules, **When** the attribution analysis (GNNExplainer or gradient-based) is run, **Then** the system outputs a visualization or data file highlighting the top 5 atoms/bonds contributing to the λmax prediction for each molecule.
2. **Given** decision cutoffs for error classification (MAE ≥ 30 nm, 40 nm, 50 nm), **When** the sensitivity analysis is run, **Then** the system sweeps these thresholds and reports the variation in false-positive/false-negative rates.
3. **Given** two subgraphs with latent embeddings showing cosine similarity > 0.9, **When** the redundancy check is run, **Then** the system aggregates these subgraphs and masks their individual attribution weights to prevent spurious independent effect claims.

### Edge Cases

- What happens when the input dataset contains SMILES strings that RDKit cannot parse (e.g., invalid valence)?
- How does the system handle molecules with no reported λmax (missing data) in the source file?
- How does the system behave if the dataset size is too large to fit into 7GB RAM (requires chunking or sampling)?
- What happens if the GNN training loss does not decrease after epochs (early stopping trigger)?

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest UV-Vis spectral data from PubChem or SDBS, parse SMILES into molecular graphs using RDKit, and output a clean CSV with scaffold IDs (See US-1)
- **FR-002**: System MUST split the dataset into train/validation/test sets (80/10/10) ensuring no molecular scaffold appears in more than one split to prevent data leakage (See US-1)
- **FR-003**: System MUST implement a message-passing GNN with 2-3 layers and <1M parameters that trains on 2 vCPU, 7GB RAM hardware without requiring GPU or CUDA and completes within 4 hours (See US-2)
- **FR-004**: System MUST evaluate the trained model against a baseline ECFP fingerprint + linear regression model and report MAE and R² metrics on the held-out test set (See US-2)
- **FR-005**: System MUST perform feature importance analysis using GNNExplainer or gradient-based attribution on a representative subset of test molecules to identify contributing substructures. (See US-3)
- **FR-006**: System MUST perform a sensitivity analysis sweeping MAE decision cutoffs over a representative range of nanometer-scale thresholds and report the variation in error rates (See US-3)
- **FR-007**: System MUST detect potential predictor collinearity in the baseline linear model (Pearson r ≥ 0.9) and flag it; for the GNN, it MUST detect subgraph redundancy (latent cosine similarity > 0.9) and mask attribution weights for redundant subgraphs to prevent spurious independent claims (See US-3)

### Key Entities

- **Molecule**: Represents a chemical entity defined by its SMILES string, molecular graph structure (atoms, bonds), and experimental λmax value.
- **Scaffold**: Represents the Bemis-Murcko scaffold of a molecule, used to ensure structural diversity across train/validation/test splits.
- **Prediction**: Represents the model's output for a specific molecule, including predicted λmax, error relative to ground truth, and feature attribution weights.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model prediction accuracy (MAE) is measured against the target of <30 nm on the held-out test set (n≥50 samples, 95% confidence interval, Wilcoxon signed-rank test against baseline), with a failure threshold defined as >50 nm. *Regime of Validity*: Thresholds apply to conjugated systems where experimental noise floor is ±15 nm (See US-2)
- **SC-002**: Computational feasibility is measured against the constraint of ≤6 hours wall-clock time on a GitHub Actions free-tier runner (2 CPU, 7GB RAM) (See US-2)
- **SC-003**: Data validity is measured against the requirement that all molecules in the final training set have valid RDKit-parsable SMILES and numeric λmax values (See US-1)
- **SC-004**: Methodological robustness is measured by the presence of a sensitivity analysis report showing error rate variation across a threshold sweep of representative nanoscale values. (See US-3)
- **SC-005**: Baseline comparison is measured by the GNN's performance relative to the ECFP+LinearRegression baseline, requiring a statistically significant improvement (α=0.05, paired Wilcoxon signed-rank test on MAE differences) or clear explanation of parity (See US-2)

## Assumptions

- The public datasets (PubChem/SDBS) contain sufficient molecules with both valid SMILES and experimentally measured λmax values to train a GNN (a substantial number of molecules).
- The molecular graph structure (atom types, bond orders, connectivity) contains sufficient signal to predict λmax without requiring explicit quantum mechanical descriptors (e.g., orbital energies).
- The GNN architecture (2-3 layers, <1M parameters) is small enough to train on a CPU-only environment (2 vCPU, 7GB RAM) within the 4-hour training time limit.
- The scaffold-based split strategy (Bemis-Murcko) is sufficient to prevent structural leakage and ensure the model generalizes to unseen chemical series.
- The MAE thresholds (<30 nm target, >50 nm failure) are justified by the experimental noise floor of UV-Vis measurements (±15 nm) for conjugated systems.
- The RDKit library is available and functional within the GitHub Actions environment for parsing SMILES and generating molecular graphs.
- The dataset size will fit within the 7GB RAM constraint of the free-tier runner without requiring chunking or sampling.