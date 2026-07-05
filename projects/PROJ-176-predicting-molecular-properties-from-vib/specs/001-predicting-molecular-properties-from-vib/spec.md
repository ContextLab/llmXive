# Feature Specification: Predicting Molecular Properties from Vibrational Spectra with Deep Learning

**Feature Branch**: `001-predict-molecular-properties`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Properties from Vibrational Spectra with Deep Learning"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1)

The researcher downloads the QM9 dataset and a corresponding pre-computed IR-spectra dataset, verifies the one-to-one molecular correspondence via InChIKey, and transforms the raw spectral data into a normalized, fixed-length tensor format suitable for model input.

**Why this priority**: Without a clean, aligned dataset, no model can be trained or evaluated. This is the foundational step that enables all subsequent analysis and ensures the data fits within the GitHub Actions memory constraints.

**Independent Test**: The pipeline can be tested by running the data download and preprocessing script alone, verifying that the output is a single `.npz` file containing aligned spectra and property vectors, and that the file size is < 10 GB.

**Acceptance Scenarios**:

1. **Given** the QM9 and QM9-IR datasets are available at the specified URLs, **When** the ingestion script executes, **Then** the system MUST successfully download both files and verify a 1:1 match of ≥ 129,000 molecules via InChIKey.
2. **Given** raw spectral data with varying wavenumber ranges, **When** the preprocessing step runs, **Then** every spectrum MUST be interpolated to a fixed grid of points (in the mid-infrared region, with uniform spacing), apply Gaussian smoothing (σ = 2 cm⁻¹), and normalize to unit area.
3. **Given** a mismatched molecule ID between the two datasets, **When** the validation check runs, **Then** the system MUST discard the mismatched entry and log the count of discarded samples.

---

### User Story 2 - 1-D CNN Model Training and Validation (Priority: P2)

The researcher trains a 1-D convolutional neural network to map the pre-processed vibrational spectra to three target MolecularProperties (dipole moment, polarizability, HOMO-LUMO gap) using a CPU-only environment, with early stopping to prevent overfitting.

**Why this priority**: This is the core research engine. It tests the hypothesis that spectra encode electronic information. It must be robust enough to run within the 6-hour CI limit and produce a model that can be evaluated.

**Independent Test**: The training script can be tested by running it on a subset ([deferred] train, [deferred] validation, [deferred] test) of the data to verify that the loss decreases, the checkpoint is saved, and the process completes within a reasonable time on a CPU-only runner.

**Acceptance Scenarios**:

1. **Given** the pre-processed dataset split into a majority of the data for training, with the remainder divided for validation and testing., **When** the training loop executes, **Then** the model MUST train for a target of 5 epochs (maximum 50 epochs) with early stopping triggered if validation loss does not improve for a predefined number of consecutive epochs.
2. **Given** the CPU-only constraint (no GPU/CUDA), **When** the model trains, **Then** the system MUST use standard floating point precision and avoid any low-bit quantization or CUDA-specific operations.
3. **Given** the three target MolecularProperties, **When** training completes, **Then** the system MUST save the best model checkpoint (based on validation loss) and a TensorBoard log file for loss curve visualization.

---

### User Story 3 - Statistical Evaluation and Significance Testing (Priority: P3)

The researcher evaluates the trained model on the held-out test set by computing Mean Absolute Error (MAE) and R² for each property, and performs paired-sample t-tests to determine if the model exhibits systematic bias (mean error ≠ 0) relative to the reference DFT values.

**Why this priority**: This step translates model performance into scientific conclusions. It validates the hypothesis and provides the quantitative evidence required for the research question.

**Independent Test**: The evaluation script can be tested by running it on a saved model checkpoint and a test set, verifying that it outputs a JSON report with MAE, R², and p-values for the t-tests.

**Acceptance Scenarios**:

1. **Given** the best model checkpoint and the held-out test set, **When** the evaluation runs, **Then** the system MUST compute and report MAE and R² for dipole moment, polarizability, and HOMO-LUMO gap.
2. **Given** the model predictions and the ground truth DFT values, **When** the statistical analysis runs, **Then** the system MUST perform a paired-sample t-test for each property and report the p-value.
3. **Given** a null hypothesis that the mean error is zero (no systematic bias), **When** the t-test is conducted, **Then** the system MUST report the p-value and the mean error for each property.

---

### User Story 4 - Independent Validation (Priority: P4)

The researcher validates the model's generalizability by evaluating it on an independent dataset containing experimental vibrational spectra and corresponding experimental property measurements (or DFT values computed with a different functional), ensuring the model does not merely memorize the training distribution's artifacts.

**Why this priority**: This step addresses the scientific soundness concern regarding circular validation. It ensures the model predicts properties based on spectral features rather than just reproducing the training DFT method's artifacts.

**Independent Test**: The validation script can be tested by running it on an external dataset file, verifying that it outputs a separate JSON report with MAE and R² distinct from the training/test set results.

**Acceptance Scenarios**:

1. **Given** an independent validation dataset (experimental or different DFT method), **When** the validation script executes, **Then** the system MUST compute and report MAE and R² for the three target properties without retraining the model.
2. **Given** the independent validation results, **When** the analysis completes, **Then** the system MUST flag if the MAE on the independent set exceeds the MAE on the test set by a significant margin.

---

### Edge Cases

- What happens if the downloaded QM9-IR dataset is corrupted or incomplete? The system MUST fail fast with a clear error message and exit code, rather than proceeding with partial data.
- How does the system handle molecules with missing property values in the QM9 dataset? The preprocessing step MUST filter out any molecule missing any of the three target MolecularProperties before training.
- What if the training loss diverges or becomes NaN? The training loop MUST detect NaN loss, stop immediately, and log a "Training Failed" status to prevent saving a broken checkpoint.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the QM9 dataset and a pre-computed IR-spectra dataset, verify one-to-one molecular correspondence via InChIKey, and discard any mismatches (See US-1).
- **FR-002**: System MUST interpolate all IR spectra to a fixed wavenumber grid (covering the mid-infrared region with fine resolution), apply Gaussian smoothing (σ = 2 cm⁻¹), and normalize them to unit area (See US-1).
- **FR-003**: System MUST implement a CNN architecture with three convolutional blocks (kernel sizes, 7, 9) and three separate regression heads for dipole, polarizability, and HOMO-LUMO gap (See US-2).
- **FR-004**: System MUST train the model using the Adam optimizer (lr=1e-3) with early stopping (patience=10) on a CPU-only runner, ensuring no GPU/CUDA operations are invoked (See US-2).
- **FR-005**: System MUST compute MAE and R² for each target property on the held-out test set and perform paired-sample t-tests to assess systematic bias (mean error ≠ 0) relative to the reference DFT values (See US-3).
- **FR-006**: System MUST enforce a maximum runtime for the entire pipeline (download, preprocess, train, evaluate) by terminating if runtime exceeds a configurable threshold. (See US-2).
- **FR-007**: System MUST evaluate the trained model on an independent validation dataset (experimental or distinct DFT method) to verify generalizability and avoid circular validation (See US-4).

### Key Entities

- **Spectrum**: A 1-D array representing the intensity of IR absorption across a fixed wavenumber grid (3601 points).
- **MolecularProperties**: A structured record containing three numeric values: dipole moment (Debye), isotropic polarizability (Å³), and HOMO-LUMO gap (eV).
- **ModelCheckpoint**: A serialized state of the trained CNN, including weights and optimizer state, saved for inference and evaluation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the model predictions is measured against the DFT-computed reference values for dipole moment, polarizability, and HOMO-LUMO gap (See FR-005).
- **SC-002**: The coefficient of determination (R²) is measured against the variance of the DFT-computed reference values to assess the proportion of variance explained by the spectral model (See FR-005).
- **SC-003**: The statistical significance of systematic bias is measured against the null hypothesis (mean error = 0) via paired-sample t-tests, with a target p-value < 0.01 for bias detection (See FR-005).
- **SC-004**: The total end-to-end runtime of the pipeline is measured against the 6-hour limit of the GitHub Actions free-tier runner to ensure feasibility (See FR-006).
- **SC-005**: The generalizability of the model is measured by comparing the MAE on the independent validation dataset against the MAE on the held-out test set, with a tolerance of ≤ 20% increase (See FR-007).

## Assumptions

- **Dataset Availability**: The QM9 dataset and a corresponding pre-computed IR-spectra dataset (e.g., "QM9-IR") are available at the specified URLs and remain stable throughout the project lifecycle.
- **Compute Constraints**: The entire analysis (including training a -D CNN on a large-scale dataset) can be completed within 6 hours on a GitHub Actions free-tier runner (A multi-core CPU configuration with a moderate amount of RAM.) without GPU acceleration.
- **Data Quality**: The pre-computed IR spectra in the external dataset are derived using a consistent DFT method and basis set, ensuring that the relationship between spectra and properties is not confounded by methodological inconsistencies.
- **No GPU Dependency**: The chosen 1-D CNN architecture and PyTorch version (≤ 2.0) are compatible with CPU-only execution and do not require CUDA-specific libraries or quantization techniques.
- **DFT Method Dependency**: The model predicts DFT-computed reference values rather than absolute physical ground truth; the relationship is statistical and dependent on the specific DFT functional used in the training data.
- **Threshold Justification**: The significance threshold for the t-test (p < 0.01) is adopted from standard scientific practice for hypothesis testing in computational chemistry, and no additional sensitivity analysis is required for this specific statistical test.