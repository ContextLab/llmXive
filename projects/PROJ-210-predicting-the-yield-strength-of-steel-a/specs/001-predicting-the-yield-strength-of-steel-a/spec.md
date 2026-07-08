# Feature Specification: Predicting the Yield Strength of Steel Alloys from Composition and Heat Treatment Parameters

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Predicting the Yield Strength of Steel Alloys from Composition and Heat Treatment Parameters"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must ingest raw tabular data from NIST and Materials Project repositories, clean missing values, normalize thermal parameters, generate specific elemental ratios and pairwise interaction features, and orthogonalize these interaction features against main effects to create a ready-to-model dataset.

**Why this priority**: Without a clean, engineered dataset containing both main effects and properly isolated interaction terms, no predictive modeling or statistical testing can occur. This is the foundational step.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a provided sample CSV and verifying the output DataFrame contains exactly the required columns (composition %, thermal params, derived interactions, orthogonalized interactions) with no null values in the target variable.

**Acceptance Scenarios**:

1. **Given** a raw dataset with missing yield strength values, **When** the preprocessing script runs, **Then** rows with missing yield strength are removed and the remaining dataset contains no nulls in the target column.
2. **Given** raw thermal parameters (temperature, cooling rate) with varying scales, **When** normalization is applied, **Then** all thermal parameters are scaled to the [0.0, 1.0] range.
3. **Given** categorical heat treatment types (quenching, tempering), **When** encoding is applied, **Then** the output contains one-hot encoded binary columns for each category.
4. **Given** elemental composition columns, **When** feature engineering runs, **Then** the output includes specific elemental ratios (C/Mn, Cr/Ni) and pairwise interaction features (e.g., C × Cooling Rate) that are orthogonalized against their constituent main effects.

---

### User Story 2 - Model Training and Interaction Detection (Priority: P2)

The system must train a Generalized Additive Model (GAM) with splines (to capture non-linear main effects), Regularized Linear Regression, Random Forest, and XGBoost models on the engineered dataset to identify which composition-heat treatment interactions carry the most predictive signal beyond non-linear main effects.

**Why this priority**: This addresses the core research question: identifying specific interactions (e.g., Carbon × Cooling Rate) that explain variance beyond main effects, while avoiding false positives caused by unmodeled non-linearities.

**Independent Test**: The training module can be tested by running it on a fixed subset of data and verifying that the output includes feature importance rankings, interaction SHAP values, R² scores for all four model types, and p-values from permutation tests for top interaction terms.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset with orthogonalized interaction features, **When** the training loop executes, **Then** four distinct models (GAM with splines, Linear Regression, Random Forest, XGBoost) are fitted with hyperparameters tuned via 3-fold cross-validation.
2. **Given** the trained models, **When** SHAP analysis is performed, **Then** the system outputs a ranked list of interaction terms (e.g., C × Cooling Rate) sorted by mean absolute SHAP value.
3. **Given** the top N interaction terms, **When** statistical validation runs, **Then** a permutation test is performed to generate p-values, and these p-values are corrected using the Benjamini-Hochberg procedure (alpha ≤ 0.05).
4. **Given** multiple models, **When** performance is compared, **Then** the R² score of the best model (XGBoost/RF) is compared against the GAM baseline to determine if interactions add value beyond non-linear main effects.

---

### User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

The system must perform sensitivity analysis on any decision thresholds (e.g., feature importance cutoffs) and validate that results are robust across small variations in these parameters, measuring feature selection stability rather than impossible false-positive rates.

**Why this priority**: To ensure methodological soundness, the project must demonstrate that findings are not artifacts of arbitrary threshold choices, satisfying the requirement for threshold justification and sensitivity analysis.

**Independent Test**: The sensitivity module can be tested by running it with a specific threshold set to 0.05, 0.01, and 0.10, and verifying that the system reports how the feature selection stability (Jaccard index) and rank consistency vary across these values.

**Acceptance Scenarios**:

1. **Given** a selected interaction threshold for feature importance, **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over {0.01, 0.05, 0.10} and reports the variation in the number of selected features.
2. **Given** the selected features at different thresholds, **When** stability is calculated, **Then** the system outputs the Jaccard index (≥ 0.8 target) and Spearman rank correlation between the top 5 features across the sweep.
3. **Given** a community-standard basis for a cutoff, **When** the justification is documented, **Then** the spec explicitly cites the rationale (e.g., "based on standard metallurgical carbon equivalent formulas") for the chosen threshold.

---

### Edge Cases

- What happens when the dataset contains fewer than 100 samples after cleaning? (System must trigger the fallback strategy defined in Assumptions, such as synthetic data generation or literature-based priors, and log a warning).
- How does the system handle a dataset where all samples have identical heat treatment parameters? (System must detect zero variance in thermal features and exclude them from interaction analysis to avoid collinearity errors).
- What happens if the NIST or Materials Project API is unreachable? (System must fail gracefully with a clear error message indicating the missing data source).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest tabular data from NIST and Materials Project repositories, removing rows with missing yield strength values (See US-1).
- **FR-002**: System MUST normalize thermal parameters (temperature, cooling rate) to a [0.0, 1.0] scale and encode categorical heat treatment types as one-hot vectors (See US-1).
- **FR-003**: System MUST generate pairwise interaction features for elemental ratios (specifically C/Mn and Cr/Ni) and thermal parameters (cooling rate × holding time), and orthogonalize these interaction features against their constituent main effects to prevent collinearity (See US-1).
- **FR-004**: System MUST train Generalized Additive Models (GAM) with splines, Regularized Linear Regression, Random Forest, and XGBoost models using `scikit-learn` and `xgboost` in CPU-only mode with 3-fold cross-validation (See US-2).
- **FR-005**: System MUST compute SHAP summary plots and interaction SHAP values to rank features by mean absolute SHAP value (See US-2).
- **FR-006**: System MUST perform a sensitivity analysis sweeping decision cutoffs over {0.01, 0.05, 0.10} and report the variation in feature selection stability (Jaccard index) and rank consistency (Spearman correlation) (See US-3).
- **FR-007**: System MUST frame all findings as associational rather than causal, explicitly stating that no random assignment was used (See US-2).
- **FR-008**: System MUST apply the Benjamini-Hochberg procedure for false discovery rate (FDR) correction with alpha ≤ 0.05 to p-values generated from permutation tests of interaction terms (See US-2).
- **FR-009**: System MUST perform permutation tests on the top-ranked interaction terms (holding main effects constant) to generate p-values for statistical significance (See US-2).
- **FR-010**: System MUST orthogonalize all interaction features against their constituent main effects prior to model training to ensure SHAP values reflect true interaction signals (See US-1).

### Key Entities

- **SteelSample**: Represents a single alloy instance with attributes: elemental composition (%C, %Mn, %Cr, etc.), heat treatment parameters (tempering temp, cooling rate, holding time), and measured yield strength (MPa).
- **RatioFeature**: Represents a derived feature calculating a specific ratio of two elemental compositions (e.g., C/Mn, Cr/Ni) used to capture synergistic effects.
- **InteractionFeature**: Represents a derived feature combining two base variables (e.g., Carbon × Cooling Rate) used to capture synergistic effects, which has been orthogonalized against main effects.
- **ModelResult**: Represents the output of a trained model, including R² score, feature importance rankings, SHAP values, and permutation p-values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The statistical significance of identified dominant interaction terms is measured against the null hypothesis of no interaction via permutation p-values (See US-2).
- **SC-002**: The R² score improvement of the best model (XGBoost/RF) over the baseline GAM model (with splines) is measured against the performance of the GAM model (See US-2).
- **SC-003**: The stability of feature selection across the sensitivity sweep (thresholds {0.01, 0.05, 0.10}) is measured against the Jaccard index (target ≥ 0.8) and Spearman rank correlation of the top 5 ranked interaction terms (See US-3).
- **SC-004**: The computational resource usage (RAM, CPU time) is measured against the free-tier CI constraints (≤7 GB RAM, ≤6 hours) (See Assumptions).
- **SC-005**: The validity of the dataset-variable fit is measured against the requirement that every predictor and outcome variable exists in the source data (See Assumptions).

## Assumptions

- The NIST Materials Data Repository and Materials Project contain datasets with ≥100 samples including all required variables: elemental composition (%C, %Mn, %Cr, etc.), heat treatment parameters (tempering temperature, cooling rate, holding time), and measured yield strength (MPa). If fewer than 100 samples are found, a fallback strategy (synthetic data generation or literature-based priors) will be employed.
- The analysis will be observational; therefore, all findings regarding composition-heat treatment relationships will be framed as associational, not causal.
- The dataset will be limited to ≤10,000 rows to ensure it fits within the ~7 GB RAM limit of the free-tier CI runner.
- No GPU, CUDA, or 8-bit/4-bit quantization methods will be used; all models will run in default precision on CPU.
- The "carbon equivalent" and "hardenability factor" indices will be computed using standard metallurgical formulas (e.g., IIW formula) as a community-standard basis.
- If the dataset lacks specific interaction variables (e.g., post-task anxiety/rumination analogs), the analysis will proceed with available variables, and any missing data will be flagged as `[NEEDS CLARIFICATION]` in the implementation phase.
- The total compute time for model training and cross-validation will remain within a practical timeframe on 2 CPU cores.
- The sensitivity analysis thresholds {0.01, 0.05, 0.10} are chosen as defensible defaults based on common statistical practices for feature importance cutoffs.
- Orthogonalization of interaction features against main effects is a standard practice to mitigate collinearity in materials informatics.