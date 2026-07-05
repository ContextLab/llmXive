# Feature Specification: Predicting Perovskite Stability via Compositional Fingerprints

**Feature Branch**: `001-predicting-perovskite-stability`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "How does elemental composition determine the thermal decomposition temperature of metal halide perovskites, and can compositional descriptors alone predict stability across diverse perovskite families?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Descriptor Computation (Priority: P1)

As a materials scientist, I want to download perovskite composition and thermal stability datasets from Materials Project and NREL, filter for entries with experimentally measured decomposition temperatures, and compute compositional descriptors (atomic fractions, weighted averages of elemental properties, variance metrics) so that I have a clean feature matrix for model training.

**Why this priority**: Without reliable data and descriptors, no downstream modeling is possible. This is the foundational data pipeline that all subsequent analysis depends on.

**Independent Test**: Can be fully tested by downloading a sample of the source datasets, computing descriptors for 50 perovskite formulas, and verifying that the output CSV contains the expected columns: [formula, T_d, atomic_fraction_A, atomic_fraction_B, atomic_fraction_X, weighted_ionic_radius, weighted_electronegativity, weighted_formation_enthalpy, variance_ionic_radius, variance_electronegativity] with non-null values.

**Acceptance Scenarios**:

1. **Given** Materials Project and NREL API keys are configured, **When** the data acquisition script runs, **Then** perovskite entries with decomposition temperature measurements are downloaded and stored locally with source attribution.
2. **Given** a perovskite chemical formula (e.g., "FAPbI3"), **When** descriptor computation runs, **Then** the output includes atomic fractions, weighted ionic radii, weighted electronegativity, and variance metrics for A/B/X site elements.
3. **Given** the raw dataset contains sufficient entries, **When** filtering by experimental decomposition temperature availability, **Then** a minimum of 200 entries remains for training (based on power analysis for regression stability, n ≥ 10 × features) with ≤10% missing values in any descriptor column, flagging if this target is not met.

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

As a data analyst, I want to implement three baseline regressors (Random Forest, Gradient Boosting, Elastic Net), perform k-fold cross-validation with grid search limited to ≤10 hyperparameter combinations, and track RMSE, R², and MAE so that I can identify the best-performing model within a fixed compute budget.

**Why this priority**: This delivers the core predictive capability. The model performance determines whether compositional fingerprints carry sufficient signal for stability prediction.

**Independent Test**: Can be fully tested by running cross-validation on a 50-entry subset and verifying that all three models complete within 30 minutes with R² values reported for each fold.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with ≥200 entries and ≥10 compositional descriptors, **When** the model training pipeline runs with 5-fold cross-validation, **Then** all three baseline regressors produce R², RMSE, and MAE metrics for each fold.
2. **Given** grid search is configured with ≤10 hyperparameter combinations per model, **When** training completes, **Then** the best hyperparameters and corresponding cross-validation metrics are logged.
3. **Given** the total compute budget is 6 hours on a CPU-only runner, **When** model training and cross-validation execute, **Then** the pipeline completes within 4 hours ([deferred] of the 6-hour budget) with ≤10% of the budget consumed by hyperparameter search to ensure CI/CD efficiency.

---

### User Story 3 - Feature Importance Analysis and External Validation (Priority: P3)

As a domain researcher, I want to extract SHAP values from the best-performing model, identify which elemental properties drive stability predictions, and test on held-out experimental data from the literature so that I can validate generalizability beyond the training distribution.

**Why this priority**: This provides interpretability and external validation. While not strictly required for a working model, it is essential for scientific credibility and answering the research question about which compositional factors matter.

**Independent Test**: Can be fully tested by running SHAP analysis on a 50-entry test set and verifying that the top 3 features by importance are reported with corresponding SHAP values and permutation-test p-values.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest or Gradient Boosting model, **When** SHAP analysis and permutation importance testing run (A sufficient number of permutations will be conducted to ensure statistical robustness.), **Then** the system reports the top descriptors by absolute SHAP value along with their permutation-test p-values, flagging those with p < 0.05 as statistically significant.
2. **Given** held-out experimental data from the literature containing compositions with elements or structural motifs NOT present in the training set (e.g., double perovskites, tin-halides if training was lead-only), **When** the best model predicts on this external test set, **Then** the R² and RMSE are reported separately from cross-validation metrics to assess true out-of-distribution generalizability.
3. **Given** feature importance results, **When** the analysis completes, **Then** a ranked list of elemental properties (ionic radii, electronegativity, formation enthalpy) by contribution to decomposition temperature prediction is generated.

---

### Edge Cases

- What happens when the Materials Project or NREL API is unavailable? The pipeline MUST retry up to 3 times with exponential backoff (min, min, 4 min) before failing gracefully with a logged error.
- How does the system handle perovskite formulas with missing elemental property data? Entries with ≥2 missing descriptor values MUST be excluded from training, and a count of excluded entries MUST be logged.
- What happens when the held-out test set contains compositions outside the training distribution? The system MUST flag these as extrapolation cases and report separate metrics for in-distribution vs. out-of-distribution predictions.
- How does the system handle collinearity between compositional descriptors (e.g., ionic radius variance vs. mean)? A variance inflation factor (VIF) diagnostic MUST be computed, and descriptors with VIF > 5 MUST be flagged for review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download perovskite composition and thermal stability data from Materials Project and NREL, filtering for entries with experimentally measured decomposition temperatures (TGA onset) (See US-1)
- **FR-002**: System MUST compute compositional descriptors including atomic fractions, weighted averages of elemental properties (ionic radius, electronegativity, first ionization energy, formation enthalpy), and variance metrics across A/B/X site elements. The target variable (T_d) MUST be sourced from independent experimental TGA data, distinct from calculated thermodynamic properties (See US-1)
- **FR-003**: System MUST implement three baseline regressors (Random Forest, Gradient Boosting, Elastic Net) using scikit-learn with grid search limited to ≤10 hyperparameter combinations per model (See US-2)
- **FR-004**: System MUST perform 5-fold cross-validation on training data, tracking RMSE, R², and MAE as primary metrics with stratification by perovskite family (See US-2)
- **FR-005**: System MUST extract SHAP values from the best-performing model for interpretability and perform permutation importance testing with a sufficient number of permutations to assess feature significance at p < 0.05 (See US-3)
- **FR-006**: System MUST test the final model on held-out experimental data from the literature containing compositions with elements or structural motifs NOT present in the training set to assess true out-of-distribution generalizability (See US-3)
- **FR-007**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) when reporting feature importance significance to control family-wise error rate (See US-3)
- **FR-008**: System MUST compute variance inflation factor (VIF) diagnostics for all compositional descriptors and flag any with VIF > 5 (See US-3)

### Key Entities

- **PerovskiteEntry**: A single perovskite composition record with attributes: chemical formula, A/B/X site elements, decomposition temperature (°C), source database, measurement uncertainty (°C)
- **CompositionalDescriptor**: A feature vector for a perovskite entry with attributes: atomic fractions (A, B, X), weighted ionic radius, weighted electronegativity, weighted formation enthalpy, variance metrics
- **ModelRun**: A training experiment record with attributes: model type, hyperparameters, cross-validation metrics (R², RMSE, MAE), training time, feature importance ranking

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: R² of the best model on held-out test set is measured against the research target of ≥ 0.6 (See US-2)
- **SC-002**: Total pipeline runtime is measured against the specified CPU-only compute budget (See US-2)
- **SC-003**: External validation R² is measured against the cross-validation R² to assess generalizability gap (See US-3)
- **SC-004**: Feature importance significance (p-value) is measured against the random baseline via permutation tests at p < 0.05 (See US-3)
- **SC-005**: Collinearity diagnostics (VIF) are measured against the threshold of 5 to identify descriptor redundancy (See US-3)
- **SC-006**: Dataset-variable fit is measured by verifying that every predictor and outcome variable in the analysis is present in the source datasets (Materials Project, NREL), flagging if any required variable is missing (See US-1)

## Assumptions

- Materials Project and NREL databases contain sufficient perovskite entries (≥200) with experimentally measured decomposition temperatures for training a regression model
- The thermal decomposition temperature measurements in the source datasets have documented precision (±5°C to ±10°C based on typical thermogravimetric analyzer specifications) — The reported measurement uncertainty for decomposition temperatures in the source datasets is ±5°C to ±10°C, consistent with standard thermogravimetric analyzer (TGA) precision specifications for metal halide perovskites. This uncertainty range is treated as a fixed error bound in the data ingestion pipeline (FR-001) and is used to weight samples during model training if uncertainty metadata is explicitly provided; otherwise, the default ±10°C bound applies.
- The target variable (T_d) is an independent experimental measurement (TGA onset) not definitionally derived from the formation enthalpy (ΔH_f) predictor used in the feature set
- The research design is observational (no random assignment of compositions), so findings MUST be framed as associational relationships between composition and stability, not causal claims
- CPU-only scikit-learn models (Random Forest, Gradient Boosting, Elastic Net) will complete within 6 hours on a GitHub Actions free-tier runner with CPU cores and ~7 GB RAM
- The dataset size (≤500 entries after filtering) will fit within ~7 GB RAM and ~ GB disk constraints
- Compositional descriptors (atomic fractions, elemental property averages) are not definitionally collinear with decomposition temperature; any observed relationships are empirical, not mechanical
- No GPU, CUDA, or hardware accelerators are available or required for the analysis
- Sensitivity analysis for any decision thresholds (e.g., feature importance cutoffs) will sweep over absolute differences ∈ {A range of significance thresholds, including 0.05 and 0.1, will be evaluated.} and report how false-positive/false-negative rates vary across the sweep
- Related work citations from the idea Markdown are copied verbatim without fabrication or modification
- The held-out test set stratification by perovskite family (lead-halide, tin-halide, double perovskites) ensures independent evaluation across compositionally distinct groups