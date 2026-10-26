# Feature Specification: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

**Feature Branch**: `001-hydrogen-diffusion-prediction`  
**Created**: 2026-07-20  
**Status**: Draft  
**Input**: User description: "Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Descriptor Engineering (Priority: P1)

The system must successfully ingest hydrogen diffusion data from the open‑access NIST Standard Reference Database (download URL:) and the *Journal of Materials Science* dataset (DOI:), calculate compositional descriptors (electronegativity, atomic radius variance) using Materials Project API data, and derive microstructural proxies (`free_volume_proxy`, `grain_boundary_density`) from processing parameters. All numerical features, including temperature, are normalized with a StandardScaler, and missing microstructural values are imputed with k‑Nearest Neighbors (k=5) using only predictor columns. As a fallback for reproducible testing, a curated CSV file containing a substantial set of verified entries is provided at `data/raw/hydrogen_diffusion.csv`.

**Why this priority**: Without a clean, enriched dataset containing both the target variable (diffusion coefficient) and the full set of predictors, no modeling can occur. This is the foundational data pipeline.

**Independent Test**: The pipeline can be fully tested by running the ingestion script on the provided `hydrogen_diffusion.csv` subset and verifying that the resulting dataframe contains the required columns (`diffusion_coefficient`, `mean_electronegativity`, `atomic_radius_variance`, `free_volume_proxy`, `grain_boundary_density`, `temperature`, `inverse_temperature`) with no missing values in the target column and ≥ 95 % non‑null entries for each descriptor column.

**Acceptance Scenarios**:

1. **Given** a raw dataset containing material composition, processing history, measurement temperature, and experimental diffusion coefficients, **When** the ingestion pipeline runs, **Then** the output dataframe contains all required descriptor columns listed above and each descriptor column has at least 95 % non‑null entries.
2. **Given** an input row with missing microstructural parameters (e.g., `grain_boundary_density`), **When** the k‑NN imputation (k=5) runs, **Then** the missing value is replaced with a calculated estimate based on crystal‑structure similarity, and the row is retained.
3. **Given** a dataset with mixed units (e.g., cm²/s vs m²/s), **When** the normalization step runs, **Then** all diffusion coefficients are converted to a single standard unit (m²/s) before model training.

### User Story 2 - Non-Linear Model Training and Optimization (Priority: P2)

The system must train XGBoost and Random Forest regressors using nested cross‑validation: an outer 5‑fold CV for unbiased performance estimation and an inner Bayesian‑optimization loop (max 2 h CPU budget) for hyper‑parameter tuning. All preprocessing (imputation, scaling) is fitted inside each inner training fold. Models are trained on the **log₁₀‑transformed** diffusion coefficient, a standard practice for Arrhenius‑type diffusion data (see justification in FR‑002).

**Why this priority**: This is the core research engine. It determines whether non‑linear interactions provide a measurable gain over traditional linear models, directly addressing the research question.

**Independent Test**: The training script can be tested by running it on a static, small subset of the data and verifying that the output log contains the best hyperparameters found, the outer‑fold CV score for the non‑linear model, and the baseline linear model score, all computed within the time limit and on the log‑scale target.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** the Bayesian optimization loop completes within the 2‑hour budget, **Then** the system reports the `max_depth`, `learning_rate`, and `n_estimators` that yielded the lowest RMSE (on log₁₀(D)) in the inner CV.
2. **Given** the trained XGBoost and Random Forest models, **When** evaluated on the held‑out outer‑fold test sets, **Then** the system outputs the $R^{2}$ and RMSE (both on log₁₀(D)) for both models and a linear baseline, explicitly stating which model performed best.
3. **Given** a 2‑hour execution window, **When** the hyperparameter search exceeds the time budget, **Then** the search loop terminates early, logs “Optimization terminated due to time budget”, records the best hyperparameters and CV score found so far, and exits with code 0.

### User Story 3 - Interaction Analysis and Robustness Validation (Priority: P3)

The system must utilize SHAP interaction values to quantify pairwise descriptor contributions (e.g., lattice distortion × defect density) and perform bootstrap resampling with a sufficient number of iterations, where the full model pipeline is refit on each resample to generate confidence intervals for feature‑importance rankings and for ablation‑based interaction impact.

**Why this priority**: This fulfills the specific research goal of identifying *which* non‑linear interactions drive variance and ensures the findings are statistically robust, moving beyond simple point estimates.

**Independent Test**: The analysis script can be tested by running it on a fixed model and verifying that the output includes a ranked list of interaction terms with SHAP values, a table showing the 95 % confidence intervals for the top feature importances derived from bootstrapped refits, and an ablation report showing the change in outer‑fold $R^{2}$ when each top interaction is zeroed.

**Acceptance Scenarios**:

1. **Given** the best‑performing non-linear model, **When** SHAP interaction analysis runs, **Then** the output identifies the most influential pairwise interactions (e.g., `atomic_radius_variance` × `dislocation_density`) that contribute most to the variance in predicted diffusion coefficients.
2. **Given** the feature‑importance rankings, **When** multiple bootstrap iterations with full model refit are performed, **Then** the system outputs a confidence interval for the importance score of the top‑ranked descriptor.
3. **Given** a specific interaction term, **When** the sensitivity/ablation analysis runs, **Then** the system reports the decrease in outer‑fold $R^{2}$ (Δ$R^{2}$) relative to the full model, confirming its necessity.

### Edge Cases

- **Dataset Variable Mismatch**: If the NIST dataset lacks specific microstructural parameters (e.g., `free_volume_proxy`) for a significant portion of entries, the system relies on literature‑derived proxy correlations independent of diffusion measurements, or flags the sample set as insufficient for interaction analysis.
- **Computational Out‑of‑Memory**: If the full NIST dataset + bootstrapping exceeds available memory, the pipeline processes the data in chunks (no hard RAM ceiling is enforced; this is an implementation detail, not a specification requirement).
- **Convergence Failure**: If Bayesian optimization fails to converge on a stable set of hyperparameters within the 2‑hour limit, the system falls back to a default grid search (max_depth = 6, learning_rate = 0.1, n_estimators = 200) and reports the result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest data from the open‑access NIST Standard Reference Database () and the *Journal of Materials Science* dataset (), or from the provided `data/raw/hydrogen_diffusion.csv` file containing ≥ 200 verified samples, calculate compositional descriptors (mean electronegativity, atomic radius variance) and derive microstructural proxies (`free_volume_proxy`, `grain_boundary_density`) using k‑NN imputation (k=5) **trained only on predictor columns**, then normalize **all numerical features (including temperature) with StandardScaler** (See US-1).
- **FR-002**: System MUST train XGBoost and Random Forest regressors with **nested 5‑fold outer cross‑validation** and **inner Bayesian optimization** (≤ 2 h CPU budget) **inside each outer training fold**, fitting imputation and scaling **inside the inner folds only**, and train models on the **log₁₀‑transformed diffusion coefficient** (a standard transformation for Arrhenius‑type diffusion data) (See US-2).
- **FR-003**: System MUST compare the performance of non‑linear models against a linear regression baseline using **RMSE and $R^{2}$ computed on log₁₀(D)** on the outer‑fold held‑out test sets (See US-2).
- **FR-004**: System MUST compute SHAP interaction values to quantify the contribution of pairwise descriptor interactions to the model’s predictions (See US-3).
- **FR-005**: System MUST perform 1,000 bootstrap iterations **refitting the full model pipeline on each resample** to generate 95 % confidence intervals for feature‑importance rankings and to assess interaction‑ablation impact Δ$R^{2}$ (See US-3).
- **FR-007**: System MUST ensure **descriptor‑target provenance independence**: the target diffusion coefficient must never be used as a predictor or in the imputation/scaling steps, and each literature‑derived proxy correlation must be documented as independent of diffusion measurements (See US-1; Constitution Principle VII).
- **FR-008**: System MUST record the measurement **temperature** for each sample **and** compute its inverse (1/T) as a predictor; the linear baseline model must use 1/T while non‑linear models may use both raw temperature and 1/T (See US-1).
- **FR-009**: System MUST conduct an a‑priori power analysis targeting detection of interaction effect sizes of at least *f*² = 0.15 with power ≥ 0.80 and α = 0.05, confirming that a sample size of **≥ 200** satisfies the requirement that bootstrap‑derived 95 % confidence‑interval widths for feature‑importance scores are ≤ 0.1 (Justified as essential to reliably detect the interaction effects of scientific interest; based on Cohen 1988 and Efron & Tibshirani 1993). (See US-3)
- **FR-010**: System MUST compute, on an **independent external hold‑out test set** sourced from the DOE Materials Data Repository () and never used in training, the **proportion of total $R^{2}$ attributable to pairwise interaction terms** by summing only the off‑diagonal SHAP interaction contributions and dividing by the model’s overall $R^{2}$; the proportion must be **≥ 70 %** (See US-3; aligns with Constitution Principle VII).

### Key Entities

- **MaterialSample**: Represents a single entry in the dataset, containing composition, crystal structure, processing history, measurement temperature, inverse temperature, and the target diffusion coefficient.
- **DescriptorSet**: A derived entity containing calculated features (mean electronegativity, atomic radius variance, free_volume_proxy, grain_boundary_density, temperature, inverse_temperature) and imputed microstructural proxies.
- **ModelPerformance**: A record containing RMSE, $R^{2}$, and hyperparameters for a specific model run (XGBoost, RF, or Linear) on log₁₀(D).
- **InteractionTerm**: A derived entity representing a pairwise interaction (e.g., `distortion` × `defect_density`) with its associated SHAP interaction value, confidence interval, and ablation impact Δ$R^{2}$.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of variance in log₁₀(diffusion coefficient) explained by the non‑linear model ($R^{2}$) is measured against the $R^{2}$ of the linear regression baseline to quantify the gain from non‑linear interactions (See US-2).
- **SC-002**: The stability of feature‑importance rankings is measured by the width of the 95 % confidence intervals derived from 1,000 bootstrap‑refit iterations (See US-3).
- **SC-003**: The contribution of specific pairwise interactions to prediction performance is measured by the decrease in outer‑fold $R^{2}$ (Δ$R^{2}$) when the interaction term is ablated, compared to its SHAP interaction magnitude (See US-3).
- **SC-005**: Data pipeline completeness is measured by the **percentage of required descriptor columns that are non‑null** (target ≥ 95 %) and by confirming that all required columns are present (See US-1).
- **SC-006**: The proportion of total $R^{2}$ attributable to pairwise interaction terms, evaluated on the independent external hold‑out set, must be **≥ 70 %** (See US-3; satisfies Constitution Principle VII).

## Assumptions

- **Dataset Availability**: It is assumed that the NIST Standard Reference Database and the *Journal of Materials Science* provide sufficient open‑access data points (≥ 200 samples) with explicit microstructural parameters or processing history to allow for proxy derivation; the fallback CSV file `data/raw/hydrogen_diffusion.csv` guarantees availability for testing.
- **Proxy Validity**: It is assumed that literature‑derived correlations for microstructural proxies (e.g., estimating free_volume_proxy from grain size) are **independent of diffusion‑coefficient measurements** and are sufficiently accurate to serve as predictors in the absence of direct measurements.
- **Computational Constraints**: It is assumed that the analysis (including 1,000 bootstrap‑refit iterations) can be completed on a standard CI runner (2 CPU, ~7 GB RAM) using efficient chunked processing; no hard time or memory caps are imposed by the specification.
- **Methodological Framing**: It is assumed that the study is observational; therefore, all findings regarding feature importance and interactions will be framed as associational rather than causal, as no randomization is applied.
- **Standard Practices**: The selection of a 5‑fold CV, k = 5 for imputation, StandardScaler normalization, and a 2‑hour Bayesian‑optimization budget follows community‑standard practice for datasets of this size.
- **No GPU Requirement**: It is assumed that XGBoost and Random Forest implementations used are optimized for CPU execution and do not require CUDA or GPU acceleration.
- **Power Analysis Justification**: Based on Cohen (1988) and Efron & Tibshirani (1993), a sample size of **≥ 200** provides ≥ 80 % power to detect interaction effect sizes of *f*² ≥ 0.15 and yields bootstrap 95 % CI widths for feature‑importance scores of ≤ 0.1, satisfying the reliability requirement for SC‑002.
