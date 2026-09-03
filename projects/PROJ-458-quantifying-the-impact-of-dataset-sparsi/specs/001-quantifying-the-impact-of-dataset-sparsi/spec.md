# Specification: Quantifying the Impact of Dataset Sparsity on Materials Property Prediction

## Overview
This project investigates how dataset size (sparsity) affects the predictive performance and uncertainty calibration of machine learning models for materials property prediction.

## User Stories

### US-0: Spec Alignment and Foundation
**Goal**: Ensure specification matches implementation plan and foundational infrastructure is in place.
- [x] Align FR-003 with Plan: Use Representative Stratified Sample (RSS) instead of full dataset.
- [x] Align FR-006 with Plan: Use Linear Mixed-Effects Modeling (LMM) instead of Repeated Measures ANOVA.
- [x] Align Assumptions with Plan: Require MP_API_KEY environment variable.
- [x] Align FR-007 with Plan: Explicitly include "slope variance < 10%" threshold.
- [x] Align US-3 Acceptance Scenario 3 with Plan: Reflect "slope variance < 10%" threshold.
- [x] Align SC-003 with Plan: Replace "Repeated Measures ANOVA" with "Linear Mixed-Effects Modeling (LMM)".

### US-1: Data Retrieval and Preprocessing Pipeline
**Goal**: Download, filter, and engineer features for the Materials Project dataset.
- **FR-001**: Download at least 30,000 entries from Materials Project API.
- **FR-002**: Filter entries to retain only those with valid formation_energy and dft_computed=True.
- **FR-003**: Generate elemental property descriptors using matminer.
- **FR-004**: Impute missing values using training pool statistics only.
- **FR-005**: Cap training pool at RSS_SIZE entries using stratified sampling.
- **FR-009**: Create a Fixed Test Set independent of the training pool partitioning.

### US-2: Sparsity Subsampling and Model Training
**Goal**: Generate nested sparsity levels and train models to measure performance degradation.
- **FR-003**: Generate strictly nested stratified subsets ([deferred], [deferred], [deferred], [deferred], [deferred], [deferred], [deferred] of RSS).
- **FR-005**: Train Gaussian Process Regression (GPR) and Random Forest models on CPU only.
- **FR-006**: Evaluate models using RMSE, MAE, Predictive Variance, and Calibration Slope.
- **FR-009**: Ensure test set independence is maintained throughout training.

### US-3: Statistical Analysis and Visualization
**Goal**: Perform statistical validation and generate research artifacts.
- **FR-006**: Perform Linear Mixed-Effects Modeling (LMM) with formula `error ~ sparsity_level + (1|seed)`.
- **FR-007**: Verify elbow point stability with slope variance < 10% between consecutive levels.
- **FR-008**: Generate final report summarizing findings as associational evidence.
- **SC-001**: Measure RMSE, MAE, Predictive Variance, and Calibration Slope.
- **SC-002**: Generate learning curves (error vs. dataset size) with error bars.
- **SC-003**: Apply pairwise contrasts with Tukey-adjusted p-values to LMM results to report p-values for differences between sparsity levels (threshold p < 0.05).

## Functional Requirements

### FR-003: Representative Stratified Sample (RSS)
The training pool shall be capped at a Representative Stratified Sample (RSS) of sufficient size to ensure statistical robustness. The sparsity levels shall span a range from highly sparse to fully dense configurations.

### FR-005: Model Evaluation Metrics
Models shall be evaluated using RMSE, MAE, Predictive Variance, and Calibration Slope.

### FR-006: Statistical Analysis Method
Statistical analysis shall use Linear Mixed-Effects Modeling (LMM) with formula `error ~ sparsity_level + (1|seed)` to handle nested sparsity levels. Pairwise contrasts with Tukey-adjusted p-values shall be applied.

### FR-007: Trend Stability Threshold
The slope variance between consecutive sparsity levels shall be < 10% to verify trend stability.

### FR-009: Test Set Independence
A Fixed Test Set shall be created from the raw pool before any training pool partitioning or filtering, ensuring strict independence.

## Assumptions

- Requires MP_API_KEY environment variable to be set.
- Materials Project API is accessible during runtime.
- Sufficient memory is available for descriptor generation (handled by chunked processing).

## Acceptance Scenarios

### SC-001: Metric Calculation
Given a trained model and the Fixed Test Set, when evaluation is performed, then RMSE, MAE, Predictive Variance, and Calibration Slope are calculated and logged.

### SC-002: Learning Curve Generation
Given metrics across all sparsity levels, when learning curves are generated, then error vs. dataset size plots with error bars are produced for multiple sparsity levels ([deferred] to [deferred]).

### SC-003: Statistical Significance Testing
Given LMM results, when pairwise contrasts are applied with Tukey adjustment, then p-values for differences between sparsity levels are reported (threshold p < 0.05).