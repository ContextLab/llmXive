# Feature Specification: Statistical Analysis of Algorithmic Fairness Metrics

**Feature Branch**: `001-fairness-metric-analysis`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "What dataset properties (base rate differences, feature dimensionality, class imbalance) most strongly predict when fairness metrics diverge, and can this prediction enable practitioners to select appropriate metrics for a given dataset without exhaustive multi-metric evaluation?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dataset Download and Preprocessing Pipeline (Priority: P1)

A researcher downloads multiple public datasets from UCI Machine Learning Repository and ProPublica's COMPAS dataset, preprocesses them to extract binary protected attributes and outcomes, and stores them in a privacy-compliant format ready for analysis.

**Why this priority**: Without accessible, preprocessed datasets, no downstream analysis can occur. This is the foundational data acquisition step.

**Independent Test**: Can be fully tested by running the download/preprocess script and verifying ≥5 datasets are present with required columns (protected attribute, outcome, features).

**Acceptance Scenarios**:

1. **Given** the download script is executed with valid dataset identifiers, **When** it completes, **Then** ≥5 datasets exist in the data directory with file size ≤500MB each
2. **Given** a dataset is downloaded, **When** preprocessing runs, **Then** the output contains binary protected attribute column, binary outcome column, and feature matrix with ≥3 features

---

### User Story 2 - Fairness Metric Computation and Correlation Analysis (Priority: P1)

A researcher trains 3-5 baseline models per dataset, calculates 6+ fairness metrics for each model, and computes pairwise correlations between all metric pairs across models and datasets.

**Why this priority**: This delivers the core research output—identifying statistical patterns in fairness metric discrepancies.

**Independent Test**: Can be tested by running the metric computation pipeline on 1 dataset and verifying ≥6 metrics are calculated with correlation matrix output.

**Acceptance Scenarios**:

1. **Given** preprocessed data and trained models, **When** fairness metrics are computed, **Then** ≥6 metrics are calculated (demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, false positive rate disparity)
2. **Given** metric values across models and datasets, **When** correlation analysis runs, **Then** a correlation matrix is output with ≥15 pairwise correlation coefficients (for 6 metrics)

---

### User Story 3 - Regression Modeling and Visualization (Priority: P2)

A researcher fits linear mixed-effects models to predict metric discrepancies from dataset characteristics and generates visualizations (heatmap of metric correlations, scatter plots with regression lines).

**Why this priority**: This enables practitioners to predict when metrics diverge based on dataset properties, advancing practical guidance.

**Independent Test**: Can be tested by running the regression pipeline on 1 dataset and verifying regression coefficients and visualization files are produced.

**Acceptance Scenarios**:

1. **Given** metric discrepancies and dataset characteristics, **When** mixed-effects regression runs, **Then** ≥3 regression coefficients are output with p-values and confidence intervals
2. **Given** completed analysis, **When** visualization is generated, **Then** ≥2 figures are saved (correlation heatmap, scatter plot with regression line)

---

### User Story 4 - Bootstrap Resampling and Confidence Intervals (Priority: P3)

A researcher performs bootstrap resampling (n=1000) to estimate confidence intervals for correlation coefficients and assesses robustness of findings.

**Why this priority**: This provides statistical rigor and quantifies uncertainty in the correlation estimates.

**Independent Test**: Can be tested by running bootstrap on 1 correlation coefficient and verifying confidence interval is output.

**Acceptance Scenarios**:

1. **Given** correlation coefficients, **When** bootstrap resampling runs, **Then** ≥1000 resamples are performed and 95% confidence intervals are computed for each correlation

---

### Edge Cases

- What happens when a dataset lacks a binary protected attribute? The system MUST skip that dataset and log a warning, continuing with ≥5 remaining datasets.
- How does the system handle datasets exceeding 100k rows? The system MUST sample to ≤100k rows before processing to fit within 7 GB RAM constraint.
- What happens when a fairness metric calculation fails for a model (e.g., zero predictions for a class)? The system MUST record NA for that metric-cell and continue without crashing.
- How does the system handle datasets with >3 protected attributes? The system MUST select the first binary protected attribute alphabetically and document this choice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and successfully process ≥5 datasets from UCI Machine Learning Repository and ProPublica's COMPAS dataset, with each dataset ≤500MB after preprocessing validation (See US-1)
- **FR-002**: System MUST preprocess each dataset to extract binary protected attribute, binary outcome, and feature matrix with ≥3 features (See US-1)
- **FR-003**: System MUST train ≥3 baseline models per dataset (logistic regression, random forest, gradient boosting) using scikit-learn (See US-2)
- **FR-004**: System MUST calculate ≥6 fairness metrics per model: demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, false positive rate disparity (See US-2)
- **FR-005**: System MUST compute pairwise Pearson/Spearman correlations between all metric pairs within-dataset (across models), outputting ≥15 correlation coefficients (See US-2)
- **FR-006**: System MUST fit linear mixed-effects models with random intercepts for dataset and random slopes for base rate difference and class imbalance ratio to predict metric discrepancies from dataset characteristics, outputting ≥3 regression coefficients with p-values and confidence intervals (See US-3)
- **FR-007**: System MUST perform bootstrap resampling with n=1000 resamples at dataset level to estimate 95% confidence intervals for correlation coefficients (See US-4)
- **FR-008**: System MUST generate ≥2 visualization outputs: correlation heatmap and scatter plots with regression lines (See US-3)
- **FR-009**: System MUST sample datasets to ≤100k rows if original size exceeds this threshold to fit within 7 GB RAM constraint (See US-1)
- **FR-010**: System MUST apply Bonferroni correction for multiple-comparison testing when reporting statistical significance across ≥15 pairwise correlations (See US-2)

### Key Entities

- **Dataset**: Represents a public dataset with protected attribute, outcome, and feature columns
- **Model**: Represents a trained baseline classifier (logistic regression, random forest, gradient boosting)
- **FairnessMetric**: Represents a computed fairness metric value (demographic parity difference, equalized odds difference, etc.)
- **DatasetCharacteristic**: Represents a dataset property (base rate difference, feature dimensionality, class imbalance ratio)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Number of datasets processed is measured against the minimum requirement of ≥5 datasets (See US-1)
- **SC-002**: Correlation coefficients between fairness metric pairs are measured against statistical significance (p<0.05 with Bonferroni correction) (See US-2)
- **SC-003**: Regression coefficients predicting metric discrepancies from dataset characteristics are measured against statistical significance (p<0.05 with Bonferroni correction) (See US-3)
- **SC-004**: Confidence interval width for correlation coefficients is measured against bootstrap resampling output (n=1000) to quantify uncertainty (See US-4)
- **SC-005**: Total computation time is measured against the 6-hour compute window constraint (See all USs)
- **SC-006**: Memory usage during analysis is measured against ≤7 GB RAM constraint (See all USs)
- **SC-007**: Dataset-variable fit is measured against the requirement that successfully preprocessed UCI/COMPAS datasets contain all required variables (base rate, feature dimensionality, class imbalance, fairness metrics) (See US-1)

## Assumptions

- UCI Machine Learning Repository and ProPublica's COMPAS dataset contain binary protected attributes and binary outcomes for fairness metric computation
- All datasets are accessible via public HTTP/HTTPS endpoints without authentication requirements
- scikit-learn's implementation of fairness metrics (or equivalent custom implementation) is sufficient for calculating demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, and false positive rate disparity
- Linear mixed-effects models can be fit using statsmodels or similar CPU-only library within the allocated compute window
- The 5-8 datasets selected will have sufficient sample size (≥1000 rows after sampling) to support statistical correlation analysis
- Observational design means findings will be framed as associational, not causal relationships between dataset characteristics and fairness metric divergence
- Multiple-comparison correction (Bonferroni) will be applied to control family-wise error rate across ≥15 pairwise correlation tests
- Predictor collinearity between base rate difference and class imbalance ratio will be diagnosed using variance inflation factor (VIF) and reported descriptively rather than claiming independent predictive effects