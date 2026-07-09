# Feature Specification: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

**Feature Branch**: `001-predict-elastic-modulus`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Feature Engineering Pipeline (Priority: P1)

As a researcher, I need to automatically retrieve HEA composition and elastic property data from public repositories (Materials Project, OQMD) and compute compositional descriptors (mixing enthalpy, atomic radius variance, etc.) using Isometric Log-Ratio (ILR) transformation—**methodologically essential to address the compositional singularity issue which the original Idea's simplified methodology overlooked**—so that I have a clean, structured dataset for analysis. **This story also includes the conditional exclusion of Miedema-derived features when the target is set to Residual Bulk Modulus to prevent circular validation, and the generation of `source_metadata.yaml` for provenance.**

**Why this priority**: Without a validated dataset and scientifically sound feature engineering, no modeling can occur. This is the foundational step that determines the feasibility and validity of the entire study.

**Independent Test**: The pipeline can be run on a subset of known HEAs, producing a CSV file with rows corresponding to the input samples and all required descriptor columns populated without errors.

**Acceptance Scenarios**:

1. **Given** valid API keys for Materials Project and OQMD, **When** the pipeline executes, **Then** it retrieves all HEA entries with ≥5 principal elements and filters for those with reported elastic constants.
2. **Given** a raw composition string (e.g., "FeCoNiCrMn"), **When** the feature engineering module runs, **Then** it outputs numeric descriptors (entropy, electronegativity variance) with no NaN values for valid inputs.
3. **Given** compositional data where element percentages sum to 1.0, **When** collinearity checks run, **Then** the system applies an Isometric Log-Ratio (ILR) transformation to break the closure constraint and prevent singular matrices in regression.
4. **Given** the target variable is set to **Residual Bulk Modulus**, **When** the feature set is constructed, **Then** the system excludes Miedema-derived features (Mixing Enthalpy, Miedema-weighted Atomic Radius Variance, Electronegativity Variance calculated via Miedema parameters) to prevent circular validation.
5. **Given** the data retrieval step completes, **When** the pipeline finishes, **Then** it generates a `source_metadata.yaml` file recording API versions, query parameters, and timestamps.

---

### User Story 2 - Model Training and Statistical Evaluation (Priority: P2)

As a researcher, I need to train multiple regression models (Random Forest, Gradient Boosting, ElasticNet) on the prepared dataset to predict the **Residual Bulk Modulus**, **Residual Young's Modulus**, **Residual Shear Modulus**, and **Residual Poisson's Ratio** (where available) and evaluate them using R², RMSE, and grouped bootstrapped confidence intervals. **This story includes the strict data hygiene rule: when the target is a Residual Modulus, the system MUST exclude the set of Miedema-derived features (Mixing Enthalpy, Miedema-weighted Atomic Radius Variance, Electronegativity Variance calculated via Miedema parameters) from the predictor set to prevent circular validation.** It also includes testing the null hypothesis (R² > 0) via permutation test, validating residual correlation with non-Miedema descriptors, and reporting potential confounds.

**Why this priority**: This delivers the core scientific output (the model and its performance metrics) required to answer the research question regarding the specific effect of alloying beyond rule-of-mixtures.

**Independent Test**: The training script completes within 6 hours on a standard CPU runner, outputting a JSON report with metrics for all three models and their confidence intervals.

**Acceptance Scenarios**:

1. **Given** the prepared dataset split (70/15/15), **When** the model training job runs, **Then** it produces R², RMSE, and MAE for **Residual Elastic Moduli** on the held-out test set.
2. **Given** the test set predictions, **When** the grouped bootstrap resampling (1000 iterations, sampling by **unique set of constituent elements**) runs, **Then** it calculates 95% confidence intervals for R² for the target variable.
3. **Given** multiple model comparisons, **When** the evaluation concludes, **Then** the system applies a multiple-comparison correction (FDR) to the **p-values from pairwise performance comparisons** to ensure valid model selection.
4. **Given** the test set, **When** the null hypothesis test runs, **Then** it outputs a p-value for R² > 0 using a permutation test (1000 iterations) and a boolean **significant** flag if p < 0.05.
5. **Given** the residuals and non-Miedema descriptors, **When** the validation check runs, **Then** it calculates Pearson |r|. If |r| > 0.1, the system logs a warning "Potential confound detected" and proceeds with caution.
6. **Given** the residuals and non-linear descriptors, **When** the validation check runs, **Then** it reports the correlation values as *model signal* (expected) rather than confounds.
7. **Given** the target is a **Residual Modulus**, **When** the feature matrix is prepared, **Then** the system explicitly verifies that the set `$MIEDEMA_FEATURES$` is absent from the predictor columns before training begins.

---

### User Story 3 - Interpretability and Associational Reporting (Priority: P3)

As a researcher, I need to extract feature importance (SHAP/Permutation) and generate visualizations (parity plots, partial dependence) while explicitly framing results as associational so that I can understand drivers of stiffness without making causal claims unsupported by the data.

**Why this priority**: This enables scientific insight (which elements drive stiffness) and ensures methodological rigor by preventing over-interpretation of observational data.

**Independent Test**: The report generation step produces a PDF/Markdown summary containing SHAP plots and a disclaimer stating the associational nature of the findings.

**Acceptance Scenarios**:

1. **Given** the best-performing model, **When** the interpretability module runs, **Then** it identifies the top 3-5 compositional descriptors contributing to prediction variance.
2. **Given** the final results, **When** the summary is drafted, **Then** it explicitly states that correlations do not imply causation due to the observational nature of the dataset.
3. **Given** the R² null hypothesis threshold (0.3), **When** sensitivity analysis runs (sweeping thresholds {0.25, 0.30, 0.35}), **Then** it reports the **p-value for R² > 0.3 (estimated via permutation testing)** at each threshold to assess robustness. **If the p-value at the specified significance threshold exceeds 0.05, the primary claim is rejected and the study halts.**

---

### Edge Cases

- **What happens when** the public APIs return insufficient HEA samples with elastic constants (e.g., < 500 samples)?
  - **Given** a retrieved sample count, **When** the count is below 500, **Then** the system does NOT halt. Instead, it proceeds with a **'Reduced Power Analysis'**, generating an 'Underpowered Study Report' that quantifies the power deficit and confidence interval widening. The study continues with the available data, but the final report MUST explicitly state the reduced statistical power and widened confidence intervals.
- **How does system handle** compositional data where element percentages do not sum to 1.0 (data entry error)?
  - **Given** raw compositional data where percentages do not sum to 1.0, **When** the normalization step runs, **Then** the system normalizes percentages to sum to 1.0 and logs the adjustment before feature engineering.
- **What happens when** a model overfits due to high dimensionality relative to sample size?
  - **Given** a train/test gap, **When** the evaluation concludes, **Then** the system calculates the 95% confidence interval of the gap. **If the 95% CI excludes zero (i.e., the gap is statistically significant), the system reports the gap and halts** to prevent invalid model deployment.
- **What happens when** the number of unique element groups (for bootstrapping) is insufficient (e.g., < 10 groups)?
  - **Given** a group count below 10, **When** the bootstrap setup runs, **Then** the system logs a warning: "Insufficient groups for grouped bootstrap (N=[N]); falling back to standard bootstrap with caution" and proceeds, **flagging the resulting confidence intervals as potentially underestimated** in the final report.
- **What happens when** the OQMD/MP APIs lack Bulk Modulus data?
  - **Given** the API returns no Bulk Modulus values, **When** the target construction step runs, **Then** the system executes a fallback sequence: 1) Attempt to switch target to **Shear Modulus** (if available); 2) If Shear Modulus is unavailable, switch to **Formation Energy** with a justification note in the report explaining the change in research question scope. The system halts only if neither alternative is available.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve HEA composition and elastic constant data from Materials Project and OQMD APIs, filtering for alloys with ≥5 principal elements (See US-1).
- **FR-002**: System MUST compute raw elemental descriptors (mixing enthalpy via Miedema's model, atomic radius variance, entropy of mixing) for every sample, **then** apply Isometric Log-Ratio (ILR) transformation to the composition vector to break the closure constraint. **Crucially, if the target variable is a Residual Modulus, the system MUST exclude the set `$MIEDEMA_FEATURES$` from the predictor set.** For **Direct Target** models, these features MAY be included to evaluate their predictive power (See US-1).
- **FR-004**: System MUST train Random Forest, Gradient Boosting, and ElasticNet models using scikit-learn on CPU-only infrastructure to predict the **Residual Bulk Modulus**, **Residual Young's Modulus**, **Residual Shear Modulus**, and **Residual Poisson's Ratio** (See US-2).
- **FR-005**: System MUST compute 95% confidence intervals for R² via grouped bootstrap resampling (1000 iterations, grouping by **unique set of constituent elements**) and apply multiple-comparison correction (FDR) to the p-values of pairwise performance differences (See US-2).
- **FR-006**: System MUST perform sensitivity analysis on the R² null hypothesis threshold (sweeping {0.25, 0.30, 0.35}) and report the **p-value for R² > 0.3 (estimated via permutation testing)** at each threshold to validate the robustness of the primary 0.3 claim. **This analysis is essential to rule out threshold sensitivity. If the p-value at the 0.3 threshold exceeds 0.05, the system MUST reject the primary claim and halt the study.** The primary scientific claim is based on the fixed 0.3 threshold; the sweep is for robustness reporting only. The output MUST include the variance in p-values across these thresholds (See US-3).
- **FR-007**: System MUST explicitly label all findings as associational in final reports to distinguish from causal claims (See US-3).
- **FR-008**: System MUST validate that the residuals are uncorrelated (Pearson |r| < 0.1) **only with `$MIEDEMA_FEATURES$`** **post-training**. If correlation exceeds this threshold, the system MUST log a warning "Potential circularity detected" and proceed with caution, noting the potential confound in the final report. **Correlations with non-linear descriptors are expected and reported as model signal** (See US-2).
- **FR-009**: System MUST record the API versions and query parameters used for data retrieval in a `source_metadata.yaml` file, complying with Constitution Principle VI (Materials Database Provenance) (See US-1).

### Key Entities *(include if data)*

- **HEA Sample**: Represents a single alloy instance; key attributes include elemental composition (atomic %), crystal structure, and measured elastic constants (Bulk Modulus, Shear Modulus, Young's Modulus, Poisson's Ratio).
- **Compositional Descriptor**: Represents a derived feature (e.g., mixing enthalpy, valence electron concentration) calculated from elemental properties and percentages. **Note**: When used with Residual Target, Miedema-derived descriptors are excluded from predictors to ensure orthogonality.
- **Model Performance Record**: Represents the evaluation output for a specific model; key attributes include R², RMSE, MAE, and 95% CI bounds.
- **Definitions**:
  - **`$MIEDEMA_FEATURES$`**: The specific set of features derived from Miedema's model that MUST be excluded when predicting Residual Moduli to prevent circular validation. This set includes:
    1. **Mixing Enthalpy (Miedema)**: Calculated using Miedema's semi-empirical model.
    2. **Atomic Radius Variance (Miedema parameters)**: Calculated as the variance of atomic radii weighted by Miedema's specific interaction parameters (distinct from standard deviation of atomic radii).
    3. **Electronegativity Variance (Miedema parameters)**: Calculated using Miedema's electronegativity scale.
    *Note*: Standard descriptors (e.g., standard deviation of atomic radii, standard mixing entropy) are **NOT** included in this exclusion set and remain valid predictors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset sufficiency is measured against the requirement of ≥500 valid HEA samples with elastic constants from public APIs (See US-1).
- **SC-002**: Model predictive power is measured against the null hypothesis (R² = 0); the system MUST output a **p-value** for the test R² > 0 using a **permutation test (1000 iterations)** and a boolean **significant** flag if p < 0.05. The primary threshold for the null hypothesis claim is a predetermined significance level. (See US-2).
- **SC-003**: Statistical robustness is measured against the requirement that 95% confidence intervals for R² are calculated using grouped bootstrapping (grouped by unique set of constituent elements) to prevent data leakage (See US-2).
- **SC-004**: Methodological validity is measured against the requirement that the final report MUST contain the exact disclaimer string: "These findings are associational and do not imply causation" (See US-3).
- **SC-005**: Residual validity is measured against the requirement that the correlation between residuals and **`$MIEDEMA_FEATURES$`** is |r| < 0.1; if exceeded, the report MUST flag the potential confound (See US-2).

## Assumptions

- **Data Availability**: Public APIs (Materials Project, OQMD) provide access to elastic constants for a sufficient subset of high-entropy alloys without requiring paid enterprise credentials.
- **Compute Constraints**: The total analysis pipeline (data fetch, engineering, training, evaluation) will complete within 6 hours on a standard GitHub Actions free-tier runner (2 CPU, ~7 GB RAM).
- **Observational Nature**: The dataset represents observational data where compositional diversity correlates with elastic modulus, but random assignment of elements is not possible, necessitating associational framing.
- **Descriptor Validity**: Standard compositional descriptors (atomic radius variance, electronegativity variance) are physically meaningful proxies for elastic behavior in HEAs, provided Miedema-derived features are excluded when using the residual target.
- **API Stability**: External data repositories will remain accessible during the execution window; transient failures will be handled via retry logic (max 3 attempts).
- **Residual Strategy Justification**: The use of the residual (B_observed - B_Miedema) as the target variable assumes that Miedema's model captures the rule-of-mixtures baseline. The model is intended to learn the *deviation* from this baseline. We acknowledge that if Miedema's error is systematic, the model may learn to correct for Miedema's bias. FR-008 mandates a check for this confound.
- **Grouping Key Definition**: The term "unique set of constituent elements" (e.g., "CrMnFeCoNi") is the definitive grouping key for bootstrapping, ensuring that resampling occurs across independent chemical spaces rather than just broad categories.