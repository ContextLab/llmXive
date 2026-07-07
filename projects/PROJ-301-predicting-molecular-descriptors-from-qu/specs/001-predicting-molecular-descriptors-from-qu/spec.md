# Feature Specification: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

**Feature Branch**: `001-predict-molecular-descriptors`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Feature Extraction (Priority: P1)

The system must successfully download the QM dataset, parse the geometry files, and generate both low-dimensional Morgan fingerprints and graph feature sets for a representative subset of molecules within the allocated runtime and memory constraints.

**Why this priority**: Without valid, aligned feature sets (2D and 3D) and corresponding DFT reference labels, no model training or comparison can occur. This is the foundational data pipeline.

**Independent Test**: Can be fully tested by verifying the existence of the generated feature matrices (`.npy` or `.csv`) and the label vector, checking their dimensions match the [deferred] molecule subset, and confirming the memory footprint during generation does not exceed acceptable limits.

**Acceptance Scenarios**:

1. **Given** the QM9 dataset is available at the Harvard Dataverse URL, **When** the pipeline executes the download and extraction script, **Then** the `.xyz` files for [deferred] molecules are present, and a subset is selected for processing.
2. **Given** the [deferred] molecule subset, **When** the feature extraction script runs, **Then** a 2D feature matrix (shape: [deferred] x 2048) and a 3D feature structure (graph objects with node/edge features) are generated, alongside the DFT reference labels (dipole, HOMO, LUMO).
3. **Given** the extraction process, **When** memory usage is monitored, **Then** the peak memory usage remains ≤ 7 GB, triggering a graceful downsampling if the limit is ≥ 6.5 GB.

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

The system must train separate Random Forest Regressors on the multi-dimensional feature sets using k-fold cross-validation, ensuring the training process completes on a CPU-only environment within a feasible time limit.

**Why this priority**: This step validates the feasibility of the chosen method (Random Forest) on the target hardware and establishes the baseline predictive performance for both representations.

**Independent Test**: Can be fully tested by running the training script on a CPU-only runner, verifying that 5-fold cross-validation completes for both models, and checking that the trained model objects (`.pkl`) are saved.

**Acceptance Scenarios**:

1. **Given** the feature matrices and labels are ready, **When** the training script executes with the specified hyperparameter grid (n_estimators ∈ {low, high}, max_depth ∈ {10, 20, None}), **Then** two Random Forest models (one for 2D, one for 3D) are trained and saved as `.pkl` files.
2. **Given** the CPU-only environment, **When** the 5-fold cross-validation loop runs, **Then** the total runtime for both models is ≤ 6 hours.
3. **Given** the training process, **When** the cross-validation metrics are calculated, **Then** the Mean Absolute Error (MAE) and RMSE for each fold are recorded for both models.

---

### User Story 3 - Comparative Analysis and Failure Boundary Identification (Priority: P3)

The system must compute the relative error increase between the D and D models for each target descriptor (dipole moment, HOMO, LUMO) and generate parity plots to identify where 2D representations fail.

**Why this priority**: This delivers the specific research outcome: quantifying the "failure boundary" and determining which properties are amenable to 2D approximation.

**Independent Test**: Can be fully tested by generating the error comparison table and parity plots, verifying that the relative error increase is calculated correctly, and confirming the plots visually distinguish between the two representations.

**Acceptance Scenarios**:

1. **Given** the cross-validation results for both models, **When** the comparison script runs, **Then** a table is generated showing the MAE and relative error increase (2D vs 3D) for dipole, HOMO, and LUMO.
2. **Given** the predictions and DFT labels, **When** the plotting script executes, **Then** parity plots (Predicted vs. DFT) are saved for both 2D and 3D models, clearly labeled.
3. **Given** the error analysis, **When** the results are reviewed, **Then** a conclusion is drawn regarding which descriptors (e.g., directional vs. global) show a significant performance gap (defined as relative error increase ≥ 10% or p-value < 0.05 via paired t-test), validating the "failure boundary" hypothesis.

### Edge Cases

- What happens if the QM9 dataset download fails or the file is corrupted? (System retries a limited number of times., then fails with a clear error log).
- How does the system handle molecules with missing DFT labels in the subset? (Rows with missing labels are silently dropped before feature extraction to ensure alignment).
- What if the 3D graph construction fails for a specific molecule due to parsing errors? (The molecule is excluded from the 3D model training set, but the 2D model may still proceed if the SMILES is valid).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the QM9 dataset from the Harvard Dataverse URL (doi:10.7910/DVN/28075) and extract `.xyz` files containing 3D coordinates and DFT properties. (See US-1)
- **FR-002**: System MUST generate 2D Morgan fingerprints (radius=2, nBits=2048) and 3D graph features (atomic number, hybridization, distance bins, bond angles, dihedral angles) for a subset of [deferred] molecules. (See US-1)
- **FR-003**: System MUST train two separate Random Forest Regressors (scikit-learn) on the D and multi-dimensional feature sets using identical hyperparameter grids (n_estimators spanning a range of values, max_depth ∈ {10, 20, None}) and 5-fold cross-validation. (See US-2)
- **FR-004**: System MUST calculate Mean Absolute Error (MAE) and Root Mean Square Error (RMSE) for each model against the DFT reference values (dipole moment, HOMO, LUMO). (See US-3)
- **FR-005**: System MUST compute the relative error increase (2D vs 3D) for each descriptor and generate parity plots (Predicted vs. DFT) to visualize performance differences, explicitly noting that the 3D model uses DFT-optimized geometries as input. (See US-3)
- **FR-006**: System MUST monitor memory usage during execution and enforce a hard limit of sufficient RAM, downsampling the dataset if the limit is ≥ 6.5 GB. (See US-1)
- **FR-007**: System MUST calculate and report the theoretical lower bound (identity mapping error) for the 3D model to quantify the complexity of the geometry-to-property mapping and contextualize the 3D model's performance. (See US-3)

### Key Entities

- **Molecule**: Represents a chemical structure with attributes: SMILES string, 3D coordinates (XYZ), and DFT reference properties (dipole, HOMO, LUMO).
- **FeatureSet**: Represents the input data for a model, containing either 2D fingerprints or 3D graph features, aligned by molecule ID.
- **ModelResult**: Stores the trained model object, cross-validation metrics (MAE, RMSE per fold), and prediction outputs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The prediction error (MAE/RMSE) for the dimensional model is measured against the DFT reference values for dipole, HOMO, and LUMO to quantify the information loss. (See US-3)
- **SC-002**: The relative error increase (2D vs 3D) is measured for each descriptor to identify the "failure boundary" where 2D representations become insufficient. (See US-3)
- **SC-003**: The total runtime of the training and validation pipeline is measured against the predetermined time limit to ensure CPU-only feasibility. (See US-2)
- **SC-004**: The peak memory usage during feature extraction and training is measured against the free-tier CI runner limits to ensure compatibility. (See US-1)
- **SC-005**: The consistency of the 5-fold cross-validation results is measured (standard deviation of MAE across folds) and must be ≤ 5% of the mean MAE to ensure model stability. (See US-2)

## Assumptions

- **Assumption about dataset variables**: The QM9 dataset contains all necessary DFT reference labels (dipole moment `mu`, HOMO, LUMO) for the selected [deferred] molecule subset. If any labels are missing, the subset size will be reduced to ensure complete data.
- **Assumption about computational resources**: The Random Forest algorithm with [deferred] samples and 2048 features is computationally tractable on a standard GitHub Actions free-tier runner (2 CPU, 7 GB RAM) within 6 hours.
- **Assumption about software dependencies**: The `RDKit` and `scikit-learn` libraries are available in the CI environment and can process the `.xyz` files and generate the required features without GPU acceleration.
- **Assumption about representational fidelity**: 2D Morgan fingerprints capture global topological information but lack explicit geometric information, while 3D graph features explicitly encode interatomic distances, bond angles, and dihedral angles, making them theoretically superior for directional properties like dipole moments, provided the 3D model's performance is contextualized against the theoretical lower bound.
- **Assumption about data quality**: The `.xyz` files in the QM9 dataset are correctly formatted and contain valid 3D coordinates for all molecules in the subset.