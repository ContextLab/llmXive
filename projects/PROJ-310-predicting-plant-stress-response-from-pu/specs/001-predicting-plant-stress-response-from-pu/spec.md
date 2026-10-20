# Feature Specification: Predicting Plant Stress Response from Publicly Available Metabolomic Data and Environmental Factors

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Predicting Plant Stress Response from Publicly Available Metabolomic Data and Environmental Factors"

## User Scenarios & Testing

### User Story 1 - Data Integration and Preprocessing Pipeline (Priority: P1) (US-1)

As a researcher, I want the system to automatically download, align, and clean plant metabolomics data with corresponding environmental variables (climate and soil) so that I have a unified, analysis-ready dataset without manual data wrangling.

**Why this priority**: Without a clean, integrated dataset, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output contains a merged DataFrame with non-null values for all required columns (metabolite concentrations, temperature, precipitation, soil pH, etc.) for at least 80% of the original samples.

**Acceptance Scenarios**:

1. **Given** a list of Metabolomics Workbench study IDs, **When** the pipeline runs, **Then** it successfully downloads the metabolomic data and merges it with ERA5 historical climate data and SoilGrids soil data based on latitude, longitude, and sampling date.
2. **Given** samples with missing environmental values, **When** the imputation step runs, **Then** missing values are filled using k‑nearest‑neighbors (k=5) and the resulting dataset has no missing values in predictor columns.
3. **Given** raw metabolite concentration values, **When** preprocessing runs, **Then** all concentrations are log‑transformed, extreme outliers beyond 3 standard deviations are capped at the 1st/99th percentile, predictors are standardized to zero mean and unit variance, and the resulting dataset contains no missing values.

---

### User Story 2 - Predictive Model Training and Evaluation (Priority: P2) (US-2)

As a researcher, I want the system to train and evaluate multiple regression models (Random Forest, XGBoost, Elastic Net) to predict stress metabolite concentrations from environmental variables so that I can identify which model performs best and quantify the explained variance.

**Why this priority**: This delivers the core analytical value of the project—quantifying the relationship between environment and metabolites. It directly addresses the research question.

**Independent Test**: Can be fully tested by running the model training script and verifying that three distinct models are trained, hyperparameters are tuned on the validation set, and performance metrics (R², RMSE, MAE) are reported for each model on the held‑out test set.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset split into training ([deferred] of samples), validation ([deferred] of samples), and test ([deferred] of samples) sets, stratified by stress type and grouped by study ID to avoid leakage, **When** model training runs, **Then** Random Forest, XGBoost (≤100 trees), and Elastic Net models are trained; Random Forest and XGBoost hyperparameters are optimized via Bayesian optimization (≤30 evaluations) and Elastic Net α is tuned via grid search over {0.001,0.01,0.1,1,10}.
2. **Given** trained models, **When** evaluation runs on the test set, **Then** R², RMSE, and MAE are calculated for each metabolite **and for each stress category (drought, salinity, metal toxicity)** and compared against a naïve baseline (training‑set mean prediction).
3. **Given** multiple metabolite targets, **When** model selection runs, **Then** the best‑performing model per metabolite and per stress category is identified and its performance is recorded.

---

### User Story 3 - Feature Importance Analysis and Visualization (Priority: P3) (US-3)

As a researcher, I want the system to compute and visualize feature importance scores with confidence intervals so that I can identify which environmental variables are the strongest predictors of stress metabolites.

**Why this priority**: This provides interpretability and actionable insights for breeding and management decisions, addressing the "which variables" part of the research question.

**Independent Test**: Can be fully tested by running the interpretability script and verifying that permutation‑based feature importance scores are computed for the best model, 95 % bootstrapped confidence intervals are generated (1,000 resamples), and partial dependence plots are created for the top three predictors.

**Acceptance Scenarios**:

1. **Given** the best‑performing model for a metabolite, **When** interpretability analysis runs, **Then** permutation‑based feature importance scores are calculated and 95 % bootstrapped confidence intervals (1,000 resamples) are generated.
2. **Given** feature importance scores, **When** statistical testing runs, **Then** a one‑sided test determines if each importance score is significantly greater than zero (bootstrap CI does not include zero, p < 0.05).
3. **Given** the top three environmental predictors, **When** visualization runs, **Then** partial dependence plots and correlation heatmaps are generated and saved as image files.

---

### Edge Cases

- What happens when a metabolomic sample has no corresponding climate/soil data within a reasonable distance (e.g., >100 km)? The system logs the sample as excluded and proceeds with the remaining valid samples.
- How does the system handle metabolites with near‑zero variance across all samples? Such metabolites are excluded from modeling (see FR‑012).
- How does the system handle extreme outliers in metabolite concentrations after log‑transformation? Outliers beyond 3 SD are capped at the 1st/99th percentile (see FR‑013).
- What if the Bayesian optimization fails to converge within 30 evaluations? The system uses the best model found so far and logs a warning about limited convergence.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download metabolomic data from Metabolomics Workbench for specified study IDs and extract location/time metadata (See US-1).
- **FR-002**: System MUST retrieve historical climate variables (e.g., temperature, precipitation) from the ERA5 reanalysis product for each sample's coordinates and sampling date (See US-1).
- **FR-003**: System MUST obtain soil composition layers (pH, organic carbon, texture) from SoilGrids for each sample's coordinates (See US-1).
- **FR-004**: System MUST align metabolomic samples with environmental data using nearest‑grid matching based on latitude, longitude, and date, excluding samples with no match within 100 km, **and** persist the exact grid coordinates and temporal offsets used for each sample in a provenance file (See US-1).
- **FR-005**: System MUST impute missing environmental values using k‑nearest‑neighbors with k=5, log‑transform metabolite concentrations, cap extreme outliers beyond 3 SD at the 1st/99th percentile, and standardize all predictor variables to zero mean and unit variance (See US-1).
- **FR-006**: System MUST split the merged dataset into training ([deferred] of samples), validation ([deferred] of samples), and test ([deferred] of samples) sets, stratified by stress type (drought, salinity, metal toxicity) and grouped by study ID to avoid leakage (See US-2).
- **FR-007**: System MUST train Random Forest, XGBoost (≤100 trees), and Elastic Net models; Random Forest and XGBoost hyperparameters are tuned via Bayesian optimization (≤30 evaluations) on the validation set, while Elastic Net α is tuned via grid search over {0.001,0.01,0.1,1,10} (See US-2).
- **FR-008**: System MUST evaluate all models on the held‑out test set, reporting R², RMSE, and MAE **for each metabolite and for each stress category (drought, salinity, metal toxicity)**, and compare these metrics against a naïve baseline (See US-2).
- **FR-009**: System MUST compute permutation‑based feature importance for the best‑performing model per metabolite and generate 95 % bootstrapped confidence intervals (1,000 resamples) (See US-3).
- **FR-010**: System MUST perform a one‑sided statistical test (null: importance ≤ 0) to determine if each feature importance score differs significantly from zero (p < 0.05) and generate partial dependence plots for the top three predictors (See US-3).
- **FR-011**: System MUST generate evaluation tables that separately list R², RMSE, and MAE for each stress type (drought, salinity, metal toxicity) and each metabolite (See US-2). *(Ensures compliance with Constitution Principle VII)*
- **FR-012**: System MUST exclude metabolites whose variance across all samples is below 1 × 10⁻⁶ before modeling (See US-1).
- **FR-013**: System MUST cap extreme metabolite outliers (post‑log‑transformation) at the 1st and 99th percentile values to limit influence on model training (See US-1).
- **FR-014**: System MUST record provenance metadata linking each metabolomic sample to the exact environmental grid cell and temporal offset used for alignment (See US-1). *(Implemented via FR‑004 extension)*
- **FR-015**: System MUST control for species, study ID, and organ/tissue effects either by including them as covariates in the models or by restricting analyses to within‑species subsets (See US-2).
- **FR-016**: System MUST use GroupKFold cross‑validation grouped by study ID when creating training/validation/test splits to prevent information leakage (See US-2).
- **FR-017**: System MUST apply Bayesian optimization with ≤30 evaluations for Random Forest and XGBoost hyperparameters (See US-2). *(Clarifies optimization budget)*
- **FR-018**: System MUST tune Elastic Net α via grid search over the set {0.001, 0.01, 0.1, 1, 10} (See US-2).
- **FR-019**: System MUST report permutation importance confidence intervals and declare a predictor significant only if the lower bound of the 95 % CI exceeds zero (See US-3).

### Key Entities

- **MetabolomicSample**: Represents a plant sample with measured stress metabolite concentrations, location coordinates, sampling date, and stress type classification.
- **EnvironmentalContext**: Aggregated environmental data (climate and soil) associated with a specific location and time period, including temperature, precipitation, pH, and soil texture.
- **PredictiveModel**: A trained regression model (Random Forest, XGBoost, or Elastic Net) with associated hyperparameters, performance metrics, and feature importance scores.
- **FeatureImportanceResult**: Statistical analysis output containing feature importance scores, confidence intervals, and significance test results for environmental predictors.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Out‑of‑sample R² for each stress category must be **≥ 0.60** *and* at least **0.05** higher than the naïve baseline R² (training‑set mean prediction) to be considered a successful demonstration of explanatory power (See US-2).
- **SC-002**: Feature importance scores with 95 % bootstrapped confidence intervals are measured against zero; a predictor is deemed robust if the lower bound of its CI exceeds zero (See US-3).
- **SC-003**: Model performance metrics (R², RMSE, MAE) are measured **per metabolite and per stress category** across all three regression algorithms to identify the best‑performing approach for each combination (See US-2).
- **SC-004**: The proportion of samples successfully matched with environmental data is measured against the total number of metabolomic samples to assess data integration completeness (See US-1).
- **SC-005**: Partial dependence plots are produced for the top three environmental predictors per metabolite to visualize non‑linear relationships and interaction effects (See US-3).

## Assumptions

- Publicly available metabolomic studies from Metabolomics Workbench contain sufficient location and time metadata to enable alignment with ERA5 and SoilGrids data.
- The GitHub Actions free‑tier runner (a modest number of CPU cores, ~7 GB RAM) can execute the entire analysis pipeline within the 6‑hour time limit. using CPU‑only methods (no GPU required).
- WorldClim and SoilGrids data are accessible via their public APIs without authentication or rate‑limiting issues that would block the pipeline.
- The metabolomic datasets include at least 50 samples per stress type (drought, salinity, metal toxicity) to enable meaningful stratified splitting and statistical testing.
- Log‑transformation of metabolite concentrations effectively normalizes the distribution for regression modeling without introducing significant bias.
- The k‑nearest‑neighbors imputation (k=5) provides adequate accuracy for missing environmental values without distorting the underlying relationships.
- The 100 km matching radius for environmental data alignment is sufficient to capture relevant environmental conditions for the plant samples without excessive data loss.
- The 30‑evaluation limit for Bayesian optimization is adequate to find near‑optimal hyperparameters for Random Forest and XGBoost; Elastic Net α is exhaustively explored via grid search.
- The 1,000 bootstrap resamples for confidence interval estimation provide stable and reliable uncertainty quantification for feature importance scores.
- The two‑sided statistical test has been replaced by a one‑sided test appropriate for non‑negative permutation importance values.
- Controlling for species, study ID, and organ/tissue effects (FR‑015) mitigates major confounding sources inherent in public metabolomics repositories.
- GroupKFold splitting (FR‑016) prevents leakage between training and test sets.
- The 70/15/15 split ratios (FR‑006) reflect the original idea’s design parameters and are justified to provide sufficient data for training, validation, and testing.