# Project Specification: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## 1. Introduction

### 1.1 Purpose
This document defines the requirements for a research pipeline that evaluates
Uncertainty Quantification (UQ) methods on material property predictions.
The system will download real datasets, train baseline models, apply UQ methods,
and statistically validate the results.

### 1.2 Scope
- Download and process real materials science datasets (OQMD, AFLOW).
- Implement 4 UQ methods: Gaussian Process Regression, MC Dropout, Deep Ensemble, Conformal Prediction.
- Calculate Calibration and Sharpness metrics.
- Perform Paired Wilcoxon Signed-Rank tests for statistical significance.

## 2. Functional Requirements

### FR-001: Data Acquisition
The system shall download and process the following real datasets:
- **Band Gap**: From OQMD.
- **Thermal Conductivity**: From AFLOW.
- **Formation Energy**: From OQMD (Substituted for Elastic Modulus due to data unavailability).

*Amendment*: Original FR-001 specified Elastic Modulus (Materials Project). This is updated to Formation Energy (OQMD) to ensure data availability.

### FR-002: Featurization
The system shall convert raw material compositions/structures into feature vectors
using `matminer` or `pymatgen`.

### FR-003: UQ Implementation
The system shall implement:
- GPR (sklearn)
- MC Dropout (PyTorch)
- Deep Ensemble (XGBoost/MLP)
- Conformal Prediction (split-conformal)

### FR-004: Statistical Validation
The system shall perform **Paired Wilcoxon Signed-Rank tests** to compare UQ methods.
*Amendment*: Original requirement for independent t-tests is replaced by Paired Wilcoxon
to align with the Constitution and Plan, as methods are evaluated on the same test set.

## 3. Success Criteria

### SC-001: Reproducibility
The pipeline must run end-to-end on a standard CPU-only environment within 1 hour.

### SC-002: Data Integrity
All input data must be fetched from real, programmatically accessible sources (OQMD, AFLOW)
with checksum validation. No synthetic data generation for inputs.

### SC-003: Statistical Rigor
All comparative analyses must use the Paired Wilcoxon Signed-Rank test as defined in FR-004.

### SC-004: Metric Calculation
Calibration Error and Prediction Interval Sharpness must be calculated for all methods.

### SC-005: Dataset Coverage
The evaluation must cover the following specific datasets:
1. **Band Gap**
2. **Thermal Conductivity**
3. **Formation Energy**

## 4. Non-Functional Requirements

### NFR-001: Performance
Total RAM usage must not exceed 2GB during execution.

### NFR-002: Error Handling
The system must handle API rate limits and data fetch failures gracefully,
logging errors and attempting fallbacks where specified.

### NFR-003: Code Quality
Code must pass `ruff` linting and `black` formatting checks.

## 5. Data Models

- **MaterialsDataset**: Container for features, targets, and metadata.
- **UQMethod**: Abstract base for UQ implementations.
- **EvaluationMetric**: Container for calibration and sharpness scores.

## 6. Output Artifacts

- `results/per_sample_errors.csv`: Per-sample predictions and intervals.
- `results/metrics_raw.csv`: Aggregated calibration and sharpness metrics.
- `results/statistical_report.csv`: Paired Wilcoxon test results.
- `results/sensitivity_report.csv`: Conformal threshold sensitivity analysis.