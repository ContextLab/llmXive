# Feature Specification: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-20  
**Status**: Draft  
**Input**: User description: "Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Descriptor Engineering (Priority: P1)

The system must successfully ingest hydrogen diffusion data from the NIST Standard Reference Database and the *Journal of Materials Science*, calculate compositional descriptors (electronegativity, atomic radius variance) using Materials Project data, and derive microstructural proxies (free volume, grain boundary density) from processing parameters.

**Why this priority**: Without a clean, enriched dataset containing both the target variable (diffusion coefficient) and the full set of predictors, no modeling can occur. This is the foundational data pipeline.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a small, hardcoded subset of known NIST entries and verifying that the resulting dataframe contains exactly the required columns (e.g., `diffusion_coefficient`, `mean_electronegativity`, `atomic_radius_variance`, `free_volume_proxy`) with no missing values in the target column.

**Acceptance Scenarios**:

1. **Given** a raw dataset containing material composition and experimental diffusion coefficients, **When** the ingestion pipeline runs, **Then** the output dataframe contains at least 50% more columns than the input, including calculated descriptors like `valence_electron_concentration` and `atomic_radius_mismatch`.
2. **Given** an input row with missing microstructural parameters (e.g., `dislocation_density`), **When** the k-Nearest Neighbors imputation (k=5) runs, **Then** the missing value is replaced with a calculated estimate based on crystal structure similarity, and the row is not dropped.
3. **Given** a dataset with mixed units (e.g., cm²/s vs m²/s), **When** the normalization step runs, **Then** all diffusion coefficients are converted to a single standard unit (m²/s) before model training.

---

### User Story 2 - Non-Linear Model Training and Optimization (Priority: P2)

The system must train XGBoost and Random Forest regressors using k-fold cross-validation, optimize hyperparameters via Bayesian optimization within a 2-hour CPU budget, and compare performance against a linear regression baseline.

**Why this priority**: This is the core research engine. It determines whether non-linear interactions provide a measurable gain over traditional linear models, directly addressing the research question.

**Independent Test**: The training script can be tested by running it on a static, small subset of the data and verifying that the output log contains the best hyperparameters found, the cross-validation score for the non-linear model, and the baseline linear model score, all computed within the time limit.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** the Bayesian optimization loop completes, **Then** the system reports the `max_depth`, `learning_rate`, and `n_estimators` that yielded the lowest RMSE in 5-fold cross-validation.
2. **Given** the trained XGBoost and Random Forest models, **When** evaluated on a held-out [deferred] test set, **Then** the system outputs the $R^2$ and RMSE for both models and a linear baseline, explicitly stating which model performed best.
3. **Given** a 2-hour execution window, **When** the hyperparameter search exceeds the time budget, **Then** the system gracefully stops the search and reports the best model found *so far* rather than crashing or hanging.

---

### User Story 3 - Interaction Analysis and Robustness Validation (Priority: P3)

The system must utilize SHAP interaction values to quantify pairwise descriptor contributions (e.g., lattice distortion × defect density) and perform bootstrapping to generate confidence intervals for feature importance rankings.

**Why this priority**: This fulfills the specific research goal of identifying *which* non-linear interactions drive variance and ensures the findings are statistically robust, moving beyond simple point estimates.

**Independent Test**: The analysis script can be tested by running it on a fixed model and verifying that the output includes a ranked list of interaction terms with SHAP values and a plot or table showing the 95% confidence intervals for the top 5 feature importances derived from bootstrapping.

**Acceptance Scenarios**:

1. **Given** the best-performing non-linear model, **When** SHAP interaction analysis runs, **Then** the output identifies the top 3 pairwise interactions (e.g., `atomic_radius_variance` × `dislocation_density`) that contribute most to the variance in predicted diffusion coefficients.
2. **Given** the feature importance rankings, **When** 1,000 bootstrap iterations are performed, **Then** the system outputs a confidence interval (e.g., [0.15, 0.22]) for the importance score of the top-ranked descriptor.
3. **Given** a specific interaction term, **When** the sensitivity analysis runs, **Then** the system reports how the model's predictive performance changes if the interaction term is artificially zeroed out, confirming its necessity.

---

### Edge Cases

- **Dataset Variable Mismatch**: What happens if the NIST dataset lacks specific microstructural parameters (e.g., `free_volume`) for a significant portion of entries? The system must rely on the literature-derived proxy correlations or flag the sample as insufficient for that specific analysis.
- **Computational Out-of-Memory**: How does the system handle if the full NIST dataset + bootstrapping exceeds ~7 GB RAM? The system must implement chunked processing or data sampling to ensure the job completes on the free-tier runner.
- **Convergence Failure**: How does the system handle if Bayesian optimization fails to converge on a stable set of hyperparameters within the 2-hour limit? The system must fallback to a default grid search or the best result found at the timeout.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest data from NIST and *Journal of Materials Science* sources, calculating compositional descriptors (mean electronegativity, atomic radius variance) and deriving microstructural proxies (free volume, grain boundary density) using k-NN imputation (k=5) for missing values (See US-1).
- **FR-002**: System MUST train XGBoost and Random Forest regressors with 5-fold cross-validation and optimize hyperparameters via Bayesian optimization within a 2-hour CPU budget (See US-2).
- **FR-003**: System MUST compare the performance of non-linear models against a linear regression baseline using RMSE and $R^2$ on a held-out [deferred] test set (See US-2).
- **FR-004**: System MUST compute SHAP interaction values to quantify the contribution of pairwise descriptor interactions to the predicted diffusion coefficient (See US-3).
- **FR-005**: System MUST perform 1,000 bootstrap iterations to generate 95% confidence intervals for feature importance rankings and assess model stability (See US-3).
- **FR-006**: System MUST enforce a hard timeout of 6 hours for the entire CI job and gracefully exit with a partial result if exceeded (See Assumption: Compute Feasibility).

### Key Entities

- **MaterialSample**: Represents a single entry in the dataset, containing composition, crystal structure, processing history, and the target diffusion coefficient.
- **DescriptorSet**: A derived entity containing calculated features (electronegativity, atomic radius variance, valence electron concentration) and imputed microstructural proxies.
- **ModelPerformance**: A record containing RMSE, $R^2$, and hyperparameters for a specific model run (XGBoost, RF, or Linear).
- **InteractionTerm**: A derived entity representing a pairwise interaction (e.g., `distortion` × `defect_density`) with its associated SHAP value and significance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of variance in hydrogen diffusion coefficients explained by the non-linear model ($R^2$) is measured against the $R^2$ of the linear regression baseline to quantify the gain from non-linear interactions (See US-2).
- **SC-002**: The stability of feature importance rankings is measured against the width of the 95% confidence intervals derived from 1,000 bootstrap iterations (See US-3).
- **SC-003**: The contribution of specific pairwise interactions to the prediction variance is measured against the magnitude of their SHAP interaction values relative to the total variance (See US-3).
- **SC-004**: The computational feasibility is measured against the 6-hour CI job limit and ~7 GB RAM constraint, ensuring the full pipeline (ingestion, training, bootstrapping) completes without resource exhaustion (See FR-006).

## Assumptions

- **Dataset Availability**: It is assumed that the NIST Standard Reference Database and the *Journal of Materials Science* provide sufficient open-access data points (≥ 200 samples) with explicit microstructural parameters or processing history to allow for proxy derivation.
- **Proxy Validity**: It is assumed that literature-derived correlations for microstructural proxies (e.g., estimating free volume from grain size) are sufficiently accurate to serve as predictors in the absence of direct measurements.
- **Computational Constraints**: It is assumed that the entire analysis (including 1,000 bootstrap iterations) can be completed on a GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) within 6 hours by using sampled data subsets if the full dataset is too large.
- **Methodological Framing**: It is assumed that the study is observational; therefore, all findings regarding feature importance and interactions will be framed as associational rather than causal, as no randomization is applied.
- **Threshold Justification**: It is assumed that the selection of the [deferred] test split and k=5 for imputation follows standard community practices for this data size; a sensitivity analysis on the test split ratio (e.g., [deferred] vs [deferred]) will be recorded if the dataset size permits.
- **No GPU Requirement**: It is assumed that XGBoost and Random Forest implementations used are optimized for CPU execution and do not require CUDA or GPU acceleration.
