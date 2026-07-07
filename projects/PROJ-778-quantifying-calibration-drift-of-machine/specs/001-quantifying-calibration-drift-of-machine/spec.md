# Feature Specification: Quantifying Calibration Drift of Machine Learning Classifiers Over Time

**Feature Branch**: `001-calibration-drift`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Quantifying Calibration Drift of Machine Learning Classifiers Over Time"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Fixed Model Training (Priority: P1)

The researcher MUST be able to download yearly snapshots of versioned benchmark datasets (e.g., UCI Adult, Credit Card Default) and train fixed probabilistic classifiers (Logistic Regression, Random Forest) on the earliest snapshot without retraining on subsequent years.

**Why this priority**: This is the foundational step. Without the fixed models and the time-series data, no drift analysis can occur. It establishes the "frozen" baseline required to observe drift.

**Independent Test**: A script runs successfully, downloading two datasets, training two models on the 1994/2005 splits, and saving the model artifacts and test data splits for years 1995-2022/2006-2021.

**Acceptance Scenarios**:

1. **Given** a list of supported dataset sources (UCI, OpenML) and a target year range, **When** the data acquisition module executes, **Then** it downloads the earliest snapshot for training and all subsequent yearly snapshots for testing, saving them to a local directory structure.
2. **Given** the training snapshot and two classifier algorithms (Logistic Regression, Random Forest) with default hyperparameters, **When** the training module executes, **Then** it produces serialized model artifacts and confirms they were trained *only* on the earliest snapshot, ignoring later data.

---

### User Story 2 - Temporal Calibration Metric Computation (Priority: P2)

The system MUST compute calibration metrics (ECE, Brier Score) and covariate shift measures (Wasserstein distance) for each fixed model across every subsequent yearly test split.

**Why this priority**: This generates the primary data points for the analysis. It transforms raw predictions into the statistical signals (drift) required to answer the research question.

**Independent Test**: For a single fixed model and a single later year, the system outputs a JSON record containing ECE, Brier score, and Wasserstein distance, which can be validated against manual calculations on a small subset.

**Acceptance Scenarios**:

1. **Given** a fixed model and a specific year's test split, **When** the evaluation module runs, **Then** it computes Expected Calibration Error (using 10 bins), Brier score, and Wasserstein distance between the training and test feature distributions.
2. **Given** a dataset with multiple years, **When** the evaluation loop completes, **Then** it produces a time-series dataset where each row contains the year, the specific metric values, and the covariate shift magnitude.

---

### User Story 3 - Statistical Trend Analysis and Reporting (Priority: P3)

The system MUST fit linear regression models to test for systematic trends in calibration metrics over time, perform correlation analysis between shift and error, detect change-points, and generate a Markdown report.

**Why this priority**: This addresses the core research question by determining if the observed drift is statistically significant and random or systematic. It produces the final scientific output.

**Independent Test**: The analysis script runs on the time-series data, outputs p-values and correlation coefficients, and generates a Markdown report with at least one time-series plot and one scatter plot.

**Acceptance Scenarios**:

1. **Given** the time-series dataset of calibration metrics, **When** the statistical analysis module runs, **Then** it fits a linear regression model (Year as predictor) and reports the p-value for the slope coefficient (threshold p < 0.05) with the null hypothesis defined as "slope = 0".
2. **Given** the dataset with multiple years, **When** the correlation analysis runs, **Then** it computes the Spearman rank correlation between covariate shift and calibration error, reporting the coefficient and p-value.
3. **Given** the time-series metric data, **When** the change-point detection module runs, **Then** it identifies abrupt shifts using a block-permutation test (block size = 2 years) with 10,000 permutations and alpha = 0.05.
4. **Given** the analysis results, **When** the reporting module executes, **Then** it generates a Markdown file containing a time-series plot of ECE/Brier score over years, a scatter plot of shift magnitude vs. calibration error, and a summary of statistical significance.

---

### Edge Cases

- What happens when a specific year's snapshot is missing from the source repository? (System skips the year and logs a warning; analysis proceeds with available years).
- How does the system handle datasets where the feature schema changes slightly between years (e.g., column renaming)? (System uses a strict schema mapping defined in the configuration; if mapping fails, it aborts with a clear error for that dataset).
- What happens if the intersection of feature columns between training and test snapshots is less than 90% of the original feature set? (System logs a warning and proceeds with the reduced feature set as defined in FR-009).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download yearly snapshots of UCI Adult (earliest available to the most recent year) and Credit Card Default (2005-2021) datasets, ensuring the training set is exclusively the earliest snapshot. (See US-1)
- **FR-002**: System MUST train Logistic Regression and Random Forest classifiers on the earliest snapshot using scikit-learn default hyperparameters and save the models without further updates. (See US-1)
- **FR-003**: System MUST compute Expected Calibration Error (ECE) using a binned approximation. and Brier Score for predictions made on each subsequent yearly test split. (See US-2)
- **FR-004**: System MUST calculate covariate shift using Wasserstein distance on RAW (non-standardized) feature vectors between the training snapshot and each test snapshot to avoid circularity with drift. (See US-2)
- **FR-005**: System MUST fit a simple linear regression model with "Year" as the predictor to test for systematic calibration trends, reporting p-values < 0.05 as significant, with the null hypothesis explicitly defined as "slope = 0". (See US-3)
- **FR-006**: System MUST perform a block-permutation change-point detection analysis (block size = 2 years) with 10,000 permutations and alpha = 0.05 to identify abrupt shifts in calibration metrics. (See US-3)
- **FR-007**: System MUST generate a Markdown report containing time-series plots of metrics and scatter plots linking covariate shift to calibration error. (See US-3)
- **FR-008**: System MUST perform a schema alignment step: it identifies the intersection of feature columns present in the training snapshot and the current test snapshot. Covariate shift is computed only on this common subset. (See US-2)
- **FR-009**: System MUST compute the Spearman rank correlation coefficient between covariate shift magnitude and calibration error, and report the coefficient and p-value. (See US-3)
- **FR-010**: System MUST validate the robustness of the correlation result by verifying the Spearman coefficient remains consistent (within ±0.1) across ECE binning strategies of 5, 10, and 20 bins. (See US-3)

### Key Entities

- **DatasetSnapshot**: Represents a specific yearly version of a benchmark dataset (e.g., Adult-1994), containing features and labels.
- **FixedModel**: A serialized classifier trained on a single snapshot, used for inference on all subsequent snapshots.
- **CalibrationMetricRecord**: A data point containing the year, dataset, model type, ECE, Brier score, and covariate shift value.
- **DriftAnalysisResult**: The statistical output containing p-values, coefficients, and change-point locations.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Calibration drift magnitude (slope of ECE change per year) is measured against the null hypothesis of zero drift (slope = 0) using the linear regression p-value. (See FR-005)
- **SC-002**: The correlation between covariate shift magnitude and calibration error is measured against a Spearman rank correlation coefficient threshold of |rho| ≥ 0.3 with p < 0.05, and must remain robust (within ±0.1) across ECE binning strategies of 5, 10, and 20 bins. (See FR-009, FR-010)
- **SC-003**: The existence of abrupt shifts is measured against the block-permutation change-point detection algorithm's 95% confidence interval; a shift is confirmed if the interval does not include the null hypothesis of no change. (See FR-006)
- **SC-004**: Computational feasibility is measured against the constraint of completing the full analysis (download, train, evaluate, analyze) within 6 hours on a 2-core CPU-only runner with ≤7 GB RAM. (See FR-001, FR-002, FR-003)

## Assumptions

- The UCI and OpenML repositories provide stable, versioned yearly snapshots for the specified years (s-2022 for Adult, 2005-2021 for Credit Card) that can be accessed via `wget`/`curl` without authentication.
- The feature schema (column names and types) remains consistent enough across yearly snapshots to allow the intersection-based feature alignment defined in FR-008 without complex imputation logic.
- The datasets are small enough to fit entirely in available RAM when loaded simultaneously for training and evaluation., or can be streamed/processed in batches without exceeding memory limits.
- The `statsmodels` library for linear regression and `ruptures` library for change-point detection are available and compatible with the CPU-only environment.
- The "default" hyperparameters for Logistic Regression and Random Forest in the installed version of scikit-learn are sufficient for the baseline analysis and do not require tuning.
- The feature distributions may shift over time, and the Wasserstein distance calculation (FR-004) will be performed on raw feature vectors to capture this divergence without standardization artifacts.