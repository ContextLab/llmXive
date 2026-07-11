# Feature Specification: Predicting Molecular Ionization Energies with Graph Neural Networks

**Feature Branch**: `001-predicting-ionization-energies`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Ionization Energies with Graph Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher needs to download the QM9 dataset, parse SMILES strings into 2D molecular graphs using RDKit, and extract atom/bond features to create a clean, CPU-tractable training dataset.

**Why this priority**: Without a valid, preprocessed dataset, no model training or analysis can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: Can be fully tested by executing the data loader script and verifying that the output file contains the specified subset size of valid molecular graph objects with corresponding ionization energy labels (derived from HOMO), and that the total memory footprint remains within a manageable range.

**Acceptance Scenarios**:

1. **Given** the QM9 dataset URL is accessible, **When** the ingestion script runs, **Then** the system downloads and parses the data into a structured format (e.g., PyTorch Geometric `Data` objects) without memory overflow.
2. **Given** a raw SMILES string with invalid characters, **When** the preprocessing step runs, **Then** the molecule is either corrected (if possible) or excluded, and a log entry is generated detailing the exclusion reason.
3. **Given** the full QM9 dataset, **When** the scaffold-based split is applied using Bemis-Murcko scaffolds, **Then** the resulting training, validation, and test sets are disjoint in terms of molecular scaffolds, ensuring no data leakage.

---

### User Story 2 - CPU-Constrained GNN Training and Ablation (Priority: P2)

The researcher needs to train a Message-Passing Neural Network (MPNN) on the preprocessed data using only CPU resources, and perform ablation studies by retraining the model with specific structural features zeroed out to determine their predictive contribution.

**Why this priority**: This is the core experimental engine. It tests the hypothesis that 2D graphs are sufficient and identifies feature importance, directly addressing the research question.

**Independent Test**: Can be tested by running the training script on a standard 2-core CPU runner and verifying that the model converges (loss decreases) within the allocated time limit, and that the ablation study produces a distinct performance drop when critical features are zeroed out and retrained.

**Acceptance Scenarios**:

1. **Given** a configured MPNN model and the training set, **When** training starts, **Then** the process completes within 6 hours on a 2-core, 7 GB RAM runner without GPU acceleration. The timer starts from the beginning of the first epoch and ends at the save of the final checkpoint, excluding data download time.
2. **Given** the trained model and the ablation protocol, **When** the ablation study runs with bond features zeroed out and the model retrained for 5 stochastic runs, **Then** the system calculates and reports the Mean Absolute Error (MAE) for each run and the unpaired t-test p-value comparing the clean model MAE distribution against the perturbed model MAE distribution.
3. **Given** the model architecture, **When** training on a batch of 64 molecules, **Then** the CPU memory usage (Peak RSS measured via psutil) remains within acceptable limits.
4. **Given** the evaluation pipeline is triggered, **When** the evaluation phase starts, **Then** the timer starts at the beginning of the first evaluation step (baseline inference or ablation inference) and ends at the generation of the final report, ensuring the total evaluation phase does not exceed a reasonable duration.

---

### User Story 3 - Model Evaluation and Attribution Analysis (Priority: P3)

The researcher needs to evaluate the model's performance against a fingerprint-based linear regression baseline, and generate gradient-based attribution maps to visualize which atoms/bonds drive predictions.

**Why this priority**: This validates the model's accuracy relative to existing 2D methods and provides the chemical intuition (feature importance) required to answer the research question.

**Independent Test**: Can be tested by executing the evaluation script and verifying that the output includes a comparison table of MAE/RMSE against the baseline and a set of visualizations (or numerical scores) indicating feature importance.

**Acceptance Scenarios**:

1. **Given** the trained GNN and the test set, **When** evaluation runs, **Then** the GNN's MAE is reported alongside the fingerprint-based linear regression baseline.
2. **Given** a specific molecule from the test set, **When** the attribution analysis runs, **Then** the system outputs a heatmap or list of atoms/bonds ranked by their gradient contribution to the predicted ionization energy.
3. **Given** the error distribution, **When** analyzed against molecule size, **Then** the system reports the correlation coefficient between the absolute error and the number of rotatable bonds (flexibility) or molecular weight (size).

---

### Edge Cases

- What happens when a molecule in the dataset has an undefined or missing ionization energy value? (System must exclude it and log the count).
- How does the system handle a molecule with a non-standard valence that RDKit cannot parse? (System must exclude it and log the error).
- What happens if the 12-hour pipeline time limit is reached before completion? (System must save the best checkpoint and report the time-out status).
- How does the system handle a test molecule with a scaffold completely unseen in the training set (out-of-distribution)? (System must evaluate it but flag the potential for higher error).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the QM9 dataset from `https://huggingface.co/datasets/deepchem/qm9`, extracting SMILES and the `homo` column, deriving the target variable as Ionization Energy (IE) using Koopmans' theorem (IE ≈ -HOMO), ensuring all data fits within 7 GB RAM (See US-1).
- **FR-002**: System MUST convert SMILES strings into 2D molecular graph objects using RDKit, extracting atom types, bond types, and functional group fingerprints (See US-1).
- **FR-003**: System MUST implement a Message-Passing Neural Network (MPNN) that operates exclusively on CPU, with a configurable batch size ≤ 64 to prevent memory overflow; the specific architecture (e.g., GCN, GAT) MUST be documented in the model definition (See US-2).
- **FR-004**: System MUST perform scaffold-based splitting using Bemis-Murcko scaffolds with an 80/10/10 train/validation/test partition to ensure the test set contains chemical scaffolds not present in the training set (See US-2).
- **FR-005**: System MUST perform ablation studies by retraining the model with specific structural features (e.g., bond features) zeroed out during the training process to measure predictive contribution (See US-2).
- **FR-006**: System MUST compute Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) on the test set and compare them against a fingerprint-based linear regression model (using ECFP4 fingerprints, radius 2) (See US-3).
- **FR-007**: System MUST generate gradient-based attribution scores for each atom and bond in the test set using Integrated Gradients to quantify feature importance (See US-3).
- **FR-008**: System MUST enforce a hard timeout for the training phase and a hard timeout for the evaluation phase, ensuring the total pipeline time remains within a predefined operational window. (See US-2).
- **FR-009**: System MUST perform ablation studies by retraining the model with bond features zeroed out, repeating the process for 5 stochastic runs to generate a distribution of MAE values (See US-2).
- **FR-010**: System MUST calculate and report the difference in MAE between the training set and the test set to quantify the generalization gap (See US-2).
- **FR-011**: System MUST analyze the correlation between the absolute prediction error and molecular size (molecular weight) and flexibility (number of rotatable bonds) (See US-3).
- **FR-012**: System MUST execute the ablation study with 5 stochastic runs per ablation configuration to enable valid statistical testing using an unpaired t-test (See US-2).
- **FR-013**: System MUST ensure the dataset size is at least 10,000 molecules (or the full dataset if smaller) to maintain statistical power ≥ 0.8 for detecting effect sizes of 0.05 eV (See US-2).
- **FR-014**: System MUST validate the Koopmans' theorem approximation (IE ≈ -HOMO) by calculating the R² correlation between -HOMO and known experimental IE values in a subset, or by citing a literature source that quantifies the systematic error margin for this approximation in organic molecules (See US-1).
- **FR-015**: System MUST analyze the residuals of the fingerprint-based baseline and compare them with the GNN's errors to determine if the GNN captures signal independent of the simple fingerprint baseline (See US-3).
- **FR-016**: System MUST perform robustness testing by applying Gaussian noise (σ=0.1) to bond features during the inference phase (forward pass) and measuring the increase in MAE, distinct from the feature importance ablation in FR-005 (See US-2).
- **FR-017**: System MUST calculate and report the Pearson correlation coefficient between the absolute prediction error and molecular size (molecular weight) and flexibility (number of rotatable bonds) (See US-3).
- **FR-018**: System MUST calculate and report the absolute difference between the Test Set MAE and the Training Set MAE to quantify the generalization gap (See US-2).
- **FR-019**: System MUST perform the specific ablation study defined in US-2 Scenario 2 by retraining the model with Gaussian noise (σ=0.1) added to bond features during the training process to measure robustness to training noise (See US-2).
- **FR-020**: System MUST analyze the correlation between the absolute prediction error and molecular size (molecular weight) and flexibility (number of rotatable bonds) and report the coefficient (See US-3).
- **FR-021**: System MUST calculate and report the generalization gap (absolute difference between Test Set MAE and Training Set MAE) to support the measurement in SC-004 (See US-2).

### Key Entities

- **MoleculeGraph**: Represents a molecule with attributes for atom types, bond types, and connectivity, derived from SMILES.
- **IonizationEnergy**: A scalar value (in eV) representing the target property, derived from HOMO energy using Koopmans' theorem (IE ≈ -HOMO).
- **AblationConfig**: Defines which structural features are zeroed out during a specific ablation run.
- **AttributionMap**: A mapping of atom/bond indices to gradient magnitudes indicating predictive contribution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the GNN model is measured against the fingerprint-based linear regression baseline (See FR-006, US-3).
- **SC-002**: The predictive contribution of specific structural features is measured by the relative increase in MAE when those features are zeroed out and the model is retrained (See FR-005, US-2).
- **SC-003**: The computational feasibility is measured by the total runtime of the training and evaluation pipeline against a predefined time limit on a 2-core CPU runner. (See FR-008, US-2).
- **SC-004**: The generalization capability is measured by the observed gap between the Test Set MAE and the Training Set MAE; the system MUST report the observed gap value (See FR-021, US-2).
- **SC-005**: The memory efficiency is measured by the peak RAM usage (Peak RSS) during the largest batch processing step against a predefined memory limit. (See FR-003, US-2).
- **SC-006**: The ablation study results are measured by the statistical significance (p-value from unpaired t-test) of the MAE increase when bond features are zeroed out across 5 stochastic runs (See FR-009, US-2).
- **SC-007**: The error distribution analysis is measured by the correlation coefficient between absolute error and molecular size/flexibility (See FR-017, US-3).
- **SC-008**: The validity of the target variable is measured by the R² correlation between -HOMO and experimental IE (or the cited literature error margin) (See FR-014).
- **SC-009**: The robustness to feature noise is measured by the increase in MAE when Gaussian noise (σ=0.1) is applied to bond features during inference (See FR-016, US-2).
- **SC-010**: The robustness to training noise is measured by the increase in MAE when Gaussian noise (σ=0.1) is applied to bond features during the training process (See FR-019, US-2).
- **SC-011**: The error distribution correlation is measured by the Pearson correlation coefficient between absolute error and molecular size/flexibility (See FR-020, US-3).

## Assumptions

- The QM9 dataset at `https://huggingface.co/datasets/deepchem/qm9` contains the `homo` column and SMILES strings, and is accessible without authentication.
- The "ionization energy" target is derived from the HOMO energy using Koopmans' theorem (IE ≈ -HOMO), which is validated per FR-014.
- The 2D graph representation (atom/bond types) is sufficient to capture the majority of the predictive signal for ionization energy in small, rigid molecules, as hypothesized.
- The PyTorch Geometric library and RDKit are available and compatible with the free-tier GitHub Actions runner environment (CPU-only).
- The scaffold-based split successfully separates chemical space such that the test set represents a true out-of-distribution challenge for the model.
- The 6-hour time limit is sufficient for training a small MPNN on a subset of QM9 (minimum 10,000 molecules) on a 2-core CPU.
- No GPU acceleration is available or required; the model must converge using standard float32 precision on CPU.
- The fingerprint-based linear regression baseline (ECFP4, radius 2) provides a valid 2D-only comparison point for the GNN.
- The Koopmans' theorem approximation (IE ≈ -HOMO) is scientifically valid for the QM9 dataset within the expected error margin, as confirmed by FR-014.