# Feature Specification: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

**Feature Branch**: `001-predict-molecular-diffusion`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Featurization Pipeline (Priority: P1)

As a researcher, I want to ingest a curated dataset of experimental diffusion coefficients and automatically convert molecular structures and solvent properties into graph representations and scalar descriptors, so that the data is ready for model training without manual preprocessing.

**Why this priority**: This is the foundational step; without valid, featurized data, no model can be trained or evaluated. It directly addresses the "Data Acquisition" and "Featurization" phases of the methodology.

**Independent Test**: Can be fully tested by running the ingestion script on a representative sample of molecules and verifying that the output files contain valid graph structures (nodes/edges) and numerical solvent descriptors, with no missing values in critical fields.

**Acceptance Scenarios**:

1. **Given** a CSV file containing SMILES strings for solutes, solvent types, and experimental diffusion coefficients, **When** the ingestion script is executed, **Then** the system outputs a JSONL file where each record contains a PyTorch Geometric Data object for the molecule and a dictionary of solvent descriptors (viscosity, dielectric constant).
2. **Given** a dataset entry with an invalid SMILES string (e.g., unclosed brackets), **When** the ingestion script is executed, **Then** the record is flagged as an error in a separate log file, and the script continues processing the remaining valid entries without crashing.
3. **Given** a dataset where a solvent property (e.g., viscosity) is missing, **When** the ingestion script is executed, **Then** the record is excluded from the dataset and logged with the tag `[MISSING_DATA_EXCLUDED]`, ensuring the training set contains only complete feature vectors.

---

### User Story 2 - CPU-Optimized GNN Training and Baseline Comparison (Priority: P2)

As a researcher, I want to train a lightweight Message Passing Neural Network (MPNN) on CPU hardware and compare its performance against a linear regression baseline, so that I can determine if static structural features encode dynamic transport properties better than simple fingerprints.

**Why this priority**: This is the core scientific experiment. It validates the research question by comparing the proposed GNN approach against a standard baseline, directly addressing the "Expected results" and "Methodology sketch" regarding correlation and model comparison.

**Independent Test**: Can be fully tested by executing the training script on a subset of the data (≤ 5,000 molecules) and verifying that the training completes in ≤ 30 minutes on a standard CPU, producing a model artifact and a results report containing RMSE and Pearson r values for both the GNN and the baseline.

**Acceptance Scenarios**:

1. **Given** a featurized dataset of ≤ 5,000 molecules and a single-layer MPNN architecture configured for CPU execution, **When** the training script runs for 50 epochs, **Then** the training loss decreases monotonically (or plateaus) without memory errors, and the final model is saved to disk.
2. **Given** the trained GNN model and a baseline linear regression model trained on the same data (including solvent descriptors), **When** both are evaluated on the held-out test set, **Then** the system outputs a comparison report containing the Pearson correlation coefficient (r) and Root Mean Squared Error (RMSE) for both models.
3. **Given** the performance metrics of the GNN and the baseline, **When** the statistical testing module runs, **Then** it performs a paired t-test on the per-sample absolute errors and reports a p-value indicating whether the GNN's improvement over the baseline is statistically significant (p < 0.05).

---

### User Story 3 - Sensitivity Analysis and Methodological Robustness Check (Priority: P3)

As a researcher, I want to perform a sensitivity analysis on key hyperparameters (e.g., message passing steps, learning rate) and verify that the model's performance is robust to small variations, so that the findings are not artifacts of a specific parameter tuning.

**Why this priority**: This ensures the scientific validity and reproducibility of the results, addressing the "Methodological soundness" requirement for threshold justification and sensitivity analysis, and ensuring the results are not due to overfitting a specific configuration.

**Independent Test**: Can be fully tested by running the sensitivity analysis script with a defined set of parameter variations and verifying that the output report shows how performance metrics (r and RMSE) fluctuate across the tested range, confirming stability.

**Acceptance Scenarios**:

1. **Given** the trained GNN model and a set of perturbed hyperparameters (e.g., message passing steps ∈ {the minimal step, 2, 3}), **When** the sensitivity analysis script runs, **Then** it re-evaluates the model (or trains small variants) and outputs a table showing the change in Pearson r and RMSE for each variation.
2. **Given** a dataset with potential outliers, **When** the robustness check is executed, **Then** the system reports the correlation coefficient both with the full dataset and after removing the top [deferred] of residuals, confirming stability.
3. **Given** the final results, **When** the report is generated, **Then** it explicitly states whether the observed correlation (r > 0.7) is stable across the tested hyperparameter range and the ablation study, or if the result is highly sensitive to specific configuration choices.

---

### Edge Cases

- What happens if the dataset contains molecules with extremely high molecular weights that exceed the memory capacity of the runner? (System must sample or truncate the graph).
- How does the system handle solvents with missing viscosity or dielectric constant data in the source CSV? (Must exclude and log with `[MISSING_DATA_EXCLUDED]`).
- What if the Pearson correlation is negative or near zero? (The system must still report this as a valid "null result" rather than failing).
- How does the system behave if the dataset size is too small (< 50 molecules) to support 5-fold cross-validation? (Must raise a specific error or switch to leave-one-out validation).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest experimental diffusion data from a CSV source containing SMILES strings, solvent types, and measured diffusion values, validating the SMILES syntax before processing. (See US-1)
- **FR-002**: The system MUST convert molecular structures into graph representations using RDKit, ensuring nodes represent atoms and edges represent bonds, and compute scalar solvent descriptors (viscosity, dielectric constant). (See US-1)
- **FR-003**: The system MUST implement a Message Passing Neural Network (MPNN) that operates exclusively on CPU hardware, avoiding any CUDA/GPU dependencies, and must log "Device: CPU" and verify `torch.cuda.is_available() is False` at startup. (See US-2)
- **FR-004**: The system MUST train the MPNN using 5-fold cross-validation with a fixed random seed of 42 and stratification by solvent type to minimize Mean Squared Error (MSE) between predicted and experimental diffusion coefficients. (See US-2)
- **FR-005**: The system MUST perform a paired t-test on the per-sample absolute errors comparing the RMSE of the GNN against a linear regression baseline (which MUST also include solvent descriptors) to determine statistical significance. (See US-2)
- **FR-006**: The system MUST execute a sensitivity analysis sweeping key hyperparameters (e.g., number of message passing steps) over a defined range (e.g., {1, 2, 3}) AND perform an ablation study removing solvent descriptors to report the variation in correlation coefficients. (See US-3)
- **FR-007**: The system MUST detect and handle dataset variables that are missing or undefined by excluding the record from the dataset and logging the event with the tag `[MISSING_DATA_EXCLUDED]`. (See US-1)

### Key Entities

- **MoleculeGraph**: Represents a molecule as a graph structure with atom nodes and bond edges, derived from SMILES.
- **SolventDescriptor**: A set of scalar physical properties (viscosity, dielectric constant) associated with the solvent environment.
- **DiffusionTarget**: The experimental diffusion coefficient value (target variable) to be predicted.
- **ModelCheckpoint**: The serialized state of the trained MPNN and baseline models.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Pearson correlation coefficient (r) between predicted and experimental diffusion coefficients is measured against the hypothesis of r > 0.7 (positive result) or r < 0.3 (null result), controlling for the confounding effect of solvent descriptors via ablation. (See US-2)
- **SC-002**: The RMSE of the GNN model is measured against the RMSE of the linear regression baseline (including solvent descriptors) to determine if the GNN provides a statistically significant improvement via paired t-test on per-sample errors. (See US-2)
- **SC-003**: The total runtime of the training and evaluation pipeline is measured against the time limit of the free-tier CI runner to ensure feasibility. (See US-2)
- **SC-004**: The stability of the correlation coefficient is measured against the results of the sensitivity analysis (including the ablation study removing solvent descriptors) across the defined hyperparameter sweep range. (See US-3)
- **SC-005**: The memory usage during graph featurization and training is measured against the RAM constraint of the runner environment. (See US-2)

## Assumptions

- The public dataset (e.g., from NIST or Zenodo) contains valid SMILES strings and corresponding experimental diffusion coefficients for at least 1,000 unique molecule-solvent pairs.
- The "static molecular topology" (graph structure) and "solvent descriptors" (viscosity, dielectric constant) are sufficient features to encode the diffusion coefficient without explicit dynamic simulation, as hypothesized in the research question. However, the GNN's unique contribution is validated by comparing performance with and without these descriptors.
- The dataset variables (SMILES, solvent type, diffusion value) are complete; any missing values will be handled by exclusion rather than imputation to avoid introducing bias.
- The relationship between static structure and diffusion is primarily associational; the project does not claim causal inference without randomization.
- The CPU-only implementation of PyTorch Geometric is sufficient to train a single-layer MPNN on a dataset of ≤ 5,000 molecules within the 6-hour time limit; if necessary, standard quantization techniques may be used to meet memory constraints.
- The linear regression baseline using molecular fingerprints (e.g., Morgan fingerprints) AND solvent descriptors is an appropriate and standard comparator for this domain.
- The sensitivity analysis range (message passing steps 1-3) and the ablation study (removing solvent descriptors) are sufficient to detect instability in the model's performance and isolate the graph structure contribution.