# Feature Specification: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

**Feature Branch**: `001-predict-weibull-modulus`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Composition on the Weibull Modulus of Ceramics"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1)

As a materials scientist, I want to ingest raw ceramic property data (stoichiometry, processing parameters, and Weibull modulus values) from open repositories and automatically compute elemental descriptors (e.g., cation size variance, electronegativity spread) so that I have a clean, feature-rich dataset ready for analysis without manual calculation.

**Why this priority**: This is the foundational step. Without a validated dataset containing both the target variable (Weibull modulus) and the engineered features derived from composition, no modeling or analysis can occur. It directly addresses the "Data Acquisition" and "Feature Engineering" phases of the methodology.

**Independent Test**: Can be fully tested by running the data pipeline on a sample of 100 known entries and verifying that the output CSV contains the target variable and at least 10 computed compositional descriptors with no missing values for the primary predictors.

**Acceptance Scenarios**:

1. **Given** a raw dataset entry with valid stoichiometry and a reported Weibull modulus, **When** the ingestion script processes the entry, **Then** the system outputs a row containing the calculated mean atomic radius, standard deviation of electronegativity, and the original Weibull modulus.
2. **Given** a raw dataset entry missing the sample count ($N$) for the Weibull test, **When** the cleaning step runs, **Then** the system flags the entry as "insufficient sample count" and excludes it from the training set (as per $N < 30$ rule).
3. **Given** a raw dataset entry with missing processing parameters (e.g., sintering temperature), **When** the cleaning step runs, **Then** the system imputes the missing value with the median of the available dataset for that specific material class (primary anion/cation group); if the class-specific sample size is < 5, the system falls back to the global median of the entire dataset.

### User Story 2 - Predictive Modeling and Cross-Validation (Priority: P2)

As a researcher, I want to train Random Forest and Gradient Boosting regression models using the computed descriptors to predict the Weibull modulus, with strict 5-fold cross-validation (or hold-out if N < 50), so that I can identify which compositional factors most strongly correlate with material reliability.

**Why this priority**: This delivers the core scientific output: the predictive link between composition and reliability. It addresses the "Model Training" and "Validation" phases. It must be independent of the interpretability phase to allow for model comparison.

**Independent Test**: Can be fully tested by executing the training script on a subset of the data and verifying that the output includes the $R^2$ and Mean Absolute Error (MAE) scores for both models, along with a stratified split report confirming the test set distribution matches the training set distribution.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with 500+ valid entries, **When** the training pipeline executes, **Then** the system outputs a JSON report containing the MAE and $R^2$ for the Random Forest model trained with 5-fold cross-validation.
2. **Given** a dataset with imbalanced material classes, **When** the split occurs, **Then** the system performs stratified splitting to ensure each fold contains a proportional representation of the material classes.
3. **Given** the CPU constraints of the environment, **When** the hyperparameter tuning runs, **Then** the system restricts the search space to a maximum of 50 parameter combinations to ensure completion within the 6-hour runtime limit.

### User Story 3 - Feature Importance and Mechanistic Interpretation (Priority: P3)

As a domain expert, I want to extract SHAP (SHapley Additive exPlanations) values from the best-performing model to rank the contribution of each compositional descriptor and compare the top features against known fracture mechanics principles, so that I can propose actionable design rules for high-reliability ceramics.

**Why this priority**: This translates the "black box" model results into scientific insight, addressing the "Feature Analysis" and "Mechanistic Interpretation" phases. It provides the "why" behind the predictions.

**Independent Test**: Can be fully tested by running the analysis script on the trained model and verifying that the output lists the top 5 most influential descriptors and includes a correlation matrix between these descriptors and the Weibull modulus.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** the SHAP analysis runs, **Then** the system generates a ranked list of features where the top feature is identified as a compositional descriptor (e.g., cation size mismatch).
2. **Given** the top-ranked descriptors, **When** the system compares them against literature principles, **Then** the output includes a text summary linking the top descriptor to a physical mechanism (e.g., "Grain boundary stability") or notes a lack of known mechanistic basis.
3. **Given** multiple predictors that are definitionally related (e.g., variance and mean of atomic radius), **When** the collinearity check runs, **Then** the system reports the Variance Inflation Factor (VIF) and flags any pair with VIF > 5 for descriptive framing rather than independent causal claims.

### Edge Cases

- **What happens when the scraped dataset contains fewer than 50 total valid entries after cleaning?** (The system MUST switch to a simple hold-out validation strategy (80/20 split) provided the TOTAL dataset size is >= 30. If the TOTAL dataset size is < 30 after filtering, the system MUST halt and output a "Power Limitation" error.)
- **How does the system handle a composition where the stoichiometry implies a non-stoichiometric phase that is not in the descriptor lookup table?** (The system MUST log a warning, exclude the entry, or impute using the nearest neighbor element if the global median fallback is triggered due to small class size.)
- **What if the Weibull modulus value is reported as a range (e.g., "10-15") rather than a point estimate?** (The system MUST extract the midpoint, set a boolean column `is_range_flag` to `true`, and store the original string in a column `range_original` in the output dataset.)

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest ceramic property data from specified open repositories (Materials Project, NIST, arXiv) and filter for entries with reported Weibull parameters and stoichiometry. (See US-1)
- **FR-002**: System MUST compute elemental descriptors including mean atomic radius, standard deviation of electronegativity, and valence electron concentration (calculated as total valence electrons divided by total number of atoms in the formula unit) from the stoichiometry of each entry. (See US-1)
- **FR-003**: System MUST exclude dataset entries where the sample count ($N$) for the Weibull test is less than 30 to ensure statistical robustness of the target variable. The system MUST extract $N$ from fields named 'N', 'sample_size', or 'n'; if absent, the entry is excluded. (See US-1)
- **FR-004**: System MUST train Random Forest and Gradient Boosting regressors using 5-fold cross-validation on a CPU-optimized environment without GPU acceleration. (See US-2)
- **FR-005**: System MUST perform stratified data splitting based on 'primary_anion_cation_group' (derived from stoichiometry) to ensure the validation metric is independent of the training distribution. (See US-2)
- **FR-005.5**: System MUST perform a leakage check by re-running the best model without the 'primary_anion_cation_group' feature; if the performance drops by less than 10%, the system MUST flag a "Potential Leakage" warning. (See US-2)
- **FR-006**: System MUST calculate and report SHAP values to rank the contribution of each compositional descriptor to the predicted Weibull modulus. (See US-3)
- **FR-007**: System MUST detect and report collinearity diagnostics (e.g., VIF) for predictors that are definitionally related to prevent claims of independent predictive effects. (See US-3)
- **FR-008**: System MUST append the disclaimer "These results represent statistical associations only and do not imply causal relationships" to all text outputs and exclude the word "cause" from the 'conclusion' field of the report. (See US-2)
- **FR-009**: System MUST report the Coefficient of Variation (CV) of the top 5 feature importance scores across cross-validation folds to assess stability. (See US-3)

### Key Entities

- **CeramicEntry**: Represents a single material sample with attributes: `composition` (string), `processing_params` (dict), `weibull_modulus` (float), `sample_count` (int), `is_range_flag` (bool), `range_original` (string).
- **DescriptorSet**: Represents the computed features for a CeramicEntry, including `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`.
- **ModelResult**: Represents the output of a training run, including `model_type`, `mae`, `r_squared`, `feature_importance_ranking`, `cv_stability_scores`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The Mean Absolute Error (MAE) of the best-performing model is measured against a baseline of predicting the global mean Weibull modulus, and the model's MAE must be at least 10% lower than the baseline MAE. (See FR-004, FR-005)
- **SC-002**: The stability of the top 5 feature importance scores is measured by the Coefficient of Variation (CV) across folds, and the CV must be <= 0.2 for the top 5 features. (See FR-009)
- **SC-003**: The collinearity diagnostic (VIF) for all predictor pairs is measured against a threshold of 5.0 to ensure no high multicollinearity invalidates the feature ranking. (See FR-007)
- **SC-004**: The total dataset size (N) is measured against the minimum requirement of 30 valid entries to ensure sufficient power. If N >= 50, 5-fold CV is used; if 30 <= N < 50, hold-out validation is used. (See FR-003, FR-004)
- **SC-005**: The runtime of the full pipeline (ingestion to SHAP analysis) is measured against the 6-hour limit on a 2-CPU, 7GB RAM runner. (See FR-004)

## Assumptions

- **Assumption about data source**: The public repositories (Materials Project, NIST) contain at least 100 entries with explicitly reported Weibull modulus values and complete stoichiometry, as the methodology relies on these specific fields.
- **Assumption about compute constraints**: The dataset, once cleaned and feature-engineered, will fit within 7 GB of RAM, allowing the entire analysis to run on the GitHub Actions free-tier CPU runner without memory swapping or OOM errors.
- **Assumption about variable availability**: The source datasets contain the necessary processing parameters (e.g., sintering temperature) or that missing values can be reasonably imputed with the median without introducing significant bias.
- **Assumption about method validity**: The relationship between elemental descriptors and Weibull modulus is non-linear enough to benefit from tree-based models (Random Forest/GBM) but simple enough to be captured by a small dataset (<5,000 samples).
- **Assumption about inference framing**: Since the data is observational and lacks random assignment to composition classes, all conclusions regarding "impact" will be interpreted strictly as statistical associations, not causal effects.
- **Assumption about threshold justification**: The exclusion threshold of $N < 30$ for Weibull tests is based on standard statistical practice for reducing bias in shape parameter estimation; this threshold will be treated as fixed and will not require a sensitivity sweep in this scope.