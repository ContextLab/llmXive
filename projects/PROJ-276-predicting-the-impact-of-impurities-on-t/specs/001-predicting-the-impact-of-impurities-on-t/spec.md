# Feature Specification: Predicting the Impact of Impurities on the Superconductivity of Magnesium Diboride

**Feature Branch**: `001-impurity-impact-mgb2`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Impurities on the Superconductivity of Magnesium Diboride"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The researcher MUST be able to download and consolidate experimental data from the Materials Project API and the SuperCon dataset, standardize units (atomic % vs weight %), and filter for entries with explicit Tc and impurity data to create a clean, analysis-ready CSV.

**Why this priority**: Without a clean, unified dataset containing the target variable (Tc) and predictors (impurities, synthesis params), no modeling or analysis can occur. This is the foundational step for the entire project.

**Independent Test**: Can be fully tested by running the data ingestion script and verifying the output CSV contains rows with non-null Tc and at least one impurity concentration field, and that the script completes without errors.

**Acceptance Scenarios**:

1. **Given** the Materials Project API and SuperCon dataset are accessible, **When** the ingestion script runs, **Then** a single consolidated CSV is generated with standardized columns for Tc, impurity atomic %, temperature, and pressure. The system MUST verify that the 'impurities' and 'Tc' columns exist and are non-null for >50% of MgB2 entries; if not, the script MUST fail with exit code 1 and a clear error message.
2. **Given** an entry in the source data lacks explicit Tc or impurity data (target variables), **When** the preprocessing step is executed, **Then** that entry is removed from the final dataset (not imputed) to preserve data integrity for the primary analysis.
3. **Given** units are mixed (atomic % and weight %), **When** the conversion script runs, **Then** all impurity concentrations are converted to atomic % using standard atomic weights, and a log of conversions is produced.
4. **Given** data is loaded from a cached file or local source, **When** the ingestion script runs, **Then** provenance metadata (source name, query timestamp, data version) is recorded and attached to the dataset header to ensure reproducibility.

---

### User Story 2 - Model Training and Selection (Priority: P2)

The researcher MUST be able to train multiple regression models (Linear Regression, Random Forest, XGBoost) on the preprocessed data, perform hyperparameter tuning within strict CPU/RAM limits, and select the best model based on cross-validated R² and Mean Absolute Error.

**Why this priority**: This delivers the core predictive capability. The selection of the best model determines the accuracy of the subsequent "Tc suppression" estimates.

**Independent Test**: Can be fully tested by running the training pipeline and verifying that a "best_model.pkl" file is saved, along with a report containing R² scores for all tested models.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset is available, **When** the training script executes, **Then** at least three distinct regressor types are trained, and the one with the highest cross-validated R² is selected. The data split MUST be stratified by impurity type, with a fallback strategy: if an impurity type has <5 samples, it is grouped into a 'Rare Impurities' bin to ensure test set diversity.
2. **Given** the GitHub Actions free-tier runner constraints (2 CPU, 7 GB RAM), **When** hyperparameter tuning runs, **Then** the grid search is limited to ≤10 combinations to ensure the job completes within the 6-hour limit.
3. **Given** the model selection process, **When** the results are logged, **Then** the output includes the specific hyperparameters of the winning model and its R² and MAE scores.

---

### User Story 3 - Statistical Validation and Interpretation (Priority: P3)

The researcher MUST be able to generate statistical evidence that impurity-driven Tc loss is significant (p < 0.05) and visualize the quantitative relationship between impurity concentration and Tc suppression via partial dependence plots.

**Why this priority**: This transforms the model from a "black box" predictor into a scientifically interpretable tool, answering the "quantitative relationship" part of the research question.

**Independent Test**: Can be fully tested by running the evaluation script and verifying the presence of a reported p-value from the significance test and generated plots for the top 3 impurities.

**Acceptance Scenarios**:

1. **Given** the trained model, **When** the multivariate significance test is performed on the *training* model (not the held-out test set), **Then** the p-value for the joint significance of impurity concentration is reported. For Linear Regression, this is ANOVA on training residuals; for tree-based models, this is a Target Permutation Test (sufficient resamples).
2. **Given** the top 3 impurity elements by effect size (identified by permutation importance or coefficient magnitude), **When** Partial Dependence Plots (PDP) analysis runs, **Then** plots are generated showing the trend of Tc suppression per 1 atomic % increase in concentration. Impurities MUST be filtered by statistical significance (p < 0.05) before being ranked for this analysis.
3. **Given** the model output, **When** the rule-of-thumb table is generated, **Then** it lists specific ΔTc values (e.g., "ΔTc ≈ -2 K per % C") derived from the model coefficients (for Linear Regression) or SHAP values averaged over the test set (for tree-based models).

---

### Edge Cases

- What happens when a specific impurity element has only one or two data points in the consolidated dataset? (System must exclude it from the "top 3" analysis to avoid overfitting, or group it into a 'Rare Impurities' bin for stratification).
- How does the system handle synthesis parameters that are reported as ranges (e.g., "800-900°C")? (System must impute the midpoint and flag the entry as "range-imputed" to preserve predictor utility, distinct from target variable handling).
- What happens if the Materials Project API returns no Mg-B entries? (System must fail gracefully with a clear error message indicating the data source is empty, and exit with code 1).
- What happens if the SuperCon dataset lacks structured impurity columns for MgB2? (System must verify column presence in US-1 AC-1; if missing for >50% of entries, the system MUST halt with exit code 1 and a specific error message).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and merge MgB₂ data from the Materials Project API and the SuperCon dataset, filtering for entries with explicit Tc and impurity data. If the canonical sources are unreachable or return empty data, the system MUST raise a fatal error (exit code 1) with a clear message. Provenance metadata (source, timestamp) MUST be recorded for all data, including cached files. (See US-1)
- **FR-002**: System MUST convert all impurity concentrations to atomic % and standardize synthesis units (Kelvin, GPa) before model ingestion. (See US-1)
- **FR-003**: System MUST train at least three distinct regression models (Linear, Random Forest, XGBoost) and select the best based on cross-validated R². (See US-2)
- **FR-004**: System MUST perform statistical significance testing on the *training* model to validate impurity predictors:
  - If the model is Linear Regression, perform multivariate ANOVA on the training residuals to derive p-values for coefficients.
  - If the model is Random Forest or XGBoost, perform a Target Permutation Test (resampling the target variable Y) to build a null distribution and calculate a p-value for the null hypothesis that impurities have no effect.
  - If collinear predictors are detected (Variance Inflation Factor ≥ 5.0), they MUST be grouped into a single feature or removed before testing. (See US-3)
- **FR-005**: System MUST generate Partial Dependence Plots (PDP) for the top 3 impurity elements (identified by effect size, after filtering for statistical significance p < 0.05) to visualize the quantitative Tc suppression relationship. (See US-3)
- **FR-006**: System MUST enforce a hyperparameter grid limit of ≤10 combinations to ensure execution within the 6-hour CPU-only CI window. (See US-2)

### Key Entities

- **DatasetRecord**: Represents a single experimental entry containing Tc (K), impurity concentrations (atomic %), synthesis temperature (K), pressure (GPa), and method flags.
- **ModelPerformance**: Stores the R², MAE, and hyperparameters for each trained model variant to facilitate selection.
- **ImpurityEffect**: A derived entity linking an impurity element to its calculated ΔTc per atomic % and statistical significance (p-value). The p-value is derived from the specific statistical test defined in FR-004 (ANOVA for Linear, Target Permutation for Tree-based).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model predictive accuracy (R²) is measured against the held-out test set to verify the methodology is sound. (Research Goal: R² ≥ 0.75 is hypothesized, but the system requirement is strictly the measurement of R²). (See US-2)
- **SC-002**: Statistical significance of impurity impact is measured against the α = 0.05 threshold via ANOVA (on training residuals) or Target Permutation Test (with a sufficient number of resamples) p-values to confirm non-accidental correlation. (See US-3)
- **SC-003**: Feature importance ranking is measured via permutation importance with confidence intervals (sufficient bootstrap resamples) to ensure robustness. (See US-3)
- **SC-004**: Computational feasibility is measured against a constrained runtime limit and memory cap on a GitHub Actions free-tier runner. (See US-2)
- **SC-005**: Data completeness is measured by the percentage of source entries successfully converted to atomic % and retained in the final analysis set. (See US-1)

## Assumptions

- The Materials Project API and SuperCon dataset contain sufficient MgB₂ entries with explicit Tc and impurity data to support a regression analysis (minimum expected N > 50).
- The "SuperCon" dataset on HuggingFace Datasets is accessible without authentication or complex API key rotation during the CI run.
- Impurity concentrations reported in weight % can be converted to atomic % using standard periodic table data under a **single-phase solid solution approximation**. This assumes impurities substitute directly into the lattice; the system acknowledges that secondary phases (e.g., MgO, B4C) may introduce systematic error in the predictor variable, which the model attempts to capture via the aggregate concentration proxy. Results are interpreted with this limitation in mind.
- The relationship between impurity concentration and Tc is sufficiently linear or monotonic to be captured by Random Forest or XGBoost models without requiring deep neural networks.
- No GPU acceleration is required or available; all libraries (scikit-learn, xgboost) must run in default CPU mode.
- The dataset does not contain collinear predictors that are definitionally derived from one another (e.g., total impurity % vs. individual impurity %) in a way that invalidates independent effect estimation; if present (VIF ≥ 5.0), they will be treated as a joint block or removed to ensure valid ANOVA/Permutation testing.
- **Research Hypothesis**: The dataset exhibits sufficient signal-to-noise ratio to achieve R² ≥ 0.75, though experimental variance (grain size, porosity) may lower this value.