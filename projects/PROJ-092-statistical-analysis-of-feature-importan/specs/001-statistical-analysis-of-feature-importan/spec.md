# Feature Specification: Statistical Analysis of Feature Importance Drift in Pre-trained Models

**Feature Branch**: `001-feature-importance-drift`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Feature Importance Drift in Pre-trained Models"

## User Scenarios & Testing

### User Story 1 - Baseline Model Training and Windowed Importance Calculation (Priority: P1)

**Description**: The system must ingest the UCI Electricity Load Diagrams dataset, split it into sequential 30-day windows, train a baseline Random Forest model on the initial window, and compute permutation importance scores for all features within that baseline and subsequent windows.

**Why this priority**: This is the foundational step. Without a trained model and computed importance scores for each time window, no drift analysis can occur. It establishes the data structure required for all downstream statistical tests.

**Independent Test**: Can be fully tested by running the data preprocessing and training script, verifying that a `RandomForestRegressor` is fitted on the first 30 days, and that a CSV or JSON file is generated containing feature names and their corresponding importance scores for that window and the next 5 windows.

**Acceptance Scenarios**:

1. **Given** the UCI Electricity Load Diagrams dataset is downloaded and preprocessed, **When** the system splits data into 30-day sequential windows, **Then** the system must generate at least 6 distinct time windows covering the period from 2011 to 2014.
2. **Given** the initial 30-day training window, **When** a Random Forest model (max_depth=10, n_estimators=100) is trained, **Then** the system must validate the R² score on the last [deferred] (6 days) of that window; if R² < 0.8, the system MUST skip that window and log a "Model Failure" error (See FR-003b).
3. **Given** a trained model and a subsequent 30-day window, **When** permutation importance is calculated, **Then** the output must list importance scores for all input features, sorted in descending order, without raising memory errors on a 4GB RAM constraint.

---

### User Story 2 - Drift Quantification via Rank Correlation (Priority: P2)

**Description**: The system must calculate Spearman rank correlation coefficients between the feature importance rankings of consecutive time windows and identify the magnitude of drift over time.

**Why this priority**: This implements the core research question: quantifying how rankings change. It transforms raw importance scores into a statistical metric (drift magnitude) that can be analyzed for trends.

**Independent Test**: Can be fully tested by executing the correlation calculation module on the importance scores generated in User Story 1, verifying that a time-series of correlation coefficients (rho) is produced for each window transition.

**Acceptance Scenarios**:

1. **Given** importance rankings for Window T and Window T+1, **When** the system calculates Spearman's rho, **Then** the result must be a floating-point value between -1.0 and 1.0.
2. **Given** a sequence of 6 windows, **When** the system computes pairwise correlations for all adjacent windows, **Then** the output must contain correlation coefficients representing the drift trajectory.
3. **Given** the computed correlation sequence, **When** the system detects a drop in correlation, **Then** the system must flag this transition as a "high drift" warning event ONLY if the block permutation p-value < 0.05 (See FR-004b).

---

### User Story 3 - Statistical Significance Testing and Trend Detection (Priority: P3)

**Description**: The system must apply a Mann-Kendall trend test to determine the direction of drift and a block permutation-based significance test (shuffling the chronological order of windows) to determine if the observed drift is statistically significant and distinguishable from random variation.

**Why this priority**: This addresses the "statistically distinguished" part of the research question. It moves beyond observation to inference, validating whether the drift is a real phenomenon or noise, using a method robust to small sample sizes and preserving the temporal structure of the data.

**Independent Test**: Can be fully tested by running the statistical inference script on the correlation sequence, verifying that a p-value (from block permutation) and a trend direction (increasing/decreasing/no trend) are returned.

**Acceptance Scenarios**:

1. **Given** a sequence of at least 5 Spearman correlation coefficients, **When** the Mann-Kendall test is applied, **Then** the system must return a Kendall's Tau statistic.
2. **Given** a negative Kendall's Tau statistic, **When** the system evaluates the trend direction, **Then** the system must report a "monotonic decrease" in feature importance stability (See FR-005).
3. **Given** a sequence of correlation coefficients, **When** the block permutation-based significance test (1000 resamples of the time order) is run, **Then** the system must return a p-value representing the probability of observing such a trend under the null hypothesis of no temporal drift (See FR-008).

### Edge Cases

- What happens if a specific time window contains missing values for a feature that was present in the baseline? (System MUST first attempt median imputation per feature as defined in FR-001. If imputation results in a feature with zero variance across the window, the system MUST drop that feature for that specific window to maintain rank integrity).
- How does the system handle a scenario where the Random Forest model fails to converge or produces zero importance for all features in a specific window? (System must log a critical error and skip that specific window to prevent division-by-zero or invalid correlation errors).
- What if the dataset has fewer than 6 windows of 30 days each? (System must raise a configuration error indicating insufficient data for the Mann-Kendall trend test, which requires a minimum of 5 data points. Note: Due to small sample size (n=5-6), the asymptotic Mann-Kendall p-value is unreliable; the system MUST rely on the block permutation-based test defined in FR-008. With n=5, the minimum achievable p-value is 0.05, which is interpreted as statistically significant at the [deferred] level).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess the UCI Electricity Load Diagrams 2011-2014 dataset, ensuring all timestamps are normalized and missing values are handled via median imputation per feature (See US-1).
- **FR-002**: System MUST split the preprocessed time-series data into sequential, non-overlapping 30-day windows, maintaining chronological order (See US-1).
- **FR-003**: System MUST train a Random Forest Regressor (n_estimators=100, max_depth=10) on the first 30-day window and compute permutation importance for all features using a fixed random seed (42) for both the model training and the permutation importance calculation, using the last [deferred] (6 days) of the window as a held-out validation set (See US-1).
- **FR-003b**: System MUST validate the R² score on the held-out validation set; if R² < 0.8, the system MUST skip processing for that window and log a "Model Failure" error, preventing the use of invalid importance scores (See US-1).
- **FR-004**: System MUST calculate Spearman rank correlation coefficients between the feature importance rankings of every adjacent pair of time windows (See US-2).
- **FR-004b**: System MUST flag any transition as a "high drift" warning ONLY if the block permutation p-value < 0.05, as this threshold represents statistical significance in the context of the null hypothesis of no temporal drift (See US-2).
- **FR-005**: System MUST apply the Mann-Kendall trend test to the sequence of Spearman correlation coefficients to detect monotonic trends and return a Kendall's Tau statistic; a negative Tau indicates a decreasing trend. Note: The Mann-Kendall test is used only for trend direction; significance is determined by the block permutation test (See US-3).
- **FR-006**: System MUST output a CSV file containing the window ID, timestamp, feature importance rankings, and the calculated drift metrics (Spearman rho, Kendall tau, p-value) (See US-3).
- **FR-007**: System MUST generate a Null Model Baseline by shuffling the chronological order of the time windows (block permutation) and recalculating importance rankings to distinguish actual drift from random temporal noise (See US-2).
- **FR-008**: System MUST perform a block permutation-based significance test (1000 resamples of the time order) on the correlation sequence to determine statistical significance, as the asymptotic Mann-Kendall test is invalid for n < 10 (See US-3).

### Key Entities

- **TimeWindow**: A data structure representing a 30-day slice of the time-series data, containing the raw feature matrix and target variable.
- **ImportanceProfile**: A vector of feature importance scores associated with a specific TimeWindow and a specific model state.
- **DriftMetric**: A record containing the correlation coefficient (Spearman rho) between two ImportanceProfiles and the statistical significance (p-value) of the trend.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of feature importance drift is measured against the baseline correlation (rho=1.0) using the Spearman rank coefficient (See US-2).
- **SC-002**: The statistical significance of the drift trend is measured against the standard alpha threshold of 0.05 using the block permutation-based p-value (See US-3).
- **SC-003**: The robustness of the drift detection is measured against the stability of the baseline model (R² > 0.8) to ensure drift is not caused by model failure (See US-1).
- **SC-004**: The validity of the drift signal is measured against the Null Model Baseline (FR-007) using block permutation of time windows to confirm the observed trend exceeds random temporal noise (See US-2).

## Assumptions

- The UCI Electricity Load Diagrams dataset (https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014) contains sufficient features (load profiles of multiple zones) to generate a meaningful feature importance vector for the Random Forest model.
- The "concept drift" in the dataset is gradual enough to be captured by 30-day windows; extreme, instantaneous shifts may require window size adjustment (deferred to implementation).
- The Random Forest model's permutation importance calculation is stable enough across different random seeds to be considered a reliable proxy for feature relevance in this context.
- The GitHub Actions free-tier runner provides sufficient disk space to store the raw dataset and intermediate CSV outputs without compression.
- No GPU acceleration is available or required; all statistical tests and model training must rely on CPU-based `scikit-learn` and `scipy` implementations.
- The dataset metadata (if available) regarding known distribution shift events is not strictly required for the primary Mann-Kendall test but may be used for qualitative validation in the final report.
- The system execution must complete within 6 hours on the GitHub Actions free-tier runner; if it exceeds this, the workflow fails, but this is an environmental constraint, not a scientific validity failure.