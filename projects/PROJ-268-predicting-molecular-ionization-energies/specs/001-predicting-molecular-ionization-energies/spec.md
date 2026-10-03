# Feature Specification: Predicting Molecular Ionization Energies with Graph Neural Networks

**Feature Branch**: `001-predicting-ionization-energies`  
**Created**: 2026-08-25  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Ionization Energies with Graph Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion, Validation, and Proxy Construction (Priority: P1)

The researcher needs to download the QM9 dataset, verify the existence of the `homo` column, and construct the target variable "Ionization Energy" using Koopmans' theorem ($IE \approx -\epsilon_{HOMO}$), while explicitly validating the approximation's validity on a hold-out subset against literature values before full-scale training.

**Why this priority**: The research question hinges on predicting ionization energy. If the proxy (HOMO) is invalid for this dataset or the data source is inaccessible, the study is untestable. This step resolves the construct validity risk identified in the panel concerns.

**Independent Test**: Can be fully tested by executing the data validation script and verifying that (1) the dataset loads successfully, (2) the `homo` column exists, (3) a calculated $R^2$ between $-\epsilon_{HOMO}$ and literature IE values (or a citation-backed error margin) meets a minimum threshold (e.g., $R^2 \ge 0.9$), and (4) the scaffold-based split is generated.

**Acceptance Scenarios**:

1. **Given** the QM9 dataset URL is accessible, **When** the ingestion script runs, **Then** the system downloads the data and verifies the presence of the `homo` column; if missing, the process halts with a `[NEEDS CLARIFICATION]` error rather than falling back to an unverified proxy.
2. **Given** the loaded data, **When** the validation step runs, **Then** the system computes the correlation between $-\epsilon_{HOMO}$ and known experimental IE values for a [deferred]-molecule subset (or cites a specific literature source quantifying the systematic error for QM9) and reports the $R^2$ or error margin.
3. **Given** the full dataset, **When** the scaffold-based split is applied using Bemis-Murcko scaffolds, **Then** the resulting training, validation, and test sets are disjoint in terms of molecular scaffolds, and the split sizes are at least 10,000 molecules for the training set to ensure statistical power.

---

### User Story 2 - CPU-Constrained GNN Training and Retrained Ablation (Priority: P2)

The researcher needs to train a Message-Passing Neural Network (MPNN) on the preprocessed data using only CPU resources, and perform ablation studies by **retraining** the model with specific structural features zeroed out (not just inference-time noise) to determine their predictive contribution, ensuring multiple stochastic runs for statistical validity.

**Why this priority**: This is the core experimental engine. It tests the hypothesis that 2D graphs are sufficient. Crucially, it resolves the panel concern regarding the mismatch between inference-time noise and feature importance by mandating retraining, and resolves the statistical power concern by requiring stochastic runs.

**Independent Test**: Can be tested by running the training script on a standard 2-core CPU runner and verifying that the model converges within the 6-hour limit, and that the ablation study produces a distinct performance drop with a valid p-value (from an unpaired t-test) when critical features are zeroed out across 5 stochastic runs.

**Acceptance Scenarios**:

1. **Given** a configured MPNN model and the training set, **When** training starts, **Then** the process completes within 6 hours on a 2-core, 7 GB RAM runner without GPU acceleration.
2. **Given** the trained model and the ablation protocol, **When** the ablation study runs with bond features zeroed out, **Then** the system retrains the model multiple times (multiple stochastic runs) and calculates the Mean Absolute Error (MAE) distribution for each run.
3. **Given** the MAE distributions from the clean and ablated models, **When** the statistical analysis runs, **Then** the system performs an unpaired t-test and reports the p-value; if $p < 0.05$, the feature is deemed predictive.
4. **Given** the model architecture, **When** training on a batch of 64 molecules, **Then** the CPU memory usage (Peak RSS) remains within acceptable limits, and the architecture choice (e.g., GCN, GAT) is documented in the model definition file.

---

### User Story 3 - Model Evaluation, Baseline Comparison, and Error Analysis (Priority: P3)

The researcher needs to evaluate the model's performance against a fingerprint-based linear regression baseline, analyze the correlation between prediction errors and molecular properties (size/flexibility), and perform a sensitivity analysis on the decision threshold for "success" (e.g., MAE < 0.5 eV).

**Why this priority**: This validates the model's accuracy relative to existing 2D methods and provides the chemical intuition required to answer the research question. It also addresses the multiplicity and threshold justification concerns.

**Independent Test**: Can be tested by executing the evaluation script and verifying that the output includes a comparison table of MAE/RMSE against the baseline, a correlation coefficient for error vs. flexibility, and a sensitivity analysis report showing how the "success" rate varies across a defined threshold range.

**Acceptance Scenarios**:

1. **Given** the trained GNN and the test set, **When** evaluation runs, **Then** the GNN's MAE is reported alongside the fingerprint-based linear regression baseline (ECFP4, radius 2).
2. **Given** the error distribution, **When** analyzed against molecule size, **Then** the system reports the Pearson correlation coefficient between the absolute error and the number of rotatable bonds (flexibility).
3. **Given** the decision threshold for "acceptable prediction" (MAE < 0.5 eV), **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over the set {0.4, 0.45, 0.5, 0.55, 0.6} and reports the variation in the "success" rate (percentage of molecules meeting the threshold).

---

### Edge Cases

- What happens when a molecule in the dataset has an undefined or missing `homo` value? (System must exclude it and log the count; if >5% of data is excluded, flag for review).
- How does the system handle a molecule with a non-standard valence that RDKit cannot parse? (System must exclude it and log the error).
- What happens if the 6-hour pipeline time limit is reached before completing all 5 ablation runs? (System must save the best checkpoint from completed runs, report the timeout status, and flag the statistical power as potentially compromised).
- How does the system handle a test molecule with a scaffold completely unseen in the training set (out-of-distribution)? (System must evaluate it but flag the potential for higher error in the final report).
- What happens if the calculated $R^2$ between $-\epsilon_{HOMO}$ and literature IE is below 0.9? (System must halt training and report a "Construct Validity Failure" with the specific $R^2$ value).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the QM9 dataset from `https://huggingface.co/datasets/deepchem/qm9`, extracting SMILES and the `homo` column, deriving the target variable as Ionization Energy (IE) using Koopmans' theorem ($IE \approx -\epsilon_{HOMO}$), and validating the proxy's $R^2 \ge 0.9$ against literature values on a representative molecular subset (See US-1).
- **FR-002**: System MUST convert SMILES strings into 2D molecular graph objects using RDKit, extracting atom types, bond types, and functional group fingerprints, ensuring the dataset size is at least 10,000 molecules for the training set (See US-1).
- **FR-003**: System MUST implement a Message-Passing Neural Network (MPNN) that operates exclusively on CPU, with a configurable batch size within a practical range suitable for the experimental setup.; the specific architecture (e.g., GCN, GAT) MUST be documented in the model definition file (See US-2).
- **FR-004**: System MUST perform scaffold-based splitting using Bemis-Murcko scaffolds with an 80/10/10 train/validation/test partition to ensure the test set contains chemical scaffolds not present in the training set (See US-1).
- **FR-005**: System MUST perform ablation studies by **retraining** the model with specific structural features (e.g., bond features) zeroed out during the training process, repeating the process for multiple stochastic runs to generate a distribution of MAE values (See US-2).
- **FR-006**: System MUST compute Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) on the test set and compare them against a fingerprint-based linear regression model (using ECFP fingerprints, radius 2) (See US-3).
- **FR-007**: System MUST perform an unpaired t-test on the MAE distributions from the clean model and the retrained ablated models (5 runs each) to determine statistical significance ($p < 0.05$) (See US-2).
- **FR-008**: System MUST enforce a hard timeout for the total training and evaluation pipeline, saving checkpoints if the limit is reached (See US-2).
- **FR-009**: System MUST analyze the correlation between the absolute prediction error and molecular size (molecular weight) and flexibility (number of rotatable bonds) and report the Pearson correlation coefficient (See US-3).
- **FR-010**: System MUST perform a sensitivity analysis on the "success" threshold (MAE < 0.5 eV) by sweeping the threshold over a range of values including 0.45, 0.5, 0.55, and 0.6 and reporting the variation in success rates (See US-3).
- **FR-011**: System MUST document the specific attribution method (e.g., Integrated Gradients) used for feature importance in the model definition file (See US-3).
- **FR-012**: System MUST exclude any molecule with a missing `homo` value and log the count; if the exclusion rate exceeds 5%, the system must flag a "Data Quality Warning" (See US-1).
- **FR-013**: System MUST ensure the total memory usage (Peak RSS) during the largest batch processing step remains within acceptable system limits (See US-2).
- **FR-014**: System MUST report the $R^2$ correlation between $-\epsilon_{HOMO}$ and literature IE values (or the cited error margin) as a primary metric of construct validity (See US-1).
- **FR-015**: System MUST compare the GNN's residuals against the baseline's residuals to determine if the GNN captures signal independent of the simple fingerprint baseline (See US-3).
- **FR-016**: System MUST calculate and report the absolute difference between the Test Set MAE and the Training Set MAE to quantify the generalization gap (See US-2).
- **FR-017**: System MUST ensure the ablation study includes at least 5 stochastic runs per configuration to enable valid statistical testing (See US-2).
- **FR-018**: System MUST explicitly state in the final report that the findings are associational (due to observational nature of the data) and not causal (See US-2).

### Key Entities

- **MoleculeGraph**: Represents a molecule with attributes for atom types, bond types, and connectivity, derived from SMILES.
- **IonizationEnergy**: A scalar value (in eV) representing the target property, derived from HOMO energy using Koopmans' theorem ($IE \approx -\epsilon_{HOMO}$).
- **AblationConfig**: Defines which structural features are zeroed out during a specific ablation run.
- **AttributionMap**: A mapping of atom/bond indices to gradient magnitudes indicating predictive contribution.
- **ValidationMetric**: Stores the $R^2$ value and error margin for the HOMO proxy validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the GNN model is measured against the fingerprint-based linear regression baseline to determine if 2D topology provides superior signal (See FR-006, US-3).
- **SC-002**: The predictive contribution of specific structural features is measured by the relative increase in MAE and the p-value from the unpaired t-test when those features are zeroed out and the model is retrained (See FR-005, FR-007, US-2).
- **SC-003**: The computational feasibility is measured by the total runtime of the training and evaluation pipeline against a 6-hour limit on a multi-core CPU runner (See FR-008, US-2).
- **SC-004**: The generalization capability is measured by the observed gap between the Test Set MAE and the Training Set MAE; the system MUST report the observed gap value (See FR-016, US-2).
- **SC-005**: The memory efficiency is measured by the peak RAM usage (Peak RSS) during the largest batch processing step against a 7 GB limit (See FR-013, US-2).
- **SC-006**: The construct validity of the target variable is measured by the $R^2$ correlation between $-\epsilon_{HOMO}$ and literature IE values (or the cited error margin) (See FR-014, US-1).
- **SC-007**: The error distribution analysis is measured by the Pearson correlation coefficient between absolute error and molecular size/flexibility (See FR-009, US-3).
- **SC-008**: The robustness of the "success" conclusion is measured by the variation in the success rate (percentage of molecules with MAE < 0.5 eV) across the threshold sweep {0.4, 0.45, 0.5, 0.55, 0.6} (See FR-010, US-3).
- **SC-009**: The statistical power of the ablation study is measured by the number of stochastic runs (must be $\ge$ a sufficient threshold) and the resulting p-value distribution (See FR-017, US-2).
- **SC-010**: The independence of the 2D signal is measured by the correlation between the GNN's residuals and the baseline's residuals (See FR-015, US-3).

## Assumptions

- The QM9 dataset at `https://huggingface.co/datasets/deepchem/qm9` contains the `homo` column and SMILES strings, and is accessible without authentication.
- The "ionization energy" target is derived from the HOMO energy using Koopmans' theorem ($IE \approx -\epsilon_{HOMO}$), which is scientifically valid for small organic molecules in the QM9 dataset with an expected $R^ \ge 0.9$ against literature values (validated per FR-014).
- The 2D graph representation (atom/bond types) is sufficient to capture the majority of the predictive signal for ionization energy in small, rigid molecules, as hypothesized.
- The PyTorch Geometric library and RDKit are available and compatible with the free-tier GitHub Actions runner environment (CPU-only).
- The scaffold-based split successfully separates chemical space such that the test set represents a true out-of-distribution challenge for the model.
- The 6-hour time limit is sufficient for training a small MPNN on a subset of QM9 (minimum 10,000 molecules) on a 2-core CPU, even with multiple stochastic ablation runs.
- No GPU acceleration is available or required; the model must converge using standard single-precision floating-point representation on CPU.
- The fingerprint-based linear regression baseline (ECFP4, radius 2) provides a valid 2D-only comparison point for the GNN.
- The findings of this study are associational, not causal, due to the observational nature of the QM9 dataset (no random assignment of molecular structures).
- The threshold for "successful prediction" (MAE < 0.5 eV) is a community-standard default for this domain, and the sensitivity analysis will confirm its robustness.
