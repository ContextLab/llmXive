# Specification: Predicting Material Stiffness from Microstructure Images

## 1. Introduction
This project aims to develop a Convolutional Neural Network (CNN) to predict the effective elastic stiffness of composite materials based on their 2D microstructure images.

## 2. Functional Requirements

### FR-001: Image Resolution
The system shall generate and process microstructure images with a resolution of **128x128 pixels**. This resolution is chosen to balance computational efficiency with sufficient detail for feature extraction.
**Acceptance Criteria:** All generated images in `data/raw/` must be 128x128 pixels.
**Reference:** US-1 Acceptance Scenario 1.

### FR-002: Ground Truth Calculation
The system shall compute the effective elastic stiffness tensor using FFT-based numerical homogenization as the ground truth for training.

### FR-003: Model Architecture
The system shall implement a shallow CNN architecture suitable for CPU-based training.

### FR-004: Training Convergence
The training process shall converge when validation loss plateaus or a maximum number of epochs is reached.

### FR-005: Stratified Cross-Validation
The training process shall use k-fold cross-validation stratified by inclusion density and topology type.

### FR-006: Evaluation Metrics
The system shall report MAE, MSE, and R2 scores on a held-out test set.

### FR-007: Statistical Analysis
The system shall perform statistical analysis using **One-way ANOVA and Tukey HSD** to evaluate prediction errors across different density groups.

### FR-008: OOD Detection
The system shall flag predictions for out-of-distribution density ranges.

## 3. User Stories

### US-1: Synthetic Data Generation
As a researcher, I want to generate synthetic microstructure images with known ground truth stiffness so that I can train a supervised model.
**Acceptance Scenario 1:** The system generates 128x128 pixel images and computes stiffness tensors that satisfy Voigt-Reuss-Hill bounds.

### US-2: Model Training
As a researcher, I want to train a CNN on CPU to predict stiffness so that I can evaluate the model's performance.

### US-3: Generalization Analysis
As a researcher, I want to analyze model generalization and statistical significance so that I can understand the model's limitations.

## 4. Constraints
- Training must complete within 6 hours on a 2-core CPU.
- Memory usage must not exceed 7GB RAM.
- All data generation must be reproducible via random seeds.
