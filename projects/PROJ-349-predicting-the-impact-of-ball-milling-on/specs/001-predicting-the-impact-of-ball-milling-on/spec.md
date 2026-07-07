# Feature Specification: Predicting the Impact of Ball Milling on Particle Size Distribution

**Feature Branch**: `001-predict-balling-milling-psd`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Ball Milling on Particle Size Distribution"

## User Scenarios & Testing

### US-1 - Data Aggregation and Preprocessing Pipeline (Priority: P1)

As a materials scientist, I want to automatically aggregate ball milling experimental data from public repositories (Materials Project, NIST, arXiv) and preprocess it to include standardized features (milling speed, time, ball-to-powder ratio, Young's modulus, density, and other material properties) so that I have a clean, analysis-ready dataset of at least 500 experiments (target) or 150 experiments (minimum viable).

**Why this priority**: Without a curated dataset, no modeling can occur. This is the foundational step that enables all subsequent analysis.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output CSV contains ≥500 rows (target) or ≥150 rows (minimum viable) with non-null values for all required predictor variables and target PSD metrics. If the dataset is <150, the system MUST log a critical warning and halt with a specific error code indicating insufficient data for statistical power.

**Acceptance Scenarios**:

1. **Given** a list of public data sources (Materials Project, NIST, arXiv), **When** the ingestion script runs, **Then** the system attempts to download and parse experiments from all three sources, aggregating at least 500 unique milling experiments with reported PSD data if available, or a minimum of 150 if data is scarce.
2. **Given** raw data with missing values, **When** the preprocessing module runs, **Then** missing values are handled via multiple imputation and the dataset is normalized.
3. **Given** categorical material types, **When** encoding is applied, **Then** all categorical variables are converted to numerical representations without data loss.
4. **Given** unstructured PSD data (e.g., images, raw curves), **When** the ingestion script encounters it, **Then** the system flags these entries for manual curation or applies a configured OCR/extraction fallback, logging the count of flagged entries.

---

### US-2 - Predictive Model Training and Validation (Priority: P2)

As a process engineer, I want to train and validate machine learning models (Gaussian Process Regression and Random Forest) on the aggregated dataset so that I can evaluate their ability to predict particle size distribution outcomes with a Primary Success Threshold of R² > 0.6 and a Secondary Success Threshold of R² > 0.3.

**Why this priority**: This delivers the core predictive capability; without a trained model, the project cannot achieve its research goal. The secondary threshold ensures the project yields valid scientific findings even if the primary hypothesis (R² > 0.6) is not met.

**Independent Test**: Can be fully tested by running the training pipeline on a subset of the data and verifying that the cross-validation scores are computed, the computational fallback triggers if limits are exceeded, and the statistical power is reported.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** the training pipeline executes, **Then** both GPR and Random Forest models are trained using k-fold cross-validation. If GPR exceeds a predefined computational threshold for time or memory, the system MUST automatically switch to Random Forest only. and log the fallback event.
2. **Given** a held-out test set ([deferred] of data), **When** the models make predictions, **Then** the R², RMSE, and MAE metrics are computed and reported.
3. **Given** a linear regression baseline, **When** paired t-tests are performed, **Then** the system determines if ML models significantly outperform the baseline at α = 0.05, AND reports the statistical power of the test.
4. **Given** a dataset size < 150, **When** the training pipeline attempts to run, **Then** the system MUST halt and report that the dataset size is below the minimum viable threshold for power analysis.

---

### US-3 - Model Interpretability and Visualization (Priority: P3)

As a researcher, I want to generate partial dependence plots and export feature importance rankings so that I can interpret how milling parameters influence particle size distribution and identify the most critical process variables.

**Why this priority**: Interpretability ensures the model provides actionable insights rather than just predictions, supporting process optimization decisions.

**Independent Test**: Can be fully tested by running the visualization script and verifying that PNG plots are generated showing PSD response to individual parameters.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** partial dependence analysis is performed, **Then** plots are generated showing the relationship between each milling parameter (speed, time, ratio) and PSD metrics.
2. **Given** a Random Forest model, **When** feature importance is calculated, **Then** a JSON file is exported containing ranked features and their importance scores.
3. **Given** the visualization outputs, **When** the files are saved, **Then** the total size of all generated plots is ≤10MB.

---

### Edge Cases

- What happens when the public data sources return fewer than 500 experiments? (System must log a warning, proceed if ≥150, and halt with error if <150.)
- How does the system handle missing Young's modulus values for novel materials not in the Materials Project? (System must use imputation or flag for manual review.)
- What happens if a dataset contains duplicate experiments with conflicting PSD measurements? (System must deduplicate based on unique experiment identifiers or average conflicting values with a documented rule.)
- What happens if GPR training exceeds a moderate duration or memory threshold.? (System MUST automatically switch to Random Forest only and log the fallback event.)

## Requirements

### Functional Requirements

- **FR-001**: System MUST aggregate ball milling experimental data from up to three public sources (Materials Project, NIST, arXiv), attempting all three but allowing success with fewer if data is unavailable, to create a unified dataset. (See US-1)
- **FR-002**: System MUST preprocess the aggregated data by handling missing values via multiple imputation, normalizing numerical features, and encoding categorical material types. (See US-1)
- **FR-003**: System MUST train both Gaussian Process Regression and Random Forest models using k-fold cross-validation on the preprocessed dataset. (See US-2)
- **FR-004**: System MUST evaluate model performance using R², RMSE, and MAE metrics on a held-out test set comprising [deferred] of the data. (See US-2)
- **FR-005**: System MUST generate partial dependence plots and export feature importance rankings in JSON format for model interpretability. (See US-3)
- **FR-006**: System MUST perform a paired t-test to determine if ML models significantly outperform a linear regression baseline at α = 0.05, and report the statistical power of the test. (See US-2)
- **FR-007**: System MUST perform a power analysis on the dataset size to determine the minimum detectable effect size and report this alongside the t-test results. (See US-2)
- **FR-008**: System MUST detect and flag unstructured PSD data (e.g., images, raw curves) for manual curation or apply a configured extraction fallback, logging the count of flagged entries. (See US-1)
- **FR-009**: System MUST implement a computational fallback strategy: if GPR training exceeds a predefined time or memory threshold, automatically switch to Random Forest only and log the event. (See US-2)
- **FR-010**: System MUST include 'Process Duration' as a predictor feature to proxy for material evolution effects during milling. (See US-2)

### Key Entities

- **Experiment**: Represents a single ball milling trial with attributes: milling speed (RPM), milling time (hours), ball-to-powder ratio, material type, **pre-milling** Young's modulus, **pre-milling** density, and PSD metrics (D10, D50, D90). *Note: Material properties are pre-milling estimates; the model does not account for dynamic evolution during milling.*
- **Model**: Represents a trained predictive model (GPR or Random Forest) with attributes: hyperparameters, cross-validation scores, feature importance rankings, and performance metrics.

### Glossary

- **Experiment**: A single ball milling trial (see Key Entities).
- **PSD**: Particle Size Distribution, typically reported as D10, D50, D90 percentiles.
- **US-1, US-2, US-3**: Unique identifiers for User Stories 1, 2, and 3 respectively.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive model accuracy (R²) is measured against the linear regression baseline using k-fold cross-validation scores. **Primary Success**: R² > 0.6; **Secondary Success**: R² > 0.3. (See US-2)
- **SC-002**: Model performance metrics (RMSE, MAE) are measured against a [deferred] held-out test set to assess generalization. (See US-2)
- **SC-003**: Statistical significance of ML model superiority is measured against the linear regression baseline via paired t-test at α = 0.05, with the statistical power of the test reported. (See US-2)
- **SC-004**: Dataset completeness is measured against the target of ≥500 unique milling experiments (with all required predictor and outcome variables) OR a minimum viable dataset of ≥150 experiments. (See US-1)
- **SC-005**: Computational feasibility is measured against the -hour GitHub Actions job limit, ensuring all training and evaluation tasks complete within this timeframe, or a documented fallback to Random Forest is triggered. (See US-2)

## Assumptions

- Public repositories (Materials Project, NIST, arXiv) contain at least 150 documented ball milling experiments with standardized reporting of milling parameters and PSD outcomes; a target sample size sufficient for full statistical power is desired.
- Young's modulus values for all materials in the dataset are available via the Materials Project API or can be reliably imputed from similar materials. *Note: These are pre-milling estimates.*
- The relationship between milling parameters and PSD is sufficiently captured by the selected features (speed, time, ball-to-powder ratio, Young's modulus, density, process duration) without requiring additional unmeasured variables (e.g., temperature, milling atmosphere), though the model acknowledges the limitation of using static properties for dynamic processes.
- The GitHub Actions free-tier runner (a limited number of CPU cores, ~7 GB RAM) is sufficient to train Random Forest models with ≤1000 trees and Gaussian Process Regression on the aggregated dataset, provided the computational fallback (FR-009) is in place.
- The dataset size (≤500 experiments) and model complexity are small enough to avoid GPU acceleration, allowing all computations to run on CPU-only infrastructure.
- The observational nature of the data (no random assignment of milling parameters) means all findings will be framed as associational rather than causal.
- Unstructured PSD data (images, curves) may exist in the source repositories and will require manual curation or extraction fallbacks as defined in FR-008.