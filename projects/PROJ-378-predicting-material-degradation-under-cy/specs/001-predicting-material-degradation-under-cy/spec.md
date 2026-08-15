# Feature Specification: Predicting Material Degradation Under Cyclic Loading from Public Datasets

**Feature Branch**: `001-predict-material-degradation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Material Degradation Under Cyclic Loading from Public Datasets"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1)

A researcher needs to aggregate public fatigue datasets from Materials Project, NIST, and UCI repositories, extract material composition (elemental percentages, heat treatment) and loading parameters (stress amplitude, frequency, R-ratio), and compute degradation targets (remaining useful life, stiffness loss) into a unified, clean dataset ready for analysis.

**Why this priority**: Without a unified, validated dataset containing all required predictors and outcomes, no modeling or statistical inference can occur. This is the foundational step.

**Independent Test**: The system can be tested by running the ingestion script against a mock or small subset of the target repositories and verifying the output CSV contains the specific columns for composition, loading, and degradation metrics with no missing critical values after imputation.

**Acceptance Scenarios**:

1. **Given** a set of public fatigue dataset URLs, **When** the ingestion pipeline executes, **Then** it produces a unified CSV where every row contains valid elemental percentages, stress amplitude, and a degradation metric.
2. **Given** a dataset with missing elemental percentages, **When** the iterative imputation (max_iter=10) is applied, **Then** the missing values are filled with plausible estimates without dropping the row, and the imputation method is logged.
3. **Given** a dataset where the target variable (e.g., stiffness loss) is reported as a time-series, **When** the extraction logic runs, **Then** it calculates a single scalar degradation rate per experiment to match the regression model input requirements.

---

### User Story 2 - Baseline Model Training and Cross-Validation (Priority: P2)

A researcher needs to train baseline regression models (ElasticNet, Random Forest, Gradient Boosting) on the prepared dataset using 5-fold cross-validation to establish a performance baseline (R²) and identify if composition and loading parameters are sufficient predictors.

**Why this priority**: This delivers the core scientific value: determining if the hypothesis (composition + loading predict degradation) holds. It must run within CPU constraints to be feasible.

**Independent Test**: The system can be tested by executing the training script on a small sample (e.g., 100 rows) and verifying that all three models complete training, produce cross-validated R² scores, and that the R² for the best model is reported in the summary log.

**Acceptance Scenarios**:

1. **Given** the unified dataset, **When** the training script runs, **Then** it trains ElasticNet, Random Forest, and Gradient Boosting models with `max_depth=5` and `k=5` cross-validation folds.
2. **Given** the training results, **When** the evaluation completes, **Then** the system outputs the mean R² score for each model and identifies the best-performing model based on the highest mean R².
3. **Given** a dataset that exceeds the 7 GB RAM limit, **When** the script detects memory pressure, **Then** it automatically subsamples the data to fit within the constraint while maintaining class balance (if applicable) or random representativeness, and logs the sampling ratio.

---

### User Story 3 - Statistical Inference and Uncertainty Quantification (Priority: P3)

A researcher needs to perform statistical significance testing on feature coefficients (with Bonferroni correction) and generate prediction intervals using Quantile Regression Forests to understand the reliability of the predictions and the dominant predictors.

**Why this priority**: This adds scientific rigor, addressing the "methodological soundness" requirements for inference framing and uncertainty, distinguishing this from a simple "black box" prediction.

**Independent Test**: The system can be tested by running the inference module on the best model from Story 2 and verifying that a p-value table with Bonferroni correction is generated and that prediction intervals (e.g., 10th and 90th percentiles) are calculated for a set of test points.

**Acceptance Scenarios**:

1. **Given** the trained models, **When** the statistical analysis runs, **Then** it performs t-tests on feature coefficients and applies Bonferroni correction (α=0.05) to flag significant predictors.
2. **Given** a set of new material/loading inputs, **When** the uncertainty module runs, **Then** it generates prediction intervals (e.g., 5th-95th percentile) alongside the point estimate for the degradation metric.
3. **Given** multiple hypotheses tested simultaneously, **When** the correction is applied, **Then** the system explicitly reports the adjusted p-values and flags any features that lose significance after correction.

---

### Edge Cases

- What happens when a public dataset lacks a critical variable (e.g., stress amplitude) required for the regression? The system must log a `[NEEDS CLARIFICATION]` marker for that specific dataset and exclude it from the training set rather than crashing.
- How does the system handle datasets where the degradation metric is censored (e.g., "survived > 10^6 cycles" without a precise failure point)? The system must exclude these rows or apply a specific survival-analysis approximation if the method supports it, otherwise log a warning.
- How does the system handle extreme outliers in elemental percentages (e.g., >100% due to data entry error)? The system must cap values at [deferred] and log the correction, or drop the row if the error is unresolvable.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest data from Materials Project, NIST, and UCI repositories, extracting composition, loading, and degradation variables, and output a unified CSV with ≥95% row retention after imputation (See US-1).
- **FR-002**: System MUST apply iterative imputation (max_iter=10) to handle missing values in predictor variables without dropping rows (See US-1).
- **FR-003**: System MUST train ElasticNet, Random Forest, and Gradient Boosting regressors with `max_depth=5` and `k=5` cross-validation folds on the unified dataset (See US-2).
- **FR-004**: System MUST calculate and report the mean R² score for each model and identify the best-performing model based on the highest mean R² (See US-2).
- **FR-005**: System MUST perform t-tests on feature coefficients and apply Bonferroni correction (α=0.05) to determine statistical significance of predictors (See US-3).
- **FR-006**: System MUST generate prediction intervals (e.g., 10th-90th percentiles) using Quantile Regression Forests for all point estimates (See US-3).
- **FR-007**: System MUST enforce a memory limit of 7 GB and a disk limit of 14 GB, automatically subsampling the dataset if these limits are approached (See US-2).

### Key Entities

- **MaterialSample**: Represents a single experimental entry with attributes: `composition` (map of element->percent), `loading_params` (stress, frequency, R-ratio), `degradation_metric` (target variable), `source_id`.
- **ModelResult**: Represents the output of a training run with attributes: `model_type`, `mean_r2`, `std_r2`, `feature_importance`, `p_values`.
- **PredictionInterval**: Represents the uncertainty bound for a prediction with attributes: `point_estimate`, `lower_bound`, `upper_bound`, `confidence_level`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The mean R² score of the best-performing model is measured against the hypothesis threshold of 0.6 to determine if composition and loading are sufficient predictors (See US-2).
- **SC-002**: The percentage of rows retained after imputation is measured against the [deferred] target to ensure data integrity and minimal information loss (See US-1).
- **SC-003**: The number of statistically significant predictors (after Bonferroni correction) is measured against the null hypothesis of zero significant predictors to validate the model's explanatory power (See US-3).
- **SC-004**: The width of the prediction intervals (90th percentile - 10th percentile) is measured against the standard deviation of the target variable to assess the utility of the uncertainty estimates (See US-3).
- **SC-005**: The total execution time of the pipeline is measured against the 6-hour limit to ensure feasibility on free-tier CI runners (See US-2).

## Assumptions

- The public datasets (Materials Project, NIST, UCI) contain the necessary variables (elemental percentages, stress amplitude, frequency, R-ratio, and a degradation metric) for the analysis; if a dataset lacks a critical variable, it is excluded.
- The degradation metrics (e.g., remaining useful life, stiffness loss) can be derived as scalar values from the reported experimental outcomes without requiring complex time-series analysis.
- The dataset size, even after aggregation from multiple sources, will fit within the 14 GB disk and 7 GB RAM constraints of the free-tier runner, possibly requiring subsampling.
- The relationship between material composition/loading and degradation is primarily linear or non-linear but monotonic, making tree-based and regularized linear models appropriate baselines.
- The Bonferroni correction is sufficient for controlling the family-wise error rate given the number of features (predictors) being tested.
- No GPU acceleration is required or available; all models must run on CPU in default precision.
- The "best" model is defined strictly by the highest cross-validated R² score, ignoring other metrics like RMSE or MAE for the primary success criterion.
