# Feature Specification: Predicting Plant Stress Response from Publicly Available Metabolomic Data and Environmental Factors

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Predicting Plant Stress Response from Publicly Available Metabolomic Data and Environmental Factors"

## User Scenarios & Testing

### User Story 1 - Data Integration and Preprocessing Pipeline (Priority: P1)

As a researcher, I want the system to automatically download, align, and clean plant metabolomics data with corresponding environmental variables (climate and soil) so that I have a unified, analysis-ready dataset without manual data wrangling.

**Why this priority**: Without a clean, integrated dataset, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output contains a merged DataFrame with non-null values for all required columns (metabolite concentrations, temperature, precipitation, soil pH, etc.) for at least 80% of the original samples.

**Acceptance Scenarios**:

1. **Given** a list of Metabolomics Workbench study IDs, **When** the pipeline runs, **Then** it successfully downloads the metabolomic data and merges it with WorldClim climate data and SoilGrids soil data based on latitude, longitude, and date.
2. **Given** samples with missing environmental values, **When** the imputation step runs, **Then** missing values are filled using k-nearest-neighbors (k=5) and the resulting dataset has no missing values in predictor columns.
3. **Given** raw metabolite concentration values, **When** preprocessing runs, **Then** all concentrations are log-transformed and all predictors are standardized (zero mean, unit variance).

---

### User Story 2 - Predictive Model Training and Evaluation (Priority: P2)

As a researcher, I want the system to train and evaluate multiple regression models (Random Forest, XGBoost, Elastic Net) to predict stress metabolite concentrations from environmental variables so that I can identify which model performs best and quantify the explained variance.

**Why this priority**: This delivers the core analytical value of the project—quantifying the relationship between environment and metabolites. It directly addresses the research question.

**Independent Test**: Can be fully tested by running the model training script and verifying that three distinct models are trained, hyperparameters are tuned on the validation set, and performance metrics (R², RMSE, MAE) are reported for each model on the held-out test set.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset split into training ([deferred]), validation ([deferred]), and test ([deferred]) sets, **When** model training runs, **Then** Random Forest, XGBoost (≤100 trees), and Elastic Net models are trained with hyperparameter optimization using Bayesian optimization (≤30 evaluations).
2. **Given** trained models, **When** evaluation runs on the test set, **Then** R², RMSE, and MAE are calculated for each metabolite and compared against a naïve baseline (training-set mean prediction).
3. **Given** multiple metabolite targets, **When** model selection runs, **Then** the best-performing model per metabolite is identified and its performance is recorded.

---

### User Story 3 - Feature Importance Analysis and Visualization (Priority: P3)

As a researcher, I want the system to compute and visualize feature importance scores with confidence intervals so that I can identify which environmental variables are the strongest predictors of stress metabolites.

**Why this priority**: This provides interpretability and actionable insights for breeding and management decisions, addressing the "which variables" part of the research question.

**Independent Test**: Can be fully tested by running the interpretability script and verifying that permutation-based feature importance scores are computed for the best model, 95% bootstrapped confidence intervals are generated (1,000 resamples), and partial dependence plots are created for the top three predictors.

**Acceptance Scenarios**:

1. **Given** the best-performing model for a metabolite, **When** interpretability analysis runs, **Then** permutation-based feature importance scores are calculated and 95% bootstrapped confidence intervals (1,000 resamples) are generated.
2. **Given** feature importance scores, **When** statistical testing runs, **Then** a two-sided test determines if each importance score differs significantly from zero (p < 0.05).
3. **Given** the top three environmental predictors, **When** visualization runs, **Then** partial dependence plots and correlation heatmaps are generated and saved as image files.

---

### Edge Cases

- What happens when a metabolomic sample has no corresponding climate/soil data within a reasonable distance (e.g., >100km)? The system should log the sample as excluded and proceed with the remaining valid samples.
- How does the system handle metabolites with near-zero variance across all samples? Such metabolites should be excluded from modeling to avoid numerical instability, with a warning logged.
- What if the Bayesian optimization fails to converge within 30 evaluations? The system should use the best model found so far and log a warning about limited convergence.
- How does the system handle extreme outliers in metabolite concentrations after log-transformation? Outliers beyond 3 standard deviations should be capped at the 1st/99th percentile to prevent skewing model training.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download metabolomic data from Metabolomics Workbench for specified study IDs and extract location/time metadata (See US-1).
- **FR-002**: System MUST retrieve climate variables (monthly temperature, precipitation) from WorldClim for each sample's coordinates and sampling date (See US-1).
- **FR-003**: System MUST obtain soil composition layers (pH, organic carbon, texture) from SoilGrids for each sample's coordinates (See US-1).
- **FR-004**: System MUST align metabolomic samples with environmental data using nearest-grid matching based on latitude, longitude, and date, excluding samples with no match within 100km (See US-1).
- **FR-005**: System MUST impute missing environmental values using k-nearest-neighbors with k=5 and log-transform metabolite concentrations before modeling (See US-1).
- **FR-006**: System MUST split the merged dataset into training ([deferred]), validation ([deferred]), and test ([deferred]) sets, stratified by stress type (drought, salinity, metal toxicity) (See US-2).
- **FR-007**: System MUST train Random Forest, XGBoost (≤100 trees), and Elastic Net models with hyperparameter tuning via Bayesian optimization (≤30 evaluations) on the validation set (See US-2).
- **FR-008**: System MUST evaluate all models on the held-out test set, reporting R², RMSE, and MAE for each metabolite and comparing against a naïve baseline (See US-2).
- **FR-009**: System MUST compute permutation-based feature importance for the best-performing model per metabolite and generate 95% bootstrapped confidence intervals (1,000 resamples) (See US-3).
- **FR-010**: System MUST perform two-sided statistical tests to determine if each feature importance score differs from zero (p < 0.05) and generate partial dependence plots for the top three predictors (See US-3).

### Key Entities

- **MetabolomicSample**: Represents a plant sample with measured stress metabolite concentrations, location coordinates, sampling date, and stress type classification.
- **EnvironmentalContext**: Aggregated environmental data (climate and soil) associated with a specific location and time period, including temperature, precipitation, pH, and soil texture.
- **PredictiveModel**: A trained regression model (Random Forest, XGBoost, or Elastic Net) with associated hyperparameters, performance metrics, and feature importance scores.
- **FeatureImportanceResult**: Statistical analysis output containing feature importance scores, confidence intervals, and significance test results for environmental predictors.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Out-of-sample R² for at least one metabolite class is measured against the naïve baseline (training-set mean prediction) to determine if environmental variables explain substantial variance (See US-2).
- **SC-002**: Feature importance scores with 95% bootstrapped confidence intervals are measured against zero to identify statistically robust environmental predictors (See US-3).
- **SC-003**: Model performance metrics (R², RMSE, MAE) are measured across all three regression algorithms to identify the best-performing approach for each metabolite (See US-2).
- **SC-004**: The proportion of samples successfully matched with environmental data is measured against the total number of metabolomic samples to assess data integration completeness (See US-1).
- **SC-005**: Partial dependence plots are measured for the top three environmental predictors per metabolite to visualize non-linear relationships and interaction effects (See US-3).

## Assumptions

- Publicly available metabolomic studies from Metabolomics Workbench contain sufficient location and time metadata to enable alignment with WorldClim and SoilGrids data.
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) can execute the entire analysis pipeline within the 6-hour time limit using CPU-only methods (no GPU required).
- WorldClim and SoilGrids data are accessible via their public APIs without authentication or rate-limiting issues that would block the pipeline.
- The metabolomic datasets include at least 50 samples per stress type (drought, salinity, metal toxicity) to enable meaningful stratified splitting and statistical testing.
- Log-transformation of metabolite concentrations effectively normalizes the distribution for regression modeling without introducing significant bias.
- The k-nearest-neighbors imputation (k=5) provides adequate accuracy for missing environmental values without distorting the underlying relationships.
- The 100km matching radius for environmental data alignment is sufficient to capture relevant environmental conditions for the plant samples without excessive data loss.
- The 30-evaluation limit for Bayesian optimization is adequate to find near-optimal hyperparameters for all three regression models.
- The 1,000 bootstrap resamples for confidence interval estimation provide stable and reliable uncertainty quantification for feature importance scores.
- The two-sided statistical test (p < 0.05) is appropriate for determining whether feature importance scores differ from zero in this observational study context.
