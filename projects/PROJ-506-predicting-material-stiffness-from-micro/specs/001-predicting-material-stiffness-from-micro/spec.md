# Feature Specification: Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks

**Feature Branch**: `001-predict-stiffness-cnn`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks"

## User Scenarios & Testing

### User Story 1 - Synthetic Data Generation and Ground Truth Calculation (Priority: P1)

As a materials scientist, I need a pipeline to generate a synthetic dataset of 2D grayscale microstructure images with varying void/inclusion densities and compute their effective elastic stiffness tensors using FFT-based numerical homogenization, so that I have a labeled dataset for training a surrogate model where the ground truth depends on the spatial arrangement of inclusions, not just volume fraction.

**Why this priority**: This is the foundational step; without a valid dataset with known ground truth that captures spatial correlations, no model training or validation can occur. It directly addresses the "Data Generation" and "Ground Truth" steps of the methodology.

**Independent Test**: This can be fully tested by running the data generation script and verifying that the output directory contains ≥ 2,000 image files and a corresponding metadata file (e.g., CSV or JSON) listing the calculated stiffness tensors for each image, ensuring all values are within physically plausible bounds and vary based on spatial topology.

**Acceptance Scenarios**:

1. **Given** a request to generate ≥ 2,000 microstructures, **When** the data generation script executes, **Then** the system produces ≥ 2,000 distinct 256x256 pixel grayscale images and a dataset file containing the corresponding stiffness tensors.
2. **Given** the generated dataset, **When** the system validates the physical plausibility of the stiffness tensors, **Then** all calculated values fall within the Voigt-Reuss-Hill bounds appropriate for the base material properties, and the variance in stiffness correlates with spatial topology, not just density.

---

### User Story 2 - CPU-Optimized CNN Training and Validation (Priority: P2)

As a researcher, I need to train a shallow Convolutional Neural Network on the generated dataset using PyTorch in CPU-only mode, so that I can develop a surrogate model that approximates stiffness tensors within an acceptable error margin while adhering to the 6-hour GitHub Actions runner limit.

**Why this priority**: This implements the core research hypothesis (CNN as a surrogate) and the primary methodology. It is the second most critical step after data generation.

**Independent Test**: This can be fully tested by executing the training script on a CPU-only environment and verifying that the training job completes within 6 hours, produces a saved model artifact, and reports a final Mean Squared Error (MSE) and R-squared value on the validation set.

**Acceptance Scenarios**:

1. **Given** the generated dataset and the training configuration, **When** the training script runs on a 2-core CPU environment, **Then** the training process completes within 6 hours without GPU/CUDA errors and saves the model weights.
2. **Given** a trained model, **When** evaluated on a held-out test set, **Then** the model achieves a Mean Absolute Error (MAE) of ≤ 5% relative to the analytical ground truth for stiffness tensors.

---

### User Story 3 - Generalization and Statistical Analysis (Priority: P3)

As a materials scientist, I need to evaluate the model's generalization across different inclusion densities and perform statistical tests (paired t-tests) on prediction errors, so that I can understand the limits of the surrogate model and validate its stability across different microstructural regimes.

**Why this priority**: This addresses the "Expected Results" and "Statistical Test" parts of the methodology, providing the scientific insight required to answer the research question. It is lower priority than building the model but essential for the research outcome.

**Independent Test**: This can be fully tested by running the evaluation script which bins test data by density, computes prediction errors for each bin, and outputs a report containing the statistical significance of differences between bins and a visualization of performance degradation.

**Acceptance Scenarios**:

1. **Given** a trained model and a test set with varying inclusion densities, **When** the evaluation script runs, **Then** it outputs a report showing that prediction error increases for densities outside the training distribution.
2. **Given** prediction errors across different density bins, **When** a paired t-test is performed, **Then** the system outputs the p-values indicating whether the differences in error rates between bins are statistically significant.

---

### Edge Cases

- What happens when the generated microstructure has an extreme void density (e.g., >90% voids) that approaches the theoretical limit of the numerical homogenization solver?
- How does the system handle a scenario where the FFT-based homogenization solver fails to converge due to numerical instability in edge-case geometries?
- How does the system behave if the runtime limit is approached during the 50th epoch of training?

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate ≥ 2,000 synthetic 2D grayscale microstructure images (256x256 pixels) with randomized void/inclusion densities using `scikit-image`. The dataset size is set to ≥ 2,000 to satisfy power analysis requirements for a 95% confidence interval on the MAE, subject to the 6-hour runtime constraint. (See US-1)
- **FR-002**: System MUST calculate effective elastic stiffness tensors for each generated image using FFT-based numerical homogenization (e.g., `pyfftw` or `scipy.fft`) to ensure the ground truth labels depend on the spatial arrangement (topology) of inclusions, not just volume fraction. (See US-1)
- **FR-003**: System MUST implement a shallow CNN architecture with a limited number of convolutional layers, ReLU activation, and global average pooling, ensuring compatibility with CPU-only inference. (See US-2)
- **FR-004**: System MUST train the CNN using PyTorch in CPU mode with the Adam optimizer, a batch size of 32, and a maximum of 50 epochs, ensuring the total runtime does not exceed 6 hours on a standard GitHub Actions free-tier runner. (See US-2)
- **FR-005**: System MUST perform k-fold cross-validation to assess model stability and prevent overfitting to specific microstructural patterns. (See US-2)
- **FR-006**: System MUST compute and report Mean Squared Error (MSE), R-squared, and Mean Absolute Error (MAE) metrics against the numerical ground truth on a held-out test set. (See US-2)
- **FR-007**: System MUST bin test data by inclusion density and perform paired t-tests to compare prediction errors across these bins. (See US-3)
- **FR-008**: System MUST flag and report instances where prediction errors exceed a predefined MAE threshold, specifically highlighting cases where test densities fall outside the training distribution. (See US-3)

### Key Entities

- **MicrostructureImage**: A 2D grayscale array (256x256) representing the spatial arrangement of inclusions and voids.
- **StiffnessTensor**: A 2D matrix (representing the effective elastic properties) calculated numerically from the microstructure via FFT-based homogenization.
- **PredictionResult**: The output of the CNN, containing the predicted stiffness tensor and the calculated error metrics relative to the ground truth.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase. Design targets (e.g., error thresholds, runtime limits) are explicit constants; empirical measurements (e.g., actual dataset size achieved, actual runtime) are recorded at run time.

- **SC-001**: The Mean Absolute Error (MAE) of the predicted stiffness tensors is measured against the FFT-based numerical homogenization ground truth, with a target threshold of ≤ 5% on held-out data. (See US-2)
- **SC-002**: The model's generalization capability is measured against the distribution of inclusion densities in the test set, specifically quantifying the degradation rate of accuracy for out-of-distribution densities. (See US-3)
- **SC-003**: The computational efficiency is measured against the GitHub Actions free-tier runner constraints (CPU cores, ~7 GB RAM, ≤6 hours), verifying that the full training and evaluation pipeline completes within these limits. (See US-2)
- **SC-004**: The statistical significance of prediction error differences across density bins is measured against the null hypothesis using paired t-tests, with a p-value threshold of < 0.05 considered significant. (See US-3)
- **SC-005**: The stability of the model is measured against the variance in performance metrics across the folds of cross-validation, ensuring no single fold deviates significantly from the mean R-squared value. (See US-2)

## Assumptions

- The synthetic microstructures generated by `scikit-image` are sufficient to represent the physical variability of real polymer microstructures for the purpose of training a surrogate model.
- The FFT-based numerical homogenization method provides a sufficiently accurate and computationally efficient ground truth for training, capturing topology-dependent stiffness that analytical Voigt-Reuss-Hill bounds cannot. Voigt-Reuss-Hill is explicitly excluded as a ground truth method because it yields values independent of spatial arrangement.
- The relationship between the spatial arrangement of inclusions/voids and the effective elastic stiffness is learnable by a shallow CNN with a limited number of layers; deeper architectures are assumed unnecessary for this specific correlation and would violate the CPU runtime constraints.
- The GitHub Actions free-tier runner environment (limited CPU, ~7 GB RAM) is stable and sufficient for training a small CNN on a dataset of ≥ 2,000 samples without requiring memory paging or disk swapping that would exceed the time limit.
- The [deferred] MAE target is a defensible community-standard baseline for surrogate models in this domain; if the model fails to meet this, the result will be interpreted as a limitation of the 2D image representation rather than a failure of the methodology.
- The "inclusion density" variable is the primary driver of stiffness variation, and other microstructural features (e.g., aspect ratio, orientation distribution) are either implicitly captured by the 2D spatial arrangement or are secondary to the primary research question.
- **Justification for Outlier Flagging (FR-008)**: Flagging individual instances with errors > 5% is essential for the generalization analysis (US-3) to identify specific failure modes and microstructural regimes where the surrogate model breaks down, rather than relying solely on aggregate statistics.
- **Justification for FFT-based Homogenization**: The switch from analytical Voigt-Reuss-Hill to FFT-based homogenization is required to ensure the research question (spatial correlation) is answerable; analytical bounds decouple stiffness from topology, rendering the CNN task trivial and scientifically invalid.