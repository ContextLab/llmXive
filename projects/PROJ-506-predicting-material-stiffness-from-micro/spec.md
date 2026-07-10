# Specification: Predicting Material Stiffness from Microstructure Images

## Functional Requirements

### FR-001: Microstructure Generation
The system shall generate synthetic 2D microstructure images of size **128x128 pixels** with varying void/inclusion densities.

### FR-002: Ground Truth Calculation
The system shall compute effective elastic stiffness tensors using FFT-based numerical homogenization.

### FR-003: CNN Architecture
The system shall implement a shallow Convolutional Neural Network for stiffness prediction.

### FR-004: Training Pipeline
The system shall support training with Adam optimizer, batch size 32, and limited epochs for CPU efficiency.

### FR-005: Cross-Validation
The system shall implement stratified k-fold cross-validation based on inclusion density and topological features.

### FR-006: Evaluation Metrics
The system shall compute MAE, MSE, and R2 metrics for model evaluation.

### FR-007: Statistical Analysis
The system shall compare model prediction errors across different inclusion density bins using **One-way ANOVA** followed by **Tukey HSD** post-hoc analysis to determine statistical significance and pairwise differences.

### FR-008: Error Thresholding
The system shall flag instances where prediction error exceeds a defined percentage of the Mean Absolute Error (MAE).

## User Stories

### US-1: Synthetic Data Generation
**Goal**: Generate synthetic microstructures and compute ground truth stiffness.
**Acceptance Scenario 1**: The system generates ≥ 2,000 images (128x128 pixels) and a metadata file with stiffness tensors within Voigt-Reuss-Hill bounds.

### US-2: Model Training
**Goal**: Train a CNN on the generated dataset.
**Acceptance Scenario 1**: Training completes within 6 hours on CPU, saves model weights, and reports MSE/R2.

### US-3: Generalization & Statistical Analysis
**Goal**: Evaluate model generalization and perform statistical tests.
**Acceptance Scenario 1**: Report shows error degradation for out-of-distribution densities.
**Acceptance Scenario 2**: The evaluation report displays F-statistics and p-values from **One-way ANOVA** comparing error distributions across all density bins, along with a **Tukey HSD** matrix highlighting significant pairwise differences.

## Success Criteria

### SC-001: Accuracy
The Mean Absolute Error (MAE) of the model's predictions against the FFT-based numerical ground truth on a held-out test set must be within the defined threshold.

### SC-002: Generalization
The degradation rate (slope of MAE vs. density) for out-of-distribution densities must be within acceptable limits.

### SC-004: Statistical Significance
The model is considered successful if **One-way ANOVA** indicates no statistically significant difference (p > 0.05) in prediction errors across density bins, and **Tukey HSD** post-hoc tests confirm no significant pairwise degradation for out-of-distribution densities.

### SC-005: Stability
The variance/standard deviation of R-squared values across the 5 folds must be within acceptable limits.

## Constraints
- **Hardware**: CPU-only execution (no CUDA).
- **Runtime**: Total pipeline ≤ 6 hours on simulated free-tier constraints.
- **Resolution**: 128x128 pixels (amended from 256x256).
- **Statistics**: **One-way ANOVA** and **Tukey HSD** (amended from paired t-tests).