# Feature Specification: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

**Feature Branch**: `001-predict-molecular-refractive-indices`  
**Created**: 2026-10-08  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Refractive Indices from Graph-Based Molecular Representations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CPU-Feasible Model Training and Baseline Comparison (Priority: P1)

A researcher needs to train a lightweight Message Passing Neural Network (MPNN) on a curated dataset of organic molecules and compare its predictive accuracy against a traditional atomic contribution baseline, all within a strict CPU-only environment (max 7GB RAM, 6h runtime) to determine if graph-based methods are viable for refractive index prediction without GPU resources.

**Why this priority**: This is the core feasibility study. If the model cannot be trained or the baseline cannot be established within the hardware constraints, the project cannot proceed to interpretability analysis. It addresses the "CPU-only" gap identified in the motivation.

**Independent Test**: Can be fully tested by executing the training pipeline on a GitHub Actions runner, verifying that the process completes within 6 hours, memory usage stays below 7GB, and produces two CSV artifacts (GNN predictions and Baseline predictions) with valid MAE/RMSE metrics.

**Acceptance Scenarios**:

1. **Given** a GitHub Actions runner with 2 CPU cores and 7GB RAM, **When** the training script is executed with the specified dataset and MPNN configuration (3 layers, hidden dim 64), **Then** the job must complete within 6 hours without OOM errors and output a test set MAE.
2. **Given** the same dataset, **When** the atomic contribution baseline is calculated, **Then** it must produce a prediction file with a valid MAE that can be directly compared to the GNN result.
3. **Given** the training completes, **When** the results are aggregated, **Then** a paired t-test must be generated comparing the GNN MAE against the baseline MAE with a p-value < 0.05 indicating statistical significance (or lack thereof).

---

### User Story 2 - Feature Attribution and Structural Driver Identification (Priority: P2)

A chemist needs to identify which specific molecular graph features (e.g., conjugated systems, halogen substitutions) drive the refractive index predictions by applying Integrated Gradients to the trained model, ensuring the results are interpretable and not just a black-box output.

**Why this priority**: This addresses the primary research question regarding "structure-property relationships." Without this, the project only proves prediction accuracy, not the interpretability gap it aims to fill.

**Independent Test**: Can be fully tested by running the attribution script on a held-out validation set, generating a feature importance bar chart and a CSV of attribution scores, and verifying that specific chemical substructures (like benzene rings or halogens) appear as top contributors.

**Acceptance Scenarios**:

1. **Given** a trained MPNN model and a test molecule, **When** Integrated Gradients are applied, **Then** the system must output a normalized importance score for each node and edge feature.
2. **Given** a set of molecules known to contain conjugated pi-systems, **When** the attribution analysis is run, **Then** the top-ranked features must correspond to the atoms and bonds within those conjugated systems, specifically: at least 80% of the top-10 attributed nodes must belong to conjugated substructures.
3. **Given** the attribution scores, **When** the results are aggregated across the test set, **Then** a summary report must identify the top 5 most influential graph features for refractive index prediction.

---

### User Story 3 - Methodological Robustness and Sensitivity Analysis (Priority: P3)

A reviewer needs to verify that the model's performance claims are robust to hyperparameter variations and that the dataset split prevents data leakage, ensuring the reported accuracy is not an artifact of specific random seeds or scaffold overlap.

**Why this priority**: This ensures the scientific validity of the results. Without sensitivity analysis and proper splitting, the findings may not be generalizable or reproducible.

**Independent Test**: Can be fully tested by re-running the training with different random seeds and verifying that the MAE variance is within a defined tolerance, and by checking that the scaffold split ensures no molecular scaffolds appear in both training and test sets.

**Acceptance Scenarios**:

1. **Given** the training pipeline, **When** executed with 3 different random seeds, **Then** the variance in test set MAE must be negligible, demonstrating stability.
2. **Given** the dataset split logic, **When** the scaffolds of the training and test sets are compared, **Then** there must be zero overlap in molecular scaffolds between the two sets.
3. **Given** the final performance metrics, **When** the sensitivity analysis is run (sweeping a decision threshold or regularization parameter), **Then** the report must show how the MAE changes across the sweep, confirming no single parameter setting is an outlier.

### Edge Cases

- **What happens when** the dataset contains molecules with molecular weight > 500 Da? **System handles** this by filtering them out during preprocessing and logging the count of excluded molecules to ensure the 7GB RAM constraint is met.
- **How does system handle** a molecule with undefined bond orders or invalid SMILES strings? **System handles** this by catching RDKit parsing errors, skipping the invalid entry, and logging the specific error to a `failed_parsing.log` file without crashing the pipeline.
- **What happens when** the GNN fails to converge or overfits significantly on the training set? **System handles** this by triggering early stopping (patience=10) and flagging the run as "Potential Overfit" if the validation loss increases for 10 consecutive epochs, outputting a warning in the final report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse a curated CSV dataset containing molecular SMILES and experimental refractive index values using `wget` and RDKit, filtering for organic molecules with molecular weight < 500 Da to ensure memory compliance. (See US-1)
- **FR-002**: System MUST implement a 3-layer Message Passing Neural Network (MPNN) with a hidden dimension of 64 using PyTorch Geometric, explicitly disabling CUDA to enforce CPU-only execution. (See US-1)
- **FR-003**: System MUST perform a scaffold-based split with 80/10/10 ratios (train/validation/test) to prevent data leakage and ensure structural diversity between sets. (See US-3)
- **FR-004**: System MUST implement a traditional group contribution baseline (e.g., Molar Refractivity via additive atomic fragments) using distinct physical descriptors to serve as a non-learning comparison. (See US-1)
- **FR-005**: System MUST apply Integrated Gradients to the trained MPNN to compute feature importance scores for each node and edge in the molecular graph. (See US-2)
- **FR-006**: System MUST calculate Mean Absolute Error (MAE) and Root Mean Square Error (RMSE) for both the GNN and the baseline on the test set and perform a paired t-test to determine statistical significance. (See US-1)
- **FR-007**: System MUST generate a parity plot (Predicted vs. Actual) and a feature importance bar chart as PNG artifacts with file sizes < 5MB. (See US-2)

### Key Entities

- **MoleculeGraph**: Represents a molecule with node features (atomic number, degree, hybridization) and edge features (bond type, conjugation).
- **RefractiveIndexSample**: A data point containing the SMILES string, experimental refractive index value, and associated molecular weight.
- **FeatureAttribution**: A record linking a specific graph feature (atom/bond) to its calculated importance score for a given prediction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The GNN model's test set MAE is measured against the traditional atomic contribution baseline MAE to determine if the graph-based method provides a statistically significant improvement (p < 0.05). (See US-1)
- **SC-002**: The variance in test set MAE across 3 independent random seeds is measured against a tolerance of 0.01 to confirm model stability. (See US-3)
- **SC-003**: The feature attribution scores are measured against independent physical measurements or properties not explicitly encoded as features to verify that the model identifies chemically plausible structural drivers. (See US-2)
- **SC-004**: The total execution time of the training and evaluation pipeline is measured against the 6-hour GitHub Actions time limit to confirm CPU feasibility. (See US-1)
- **SC-005**: The memory usage of the training process is measured against the 7GB RAM limit to ensure the method fits within free-tier CI constraints. (See US-1)

## Assumptions

- The public dataset (e.g., from NIST or Zenodo) contains sufficient experimental refractive index values and corresponding SMILES strings for organic molecules with MW < 500 Da to train a model with at least 500 samples.
- The RDKit library is available in the GitHub Actions environment and can parse the SMILES strings without requiring GPU acceleration.
- The "atomic contribution method" baseline can be implemented using standard additive rules (e.g., Lorentz-Lorenz) available in public literature without requiring proprietary data.
- The dataset does not contain significant missing values for refractive index; any missing values will be imputed or the molecule excluded.
- The specific threshold for "statistical significance" is fixed at p < 0.05 for the paired t-test, consistent with standard scientific practice.
- The Integrated Gradients implementation in PyTorch Geometric or a compatible library is sufficient for graph-level attribution without requiring custom CUDA kernels.
- The public dataset contains experimental refractive index values. If values are recorded at temperatures other than 20°C (standard reference), the system MUST apply the Edlén equation or a standard linear temperature coefficient (dn/dT is negative for organic liquids.) to normalize all values to 20°C before training. If temperature data is unavailable, the system MUST flag the sample for exclusion or estimate uncertainty using a range of coefficients (±0.0001 K⁻¹) to account for chemical class variation. This normalization is applied automatically during the preprocessing step defined in FR-001. (See US-1)