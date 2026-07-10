# Project Specification: Predicting Material Stiffness from Microstructure Images Using CNNs

## 1. Introduction
This project aims to develop a Convolutional Neural Network (CNN) to predict the effective elastic stiffness of materials based on 2D microstructure images.

## 2. Functional Requirements

### FR-001: Microstructure Generation
The system shall generate synthetic 2D microstructure images with varying inclusion densities and topologies.
- **Resolution**: 128x128 pixels (Amended from 256x256 in T004).
- **Decoupling**: Density and topology must be independently controllable.

### FR-002: Ground Truth Calculation
The system shall compute the effective stiffness tensor using FFT-based numerical homogenization (per Constitution Principle VI).

### FR-003: CNN Architecture
The system shall implement a shallow CNN architecture optimized for CPU inference.

### FR-004: Training Pipeline
The system shall support training with k-fold cross-validation.

### FR-005: Data Validation
The system shall validate generated data against physical bounds (Voigt-Reuss-Hill).

### FR-006: Evaluation Metrics
The system shall report MAE, MSE, and R2 scores.

### FR-007: Statistical Analysis
The system shall evaluate model generalization across inclusion densities.
- **Methodology**: Perform **One-way ANOVA** to test for significant differences in prediction errors across density bins, followed by **Tukey HSD** post-hoc tests for pairwise comparisons.
- **Note**: This replaces the previously specified "paired t-tests" to align with the multi-group comparison requirements of Plan Task 0.5.

### FR-008: OOD Detection
The system shall flag predictions made on out-of-distribution densities.

## 3. Success Criteria

### SC-001: Prediction Accuracy
The model must achieve a Mean Absolute Error (MAE) of < 5% on the held-out test set relative to the FFT ground truth.

### SC-002: Generalization
The degradation rate of MAE for Out-of-Distribution (OOD) densities must be quantified and reported.

### SC-003: Runtime
Full pipeline (generation + training + evaluation) must complete within 6 hours on a standard 2-core CPU.

### SC-004: Statistical Significance
The One-way ANOVA test on prediction errors across density bins must yield a p-value < 0.05, indicating that density significantly affects model error.
- **Method**: One-way ANOVA followed by Tukey HSD.
- **Note**: This criterion was updated from "paired t-tests" to "One-way ANOVA" to correctly handle multiple density groups as per Plan Task 0.5.

### SC-005: Stability
The standard deviation of R2 scores across 5-fold cross-validation must be < 0.05.

## 4. User Stories

### US-1: Synthetic Data Generation
As a researcher, I want to generate 2,000+ synthetic microstructures with known ground truth stiffness so that I can train a supervised model.
**Acceptance Scenario 1**:
1. Generate 2,000 images at 128x128 resolution.
2. Compute stiffness via FFT.
3. Verify all tensors satisfy Voigt-Reuss-Hill bounds.

### US-2: Model Training
As a data scientist, I want to train a CNN on the generated dataset using CPU resources so that I can obtain a predictive model.
**Acceptance Scenario 2**:
1. Train model using 5-fold stratified cross-validation.
2. Report R2 and MAE.
3. Verify training completes within 6 hours.

### US-3: Generalization & Statistical Validation
As a material scientist, I want to verify that the model's error does not significantly degrade within the training distribution and understand the degradation rate outside it.
**Acceptance Scenario 2**:
1. Bin test data by inclusion density.
2. Perform **One-way ANOVA** on prediction errors across bins.
3. If significant, perform **Tukey HSD** to identify specific bin differences.
4. Report the degradation rate (slope of MAE vs. density) for OOD samples.
- **Note**: The statistical method was updated from "paired t-tests" to "One-way ANOVA and Tukey HSD" to satisfy the requirements of Plan Task 0.5 and SC-004.

## 5. Constraints
- CPU-only execution (no CUDA).
- Maximum 4GB RAM usage.
- Python 3.9+.
