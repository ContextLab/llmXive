# Feature Specification: Fairness Metric Divergence Analysis

**Feature Branch**: `001-fairness-metric-divergence-analysis`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Analyze statistical patterns in algorithmic fairness metric discrepancies across datasets and predict divergence from dataset characteristics"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dataset Acquisition and Preprocessing (Priority: P1)

As a researcher, I need to download 5-8 public datasets containing binary protected attributes and outcomes, preprocess them to extract fairness-relevant features, and ensure all required variables are present, so that I can proceed with fairness metric computation.

**Why this priority**: This is the foundational step—without valid datasets containing the required variables (protected attribute, outcome, predictions), no subsequent analysis can occur. This delivers value by establishing the empirical basis for the entire study.

**Independent Test**: Can be fully tested by verifying that all target datasets are downloaded, contain required columns, and are within size constraints (≤100k rows, <500MB each), delivering a validated dataset repository.

**Acceptance Scenarios**:

1. **Given** the UCI Adult and COMPAS datasets are available via public URLs, **When** the download script executes, **Then** all 5-8 datasets are stored in the working directory with verified checksums.
2. **Given** a downloaded dataset, **When** the preprocessing module runs, **Then** binary protected attributes (e.g., gender, race) and binary outcomes are extracted, and datasets exceeding 100k rows are sampled to ≤100k.
3. **Given** a dataset lacks a required variable (e.g., no protected attribute), **When** validation runs, **Then** the system logs an exclusion event to logs/exclusion.log with dataset_id and missing_variable_name, and excludes the dataset from analysis. Target datasets (UCI Adult, COMPAS, Bank Marketing, German Credit, Law School Admission) are confirmed to contain required variables.

---

### User Story 2 - Fairness Metric Computation (Priority: P2)

As a researcher, I need to train 3-5 baseline models per dataset and compute Multiple fairness metrics (demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, false positive rate disparity), so that I can quantify metric divergence across models and datasets.

**Why this priority**: This delivers the core empirical measurements—the fairness metric values that will be analyzed for correlations. It depends on US-1 but can be tested independently once datasets are available.

**Independent Test**: Can be fully tested by running the metric computation pipeline on a single dataset and verifying all 6+ metrics are calculated for each model, delivering a metrics matrix.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with 3 trained models, **When** the fairness metric module executes, **Then** all 6+ metrics are computed with documented formulas and stored as structured outputs.
2. **Given** a model prediction set, **When** demographic parity difference is calculated, **Then** the absolute difference in positive prediction rates across protected groups is computed and recorded.
3. **Given** multiple fairness metrics are computed, **When** the output is generated, **Then** each metric value is paired with its model identifier, dataset identifier, and protected attribute for traceability.

---

### User Story 3 - Correlation Analysis and Predictive Modeling (Priority: P3)

As a researcher, I need to compute pairwise correlations between all metric pairs, fit fixed-effects regression models to predict discrepancies from dataset characteristics (base rate difference, feature dimensionality, class imbalance ratio), and perform bootstrap resampling for confidence intervals, so that I can identify systematic patterns and enable metric selection guidance.

**Why this priority**: This delivers the research findings—identifying which dataset properties predict metric divergence. It depends on US-2 but can be tested independently once metrics are available.

**Independent Test**: Can be fully tested by running the analysis pipeline on existing metric outputs and verifying correlation matrices, regression coefficients, and bootstrap confidence intervals are generated, delivering the final research artifacts.

**Acceptance Scenarios**:

1. **Given** a matrix of fairness metric values across datasets and models, **When** the correlation module executes, **Then** all pairwise Pearson/Spearman correlations are computed and stored with p-values and Benjamini-Hochberg corrected q-values.
2. **Given** dataset characteristics (base rate difference, feature dimensionality, class imbalance ratio) and metric discrepancies, **When** the regression module executes, **Then** fixed-effects regression models are fitted with dataset and model as fixed covariates, with VIF diagnostics applied (exclude predictors with VIF > 5), and include interpretation note acknowledging theoretical relationship between base rate difference and demographic parity difference per Constitution Principle VII.
3. **Given** correlation coefficients, **When** bootstrap resampling (n=1000) executes, **Then** 95% confidence intervals are computed and reported for each correlation.

---

### Edge Cases

- What happens when a dataset lacks a binary protected attribute (e.g., only continuous variables available)? → Exclude from analysis and log to logs/exclusion.log with dataset_id and reason. Target datasets (UCI Adult, COMPAS, Bank Marketing, German Credit, Law School Admission) are confirmed to contain binary protected attributes: UCI Adult (gender: male/female), COMPAS (race: white/black), Bank Marketing (age: ≤60/≥60), German Credit (gender: male/female), Law School Admission (race: white/non-white).
- How does the system handle class imbalance ratios >10:1 that may destabilize fairness metric computation? → Apply stratified sampling to balance groups before metric calculation.
- What happens when the 6-hour GHA job window is exceeded during bootstrap resampling? → Reduce bootstrap iterations from 1000 to 500 and log the reduction as a computational constraint.
- How does the system handle datasets with >100 features causing multicollinearity in regression? → Apply variance inflation factor (VIF) diagnostics and exclude predictors with VIF > 5.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download multiple public datasets (UCI Adult, Bank Marketing, COMPAS, etc.) via HTTP/HTTPS with verified file integrity (SHA-256 checksums) (See US-1)
- **FR-002**: System MUST preprocess datasets to extract binary protected attributes (e.g., gender=0/1, race=0/1) and binary outcomes, ensuring no more than 100k rows per dataset. If extraction fails, exclude dataset and log to logs/exclusion.log with dataset_id and missing_variable_name (See US-1)
- **FR-003**: System MUST train multiple baseline models per dataset using scikit-learn (logistic regression, random forest, gradient boosting) with CPU-only execution (See US-2)
- **FR-004**: System MUST compute ≥6 fairness metrics per model: demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, false positive rate disparity (See US-2)
- **FR-005**: System MUST compute pairwise Pearson and Spearman correlations between all metric pairs across models and datasets with p-values and Benjamini-Hochberg false discovery rate correction (α=0.05) (See US-3)
- **FR-006**: System MUST fit fixed-effects regression models to predict metric discrepancies from dataset characteristics (base rate difference, feature dimensionality, class imbalance ratio) with variance inflation factor (VIF) diagnostics; exclude predictors with VIF > 5. Mixed-effects models are documented as fallback but not used due to n=5 datasets < 10 minimum for reliable variance estimation (See US-3)
- **FR-007**: System MUST perform bootstrap resampling (n=1000, reducible to n=500 if needed) to estimate 95% confidence intervals for correlation coefficients (See US-3)
- **FR-008**: System MUST frame all findings as associational, not causal, in all output documentation. All reports and console output must include disclaimer text: "Findings are associational only; no causal claims are made." (See US-3)
- **FR-009**: System MUST generate metric selection guidance output mapping dataset characteristics to recommended fairness metrics based on correlation analysis results (See US-3)

### Key Entities

- **Dataset**: Represents a public ML dataset containing features, protected attributes, and outcomes; key attributes include dataset_id, row_count, feature_count, protected_attribute_name, outcome_name
- **Model**: Represents a trained baseline classifier; key attributes include model_id, model_type, dataset_id, training_parameters
- **FairnessMetric**: Represents a computed fairness metric value; key attributes include metric_name, metric_value, model_id, dataset_id, protected_attribute, confidence_interval
- **DatasetCharacteristic**: Represents a property of the dataset used for prediction; key attributes include characteristic_name (base_rate_difference, feature_dimensionality, class_imbalance_ratio), value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset availability and variable completeness is measured against the research design requirements (≥5 datasets with binary protected attributes and outcomes) (See US-1)
- **SC-002**: Fairness metric computation accuracy is measured against the documented mathematical formulas for each metric (demographic parity, equalized odds, etc.) documented in Appendix A (Formula Reference) (See US-2)
- **SC-003**: Correlation analysis completeness is measured against the total number of metric pairs (≥15 pairs for 6 metrics) with reported p-values and confidence intervals (See US-3)
- **SC-004**: Multiple-comparison correction is measured against the family-wise error rate using Bonferroni or Benjamini-Hochberg correction across all correlation tests (See US-3)
- **SC-005**: Sample size/power adequacy is measured against the number of dataset-model combinations (≥15 observations: 5 datasets × 3 models) for regression stability (See US-3)

## Assumptions

- Public datasets (UCI Adult, COMPAS, Bank Marketing) are available via stable HTTP/HTTPS URLs and will not change during the 6-hour job window
- All target datasets contain binary protected attributes (e.g., gender, race) and binary outcomes required for fairness metric computation
- scikit-learn and statsmodels libraries are available in the GitHub Actions free-tier environment with CPU-only execution
- The 6-hour GitHub Actions job window is sufficient for downloading ≤8 datasets, training 3-5 models per dataset, and running bootstrap resampling with 1000 iterations
- Fixed-effects regression will converge within the computational constraints; non-convergence will trigger a fallback to reduced predictor set
- Fairness metric formulas follow standard definitions from Hardt et al., Chouldechova, and Kleinberg et al. as referenced in related work
- No GPU or CUDA accelerators are available or required; all computations use CPU-only default precision
- Dataset sizes after preprocessing will fit within allocated RAM and disk limits
- The observed correlations are associational only; no causal claims are made about dataset properties causing metric divergence
- If any dataset lacks a required variable (protected attribute or outcome), it will be excluded from analysis and logged as exclusion event to logs/exclusion.log