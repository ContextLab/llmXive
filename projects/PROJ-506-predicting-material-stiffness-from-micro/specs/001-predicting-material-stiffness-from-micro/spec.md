# Project Specification: Predicting Material Stiffness from Microstructure Images Using CNNs

## 1. Introduction
This project aims to develop a Convolutional Neural Network (CNN) to predict the effective elastic stiffness of composite materials based on 2D microstructure images. The ground truth stiffness values are computed using FFT-based numerical homogenization, as permitted by the amended Constitution (Principle VI).

## 2. Functional Requirements

### FR-001: Microstructure Generation
The system shall generate synthetic 2D microstructure images with controlled inclusion densities and topologies.
- **Input**: Target inclusion density, topology type (e.g., random, aligned, periodic), image resolution.
- **Output**: 128x128 pixels PNG images stored in `data/raw/`.
- **Constraint**: Images must be strictly 128x128 pixels to ensure consistent model input dimensions.
- **Decoupling**: The generation process must decouple density from topology to allow independent analysis of their effects.

### FR-002: Ground Truth Calculation
The system shall compute the effective elastic stiffness tensor for each generated microstructure using FFT-based numerical homogenization.
- **Method**: FFT-based homogenization (CPU-optimized).
- **Output**: Stiffness tensor (Voigt notation) stored in metadata.

### FR-003: CNN Architecture
The system shall implement a shallow CNN architecture suitable for CPU training.
- **Layers**: Convolutional layers with ReLU activation, global average pooling, fully connected output.
- **Input**: 128x128 grayscale images.
- **Output**: Predicted stiffness scalar or tensor components.

### FR-004: Training Loop
The system shall implement a training loop with Adam optimizer and configurable epochs.
- **Optimizer**: Adam.
- **Batch Size**: 32.
- **Convergence**: Training shall continue until convergence or a maximum epoch limit is reached.

### FR-005: Cross-Validation
The system shall support k-fold cross-validation to ensure robust model evaluation.
- **Stratification**: Folds must be stratified by inclusion density and topology type.

### FR-006: Evaluation Metrics
The system shall compute Mean Absolute Error (MAE), Mean Squared Error (MSE), and R-squared (R2) for model evaluation.

### FR-007: Statistical Analysis
The system shall perform One-way ANOVA and Tukey HSD tests to analyze prediction errors across different inclusion density bins.
- **Method**: One-way ANOVA followed by Tukey HSD for post-hoc analysis.
- **Purpose**: To determine if prediction errors differ significantly between density groups.

### FR-008: Out-of-Distribution Detection
The system shall flag predictions made on microstructures with inclusion densities outside the training distribution.

## 3. User Stories

### US-1: Synthetic Data Generation and Ground Truth Calculation
**As a** researcher,
**I want** to generate synthetic microstructure images with known ground truth stiffness values,
**So that** I can train and validate a CNN model.

**Acceptance Scenario 1: Generate Microstructures**
Given I have specified the target inclusion density and topology type,
When I run the generation script,
Then the system shall produce 128x128 pixels PNG images in `data/raw/`.
And the system shall compute the corresponding stiffness tensor using FFT-based homogenization.
And the metadata shall include density, topology, and topological metrics (shape_factor, connectivity).

**Acceptance Scenario 2: Validate Physical Plausibility**
Given a set of generated microstructures,
When I run the validation script,
Then the system shall verify that stiffness tensors fall within Voigt-Reuss-Hill bounds.
And invalid entries shall be logged to `data/processed/validation_log.csv` with specific reasons.

### US-2: CPU-Optimized CNN Training and Validation
**As a** data scientist,
**I want** to train a CNN on the generated dataset using CPU resources,
**So that** I can develop a predictive model within the 6-hour time constraint.

**Acceptance Scenario 1: Train Model**
Given a generated dataset,
When I run the training script,
Then the model shall be trained using the defined CNN architecture.
And the training shall complete within 6 hours on a 2-core CPU.
And the model weights shall be saved to `code/models/`.

**Acceptance Scenario 2: Evaluate Model**
Given a trained model and a held-out test set,
When I run the evaluation script,
Then the system shall compute MAE, MSE, and R2 metrics.
And the results shall be reported in `data/processed/analysis_report.md`.

### US-3: Generalization and Statistical Analysis
**As a** researcher,
**I want** to evaluate the model's generalization performance across different inclusion densities,
**So that** I can understand the model's limitations and reliability.

**Acceptance Scenario 1: Analyze Error vs. Density**
Given model predictions on a test set with varying densities,
When I run the statistical analysis script,
Then the system shall bin data by inclusion density.
And compute errors for each bin.
And perform One-way ANOVA and Tukey HSD tests to compare errors across bins.
And report the degradation rate for out-of-distribution densities.

**Acceptance Scenario 2: Report Findings**
Given the statistical analysis results,
When I view the analysis report,
Then the report shall include error vs. density plots.
And tables showing ANOVA p-values and Tukey HSD results.
And the quantitative degradation rate metric.

## 4. Non-Functional Requirements

### NFR-001: Performance
- Training must complete within 6 hours on standard CPU hardware.
- FFT solver must be optimized for CPU execution.

### NFR-002: Reproducibility
- All experiments must be reproducible with fixed random seeds.
- Data generation and model training scripts must log all parameters.

### NFR-003: Data Integrity
- Generated datasets must conform to the defined schema (`specs/001-predict-stiffness-cnn/contracts/dataset.schema.yaml`).
- Ground truth values must be physically plausible (within VRH bounds).

## 5. Data Model

### Dataset Schema
- `image_path`: string (path to PNG image)
- `stiffness_tensor`: float[] (Voigt notation stiffness components)
- `inclusion_density`: float (0.0 to 1.0)
- `topology_type`: string (e.g., "random", "aligned")
- `shape_factor`: float (topological metric)
- `connectivity`: float (topological metric)
- `seed`: integer (random seed used for generation)

### Model Output Schema
- `model_version`: string
- `prediction`: float[] (predicted stiffness)
- `error`: float (absolute error)
- `density_bin`: string (bin label for analysis)

## 6. Appendix

### A. FFT-Based Homogenization
The ground truth stiffness is computed using FFT-based numerical homogenization, a method that solves the Lippmann-Schwinger equation iteratively. This approach is efficient for periodic microstructures and is explicitly permitted by the project Constitution (Principle VI).

### B. Statistical Methods
- **One-way ANOVA**: Used to test if there are statistically significant differences between the means of three or more independent groups (density bins).
- **Tukey HSD**: A post-hoc test used to determine which specific groups differ from each other after a significant ANOVA result.