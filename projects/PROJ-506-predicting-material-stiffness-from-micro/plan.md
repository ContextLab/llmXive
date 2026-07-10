# Project Plan: Predicting Material Stiffness from Microstructure Images

## Overview
This project aims to develop a Convolutional Neural Network (CNN) to predict the effective stiffness tensor of 2D microstructures from their image representations. The methodology relies on FFT-based numerical homogenization for ground truth generation and rigorous statistical analysis for model validation.

## Phase 0: Governance & Constitution Amendment
- **Task 0.1**: Justify shift to FFT-based homogenization (T001).
- **Task 0.2**: Amend Constitution Principle VI (T002).
- **Task 0.3**: Update project state artifact hashes (T003).
- **Task 0.4**: Update spec resolution to 128x128 (T004).
- **Task 0.5**: **Update statistical methodology to One-way ANOVA and Tukey HSD** (T005).

## Phase 1: Setup
- Initialize project structure and dependencies.
- Configure linting and formatting tools.

## Phase 2: Foundational
- Implement FFT-based homogenization solver (`code/utils/fft_homogenization.py`).
- Implement utility metrics (MAE, MSE, R2).
- Setup k-fold cross-validation utilities.
- Define data and model output schemas.

## Phase 3: User Story 1 - Data Generation
- Generate synthetic microstructures with varying void/inclusion densities.
- Compute effective stiffness tensors using the FFT solver.
- Validate physical plausibility (Voigt-Reuss-Hill bounds).
- Orchestrate pipeline and log metadata.

## Phase 4: User Story 2 - Model Training
- Implement shallow CNN architecture.
- Implement training loop with Adam optimizer.
- Integrate stratified k-fold cross-validation (by density and topology).
- Implement data streaming to respect RAM limits.
- Evaluate on held-out test sets.

## Phase 5: User Story 3 - Generalization & Analysis
- **Statistical Test (Task 3.2)**: Perform **One-way ANOVA** on prediction errors across density bins. If significant, perform **Tukey HSD** post-hoc tests to identify specific pairwise differences. This replaces the previously planned paired t-tests.
- Define OOD thresholds based on training density distribution.
- Calculate degradation rate metrics for out-of-distribution densities.
- Generate comprehensive analysis report including ANOVA tables and degradation plots.
- Verify success criteria (SC-001, SC-002, SC-004) using the new statistical methods.

## Success Criteria
- **SC-001**: Model MAE on held-out test set is within acceptable threshold.
- **SC-002**: Quantitative degradation rate for OOD densities is reported and within limits.
- **SC-004**: **One-way ANOVA** shows no significant difference in errors across density bins (p > 0.05), supported by **Tukey HSD** analysis.
- **SC-005**: Stability of R-squared values across 5 folds is within acceptable variance.

## Methodology Notes
- **Homogenization**: FFT-based numerical homogenization is the primary method for ground truth calculation.
- **Resolution**: 128x128 pixels (amended from 256x256).
- **Statistics**: **One-way ANOVA** and **Tukey HSD** are the primary statistical tools for generalization analysis (amended from paired t-tests).
