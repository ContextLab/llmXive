# Project Specification: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## 1. Introduction

This project evaluates the performance of various Uncertainty Quantification (UQ) techniques
when applied to machine learning models predicting materials properties. The focus is on
reproducibility, statistical rigor, and practical applicability in a resource-constrained
environment (CPU-only, limited RAM).

## 2. User Stories

### US1: Reproducible UQ Pipeline Execution
As a researcher, I want to run a single orchestrated script that downloads data, trains baseline models,
applies 4 UQ methods, and outputs metrics, so that I can verify the reproducibility of the pipeline.

### US2: Calibration and Sharpness Metric Calculation
As a researcher, I want to calculate Calibration Error and Prediction Interval Sharpness for all test predictions,
so that I can quantitatively compare the quality of uncertainty estimates.

### US3: Statistical Significance and Sensitivity Analysis
As a researcher, I want to perform statistical significance testing (Paired Wilcoxon) and sensitivity analysis
on conformal thresholds, so that I can determine if observed differences are statistically meaningful.

## 3. Functional Requirements

### FR-001: Data Sources
The system must use real, publicly available datasets.
- **Band Gap**: OQMD (Open Quantum Materials Database)
- **Formation Energy**: OQMD (Substituted for Elastic Modulus due to data unavailability)
- **Thermal Conductivity**: AFLOW
- *Amendment*: Elastic Modulus (Materials Project) is substituted with Formation Energy (OQMD).

### FR-002: Model Constraints
All models must be runnable on CPU-only environments with minimal RAM usage (< 2GB total).
- No GPU acceleration.
- No 8-bit quantization.
- Use XGBoost or small MLPs only.
- Maximum ensemble size: 3 models.
- Maximum MC Dropout passes: 200.

### FR-003: Featurization
The system must convert raw compositions/structures to feature vectors using `matminer` (or fallback to `pymatgen`).
- Must enforce a hard cap on samples per dataset based on available memory.
- Must implement stratified train/validation/test split by property range.

### FR-004: Statistical Testing
The system must perform **Paired Wilcoxon Signed-Rank tests** to compare UQ methods.
- Tests must be paired on per-sample errors (same test set).
- Independent-sample t-tests or ANOVA are explicitly forbidden.
- *Amendment*: Replaces original independent-sample requirement to align with the Constitution.

### FR-005: Output Formats
All outputs must be saved in CSV format with defined schemas.
- `per_sample_errors.csv`: Contains sample-level predictions and errors.
- `metrics_raw.csv`: Contains calibration and sharpness metrics.
- `statistical_report.csv`: Contains p-values and significance flags.
- `sensitivity_report.csv`: Contains coverage trade-offs.

## 4. Non-Functional Requirements

### NFR-001: Performance
- Total pipeline execution time must be < 1 hour on CPU-only runner.
- Memory usage must not exceed 2GB at any point.

### NFR-002: Reliability
- The system must handle API rate limits and failures gracefully.
- Partial results must be saved even if some methods fail.

### NFR-003: Reproducibility
- Fixed random seeds must be used for all stochastic processes.
- All dependencies must be pinned in `requirements.txt`.

## 5. Success Criteria

### SC-001: Pipeline Execution
The pipeline script (`code/pipeline.py`) must complete without errors on a subset of data.

### SC-002: Metric Calculation
Calibration Error and Sharpness metrics must be calculated for all methods and datasets.

### SC-003: Statistical Significance
Paired Wilcoxon tests must be executed and p-values reported for method comparisons.

### SC-004: Sensitivity Analysis
Sensitivity analysis must sweep coverage levels from 0.80 to 0.99 with step size 0.01.

### SC-005: Dataset Coverage
The system must successfully process and evaluate the following datasets:
1. **Band Gap** (from OQMD)
2. **Thermal Conductivity** (from AFLOW)
3. **Formation Energy** (from OQMD, substituted for Elastic Modulus)

## 6. Assumptions & Constraints

- Test set size must be >= 100 samples for statistical tests to be considered conclusive.
- API access to OQMD and AFLOW is assumed to be available; fallback to pre-processed CSVs if API fails.
- All code must be Python 3.11 compatible.

## 7. Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2024-01-01 | Team | Initial draft |
| 1.1 | 2024-01-02 | Team | FR-001: Substituted Elastic Modulus with Formation Energy |
| 1.2 | 2024-01-03 | Team | FR-004: Changed to Paired Wilcoxon test |
| 1.3 | 2024-01-04 | Team | SC-005: Explicitly listed Band Gap, Thermal Conductivity, Formation Energy |