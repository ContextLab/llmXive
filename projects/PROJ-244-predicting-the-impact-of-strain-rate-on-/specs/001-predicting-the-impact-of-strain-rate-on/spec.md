# Feature Specification: Predicting the Impact of Strain Rate on the Yield Strength of Metals

**Feature Branch**: `001-predict-strain-rate-yield`  
**Created**: 2026-06-19  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Strain Rate on the Yield Strength of Metals"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher needs to ingest heterogeneous tensile test data from public repositories (NIST, OpenML) and supplemental composition tables (Materials Project), then preprocess this data into a unified, clean dataset ready for modeling. This includes unit standardization, missing value imputation, and feature engineering (e.g., elemental fraction vectors).

**Why this priority**: Without a clean, unified dataset, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: Can be fully tested by running the ingestion script against a mock dataset and verifying that the output CSV contains standardized units, imputed values for missing grain sizes (where primary predictors are present), and correctly encoded composition vectors.

**Acceptance Scenarios**:

1. **Given** raw CSV files from NIST containing yield strength and strain rate in mixed units, **When** the preprocessing pipeline is executed, **Then** all yield strength values are converted to MPa and all strain rates to s⁻¹.
2. **Given** records with missing grain size but known alloy composition (and present yield strength/strain rate), **When** k-nearest neighbors imputation is applied, **Then** the missing values are filled based on composition similarity without dropping the record.
3. **Given** raw JSON/XML files from OpenML, **When** the parser processes them, **Then** the output includes a standardized 10-dimensional elemental fraction vector for the most common elements.

---

### User Story 2 - Model Training and Baseline Comparison (Priority: P2)

The researcher needs to train multiple machine learning models (Random Forest, Gradient Boosting, Linear Regression, Ridge Regression) and compare their performance against established empirical constitutive models (Johnson-Cook, Zerilli-Armstrong) on a held-out test set. The system must automatically tune hyperparameters and calculate error metrics (R², MAE, RMSE).

**Why this priority**: This is the core research activity that directly addresses the research question regarding the predictive power of data-driven models versus empirical ones.

**Independent Test**: Can be fully tested by training models on a subset of the data and verifying that the output includes performance metrics for both ML and empirical models, with the ML models showing tunable hyperparameters.

**Acceptance Scenarios**:

1. **Given** a stratified training set (maintaining alloy family distribution), **When** the Random Forest model is trained with grid search, **Then** the best hyperparameters (max depth, number of trees) are selected based on validation set performance.
2. **Given** the same training data, **When** the Johnson-Cook empirical model is fitted, **Then** its parameters are optimized to minimize the sum of squared errors (SSE) on the training data, distinct from the ML loss function.
3. **Given** the independent test set, **When** predictions are generated for both ML and empirical models, **Then** R², MAE, and RMSE are calculated and reported for each model family.

---

### User Story 3 - Interpretability and Failure Regime Analysis (Priority: P3)

The researcher needs to interpret the best-performing model to understand feature importance (specifically strain rate sensitivity) and identify specific alloy families or strain rate regimes where empirical models fail. The system must generate partial dependence plots and statistical significance tests.

**Why this priority**: This provides the scientific insight required to answer "where do existing empirical constitutive models fail" and validates the mechanistic plausibility of the ML models.

**Independent Test**: Can be fully tested by generating partial dependence plots for a specific alloy family and verifying that the plot shows the expected non-linear relationship between strain rate and yield strength.

**Acceptance Scenarios**:

1. **Given** the trained Gradient Boosting model, **When** feature importance is extracted, **Then** strain rate, composition, and grain size must rank within the top 3 predictors by SHAP value, with the top feature having a SHAP value ≥ 0.1 or a permutation test p-value < 0.05.
2. **Given** predictions for high-strength steels at high strain rates, **When** the error distribution is compared between ML and Johnson-Cook models, **Then** a Wilcoxon signed-rank test confirms a statistically significant difference (p < 0.05).
3. **Given** a representative alloy family (e.g., AA-6061), **When** a partial dependence plot is generated, **Then** the curve must fit a non-linear model (e.g., cubic spline) with R² ≥ 0.8.

---

### Edge Cases

- What happens when a specific alloy family has fewer than 20 samples in the dataset? The system must flag this as a "low-sample regime" and exclude it from stratified splitting to prevent overfitting.
- How does the system handle missing strain rate data in the NIST repository? Records with missing strain rate must be dropped, as strain rate is the primary predictor variable.
- What if the Materials Project API returns no composition data for a specific alloy ID? The system must log a warning, impute the composition using the alloy family average, and then proceed with grain size imputation (if yield strength and strain rate are present).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest data from NIST Materials Data Repository and OpenML (specific dataset IDs to be resolved during implementation based on availability of yield strength/strain rate data), parsing CSV, JSON, and XML formats to extract yield strength, strain rate, temperature, and grain size (See US-1).
- **FR-002**: System MUST standardize all units to MPa for yield strength, s⁻¹ for strain rate, and µm for grain size before any modeling occurs (See US-1).
- **FR-003**: System MUST drop any record missing yield strength or strain rate. For records where yield strength and strain rate are present, the system MUST impute missing grain size values using k-nearest neighbors based on alloy composition. If alloy composition is missing, the system MUST first impute composition using the alloy family average before applying KNN for grain size (See US-1).
- **FR-004**: System MUST train Random Forest, Gradient Boosting, Linear Regression, and Ridge Regression regressors with hyperparameter tuning via grid search on a validation set (See US-2).
- **FR-005**: System MUST fit Johnson-Cook and Zerilli-Armstrong empirical models on the same training data to enable direct performance comparison (See US-2).
- **FR-006**: System MUST generate partial dependence plots for yield strength vs. strain rate for at least three representative alloy families (See US-3).
- **FR-007**: System MUST perform Wilcoxon signed-rank tests to compare error distributions between ML models and empirical models (See US-3).
- **FR-008**: System MUST perform a sensitivity analysis comparing models trained on raw vs. imputed grain size to quantify potential bias introduced by imputation (See US-1).

### Key Entities

- **TensileTestRecord**: Represents a single experimental measurement containing yield strength, strain rate, temperature, grain size, and alloy composition.
- **AlloyFamily**: A categorical grouping of metals (e.g., "AA-6061", "AISI-4340") used for stratification and analysis.
- **ConstitutiveModel**: An empirical mathematical model (e.g., Johnson-Cook) defined by a set of fitted parameters.
- **MLModel**: A data-driven model (e.g., Random Forest) defined by its structure and trained weights.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive accuracy (R²) of ML models is measured against the R² of empirical constitutive models (Johnson-Cook, Zerilli-Armstrong) on the held-out test set (See US-2).
- **SC-002**: Feature importance rankings are measured against domain literature expectations regarding the influence of strain rate, composition, and grain size (See US-3).
- **SC-003**: Statistical significance of performance differences is measured via Wilcoxon signed-rank test p-values comparing error distributions of ML vs. empirical models across alloy families (See US-3).
- **SC-004**: Model robustness is measured by the stability of performance metrics across different random seeds for data splitting (See US-2).
- **SC-005**: The bias introduced by grain size imputation is measured by the difference in R² between models trained on raw data and models trained on imputed data (See US-1).

## Assumptions

- The NIST Materials Data Repository and OpenML contain sufficient records (≥ 500 total) with both yield strength and strain rate measurements to train a robust model.
- The Materials Project API provides elemental composition data for the majority of alloys in the NIST dataset; missing data will be imputed using family averages.
- The analysis will be performed on a CPU-only environment (GitHub Actions free tier), limiting the dataset size to ≤ 100,000 records and avoiding GPU-intensive deep learning methods.
- The Johnson-Cook and Zerilli-Armstrong models can be fitted using standard optimization libraries (e.g., `scipy.optimize`) without requiring specialized hardware.
- The relationship between strain rate and yield strength is hypothesized to be monotonic and non-linear, but the system MUST detect and report any non-monotonic regimes observed in the data (See US-3).