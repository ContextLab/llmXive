# Feature Specification: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

**Feature Branch**: `001-predict-elastic-modulus`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Feature Engineering Pipeline (Priority: P1)

As a researcher, I need to automatically retrieve HEA composition and elastic property data from public repositories (Materials Project, OQMD) and compute compositional descriptors (mixing enthalpy, atomic radius variance, etc.) using Isometric Log-Ratio (ILR) transformation so that I have a clean, structured dataset for analysis that avoids compositional singularity.

**Why this priority**: Without a validated dataset and scientifically sound feature engineering, no modeling can occur. This is the foundational step that determines the feasibility and validity of the entire study.

**Independent Test**: The pipeline can be run on a subset of known HEAs, producing a CSV file with rows corresponding to the input samples and all required descriptor columns populated without errors.

**Acceptance Scenarios**:

1. **Given** valid API keys for Materials Project and OQMD, **When** the pipeline executes, **Then** it retrieves all HEA entries with ≥5 principal elements and filters for those with reported elastic constants.
2. **Given** a raw composition string (e.g., "FeCoNiCrMn"), **When** the feature engineering module runs, **Then** it outputs numeric descriptors (entropy, electronegativity variance) with no NaN values for valid inputs.
3. **Given** compositional data where element percentages sum to 1.0, **When** collinearity checks run, **Then** the system applies an Isometric Log-Ratio (ILR) transformation to break the closure constraint and prevent singular matrices in regression.

---

### User Story 2 - Model Training and Statistical Evaluation (Priority: P2)

As a researcher, I need to train multiple regression models (Random Forest, Gradient Boosting, ElasticNet) on the prepared dataset to predict the **Residual Bulk Modulus** (B_observed - B_Miedema) and evaluate them using R², RMSE, and grouped bootstrapped confidence intervals so that I can identify the best predictive approach for the non-linear alloying effect and quantify uncertainty without data leakage.

**Why this priority**: This delivers the core scientific output (the model and its performance metrics) required to answer the research question regarding the specific effect of alloying beyond rule-of-mixtures.

**Independent Test**: The training script completes within 6 hours on a standard CPU runner, outputting a JSON report with metrics for all three models and their confidence intervals.

**Acceptance Scenarios**:

1. **Given** the prepared dataset split (70/15/15), **When** the model training job runs, **Then** it produces R², RMSE, and MAE for **Residual Bulk Modulus** on the held-out test set.
2. **Given** the test set predictions, **When** the grouped bootstrap resampling (1000 iterations, sampling by **unique set of constituent elements**) runs, **Then** it calculates 95% confidence intervals for R² for the target variable.
3. **Given** multiple model comparisons, **When** the evaluation concludes, **Then** the system applies a multiple-comparison correction (FDR) to the **p-values from pairwise performance comparisons** to ensure valid model selection.

---

### User Story 3 - Interpretability and Associational Reporting (Priority: P3)

As a researcher, I need to extract feature importance (SHAP/Permutation) and generate visualizations (parity plots, partial dependence) while explicitly framing results as associational so that I can understand drivers of stiffness without making causal claims unsupported by the data.

**Why this priority**: This enables scientific insight (which elements drive stiffness) and ensures methodological rigor by preventing over-interpretation of observational data.

**Independent Test**: The report generation step produces a PDF/Markdown summary containing SHAP plots and a disclaimer stating the associational nature of the findings.

**Acceptance Scenarios**:

1. **Given** the best-performing model, **When** the interpretability module runs, **Then** it identifies the top 3-5 compositional descriptors contributing to prediction variance.
2. **Given** the final results, **When** the summary is drafted, **Then** it explicitly states that correlations do not imply causation due to the observational nature of the dataset.
3. **Given** the R² null hypothesis threshold (0.3), **When** sensitivity analysis runs (sweeping thresholds {0.25, 0.30, 0.35}), **Then** it reports the **Type I error rate (estimated via permutation testing)** at each threshold to assess robustness. The primary scientific claim remains based on the fixed 0.3 threshold; the sweep is strictly for robustness reporting.

---

### Edge Cases

- **What happens when** the public APIs return insufficient HEA samples with elastic constants (e.g., < 500 samples)?
  - **Given** a retrieved sample count, **When** the count is below 500, **Then** the system triggers a hard halt and logs the specific deficit message: "Retrieved [N] samples; threshold 500 not met" rather than proceeding with underpowered training.
- **How does system handle** compositional data where element percentages do not sum to 1.0 (data entry error)?
  - **Given** raw compositional data where percentages do not sum to 1.0, **When** the normalization step runs, **Then** the system normalizes percentages to sum to 1.0 and logs the adjustment before feature engineering.
- **What happens when** a model overfits due to high dimensionality relative to sample size?
  - **Given** a train/test gap (absolute difference between training R² and test R²) exceeding 0.15, **When** the evaluation concludes, **Then** the system reports the gap as a diagnostic metric and triggers a hard halt to prevent invalid model deployment, ensuring automated completion within the 6-hour limit.
- **What happens when** the number of unique element groups (for bootstrapping) is insufficient (e.g., < 10 groups)?
  - **Given** a group count below 10, **When** the bootstrap setup runs, **Then** the system logs a warning: "Insufficient groups for grouped bootstrap (N=[N]); falling back to standard bootstrap with caution" and proceeds, rather than halting, to allow for diagnostic reporting.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve HEA composition and elastic constant data from Materials Project and OQMD APIs, filtering for alloys with ≥5 principal elements (See US-1).
- **FR-002**: System MUST compute raw elemental descriptors (mixing enthalpy via Miedema's model, atomic radius variance, entropy of mixing) for every sample, **then** apply Isometric Log-Ratio (ILR) transformation to the composition vector to break the closure constraint. **Note**: When used with the Residual Target, Miedema-derived features (e.g., Mixing Enthalpy calculated via Miedema's model) MUST be excluded from the predictor set to prevent circular validation (See US-1).
- **FR-003**: System MUST apply an Isometric Log-Ratio (ILR) transformation to compositional data before regression to break the closure constraint and prevent singular matrices (See US-1).
- **FR-004**: System MUST train Random Forest, Gradient Boosting, and ElasticNet models using scikit-learn on CPU-only infrastructure to predict the **Residual Bulk Modulus** (B_observed - B_Miedema) (See US-2).
- **FR-005**: System MUST compute 95% confidence intervals for R² via grouped bootstrap resampling (1000 iterations, grouping by **unique set of constituent elements**) and apply multiple-comparison correction (FDR) to the p-values of pairwise performance differences (See US-2).
- **FR-006**: System MUST perform sensitivity analysis on the R² null hypothesis threshold (sweeping {0.25, 0.30, 0.35}) and report the **Type I error rate (estimated via permutation testing)** at each threshold to validate the robustness of the primary 0.3 claim. The primary scientific claim is based on the fixed 0.3 threshold; the sweep is for robustness reporting only. The output MUST include the variance in false-positive rates across these thresholds (See US-3).
- **FR-007**: System MUST explicitly label all findings as associational in final reports to distinguish from causal claims (See US-3).
- **FR-008**: When the target variable is **Residual Bulk Modulus** (B_observed - B_Miedema), the system MUST **exclude** any Miedema-derived features (e.g., Mixing Enthalpy calculated via Miedema's model) from the predictor set to prevent circular validation and multicollinearity (See US-2).
- **FR-009**: System MUST validate that the residuals (B_observed - B_Miedema) are uncorrelated (Pearson |r| < 0.1) with the compositional descriptors prior to model training. If correlation exceeds this threshold, the system MUST log a warning and proceed with caution, noting the potential confound in the final report (See US-2).
- **FR-010**: System MUST record the API versions and query parameters used for data retrieval in a `source_metadata.yaml` file, complying with Constitution Principle VI (Materials Database Provenance) (See US-1).

### Key Entities *(include if feature involves data)*

- **HEA Sample**: Represents a single alloy instance; key attributes include elemental composition (atomic %), crystal structure, and measured elastic constants (Bulk Modulus, Shear Modulus).
- **Compositional Descriptor**: Represents a derived feature (e.g., mixing enthalpy, valence electron concentration) calculated from elemental properties and percentages. **Note**: When used with Residual Target, Miedema-derived descriptors are excluded from predictors to ensure orthogonality.
- **Model Performance Record**: Represents the evaluation output for a specific model; key attributes include R², RMSE, MAE, and 95% CI bounds.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset sufficiency is measured against the requirement of ≥500 valid HEA samples with elastic constants from public APIs (See US-1).
- **SC-002**: Model predictive power is measured against the null hypothesis (R² = 0); the system MUST output a **p-value** for the test R² > 0 and a boolean **significant** flag if p < 0.05. The primary threshold for the null hypothesis claim is a predetermined significance level. (See US-2).
- **SC-003**: Statistical robustness is measured against the requirement that 95% confidence intervals for R² are calculated using grouped bootstrapping (grouped by unique set of constituent elements) to prevent data leakage (See US-2).
- **SC-004**: Methodological validity is measured against the requirement that the final report MUST contain the exact disclaimer string: "These findings are associational and do not imply causation" (See US-3).
- **SC-005**: Residual validity is measured against the requirement that the correlation between residuals and predictors is |r| < 0.1; if exceeded, the report MUST flag the potential confound (See US-2).

## Assumptions

- **Data Availability**: Public APIs (Materials Project, OQMD) provide access to elastic constants for a sufficient subset of high-entropy alloys without requiring paid enterprise credentials.
- **Compute Constraints**: The total analysis pipeline (data fetch, engineering, training, evaluation) will complete within 6 hours on a standard GitHub Actions free-tier runner (2 CPU, ~7 GB RAM).
- **Observational Nature**: The dataset represents observational data where compositional diversity correlates with elastic modulus, but random assignment of elements is not possible, necessitating associational framing.
- **Descriptor Validity**: Standard compositional descriptors (atomic radius variance, electronegativity variance) are physically meaningful proxies for elastic behavior in HEAs, provided Miedema-derived features are excluded when using the residual target.
- **API Stability**: External data repositories will remain accessible during the execution window; transient failures will be handled via retry logic (max 3 attempts).
- **Residual Strategy Justification**: The use of the residual (B_observed - B_Miedema) as the target variable assumes that Miedema's model captures the rule-of-mixtures baseline. The model is intended to learn the *deviation* from this baseline. We acknowledge that if Miedema's error is systematic, the model may learn to correct for Miedema's bias. FR-009 mandates a check for this confound.
- **Grouping Key Definition**: The term "unique set of constituent elements" (e.g., "CrMnFeCoNi") is the definitive grouping key for bootstrapping, ensuring that resampling occurs across independent chemical spaces rather than just broad categories.