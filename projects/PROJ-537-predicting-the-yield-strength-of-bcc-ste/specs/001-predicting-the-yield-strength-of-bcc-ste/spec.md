# Feature Specification: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

**Feature Branch**: `001-predict-yield-strength-bcc`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory"

## User Scenarios & Testing

### User Story 1 - Data Integration and Validation (Priority: P1)

As a materials researcher, I need to successfully merge experimental yield strength data from public repositories (MatNavi/NIST) with pre-computed DFT elastic constants from the Materials Project API, so that I can establish a unified dataset linking atomic-scale properties to macroscopic strength.

**Why this priority**: Without a validated, merged dataset containing both the predictor (DFT elastic constants) and the outcome (experimental yield strength), no modeling or analysis can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: The system can be tested by executing the data ingestion script and verifying that the resulting merged CSV contains at least 30 valid rows where both experimental yield strength and DFT shear modulus values are non-null. If the dataset contains between 20 and 29 rows, the system must log a warning regarding reduced statistical power but continue execution. The merge logic must correctly filter for BCC structure stability.

**Acceptance Scenarios**:

1. **Given** a list of BCC iron alloy compositions from MatNavi, **When** the system queries the Materials Project API for matching elastic constants, **Then** the output CSV contains at least 30 rows with both `yield_strength_MPa` and `shear_modulus_GPa` populated. If 20 <= rows < 30, a warning is logged.
2. **Given** a composition with no matching DFT data in the Materials Project, **When** the system attempts to merge, **Then** that specific row is excluded from the final dataset with a logged warning, ensuring no null values propagate to the model.
3. **Given** a composition with multiple polymorphs in the database, **When** the system filters for BCC stability, **Then** only the entry with the BCC crystal structure (space group 229 or equivalent) is retained.

---

### User Story 2 - Predictive Modeling and Baseline Comparison (Priority: P2)

As a data scientist, I need to train a Random Forest regressor using both composition features and DFT elastic descriptors, and compare its performance against a composition-only baseline, so that I can quantify the added predictive value of atomic-scale physics.

**Why this priority**: This directly addresses the research question by testing the hypothesis that DFT descriptors improve prediction. It requires the dataset from US-1 and produces the primary statistical evidence (R², MAE) needed to validate the gap analysis.

**Independent Test**: The system can be tested by running the training pipeline with 5-fold cross-validation and verifying that the Random Forest model (with DFT features) achieves a statistically significant reduction in Mean Absolute Error compared to the composition-only baseline, as measured by a paired t-test (p < 0.05).

**Acceptance Scenarios**:

1. **Given** the merged dataset from US-1, **When** the Random Forest model is trained with 5-fold cross-validation, **Then** the model reports an R² score and Mean Absolute Error (MAE) for each fold.
2. **Given** the same dataset, **When** a composition-only baseline model is trained, **Then** the baseline's MAE is recorded for direct comparison.
3. **Given** the performance metrics from both models, **When** a paired t-test is performed on the fold-wise errors, **Then** the p-value is calculated and reported to determine if the DFT-enhanced model is significantly better.

---

### User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

As a domain expert, I need to view permutation importance rankings and a sensitivity analysis of the shear modulus threshold, so that I can understand which atomic-scale properties drive the predictions and ensure the model is robust to parameter variations.

**Why this priority**: This satisfies the methodological soundness requirement for "threshold justification & sensitivity analysis" and "measurement validity." It moves beyond simple prediction to explainability, ensuring the findings are scientifically defensible.

**Independent Test**: The system can be tested by generating a permutation importance plot and a sensitivity analysis report showing how the model's MAE changes when the shear modulus threshold is swept across a defined range, confirming the results are not artifacts of a single arbitrary cutoff.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model, **When** permutation importance is calculated, **Then** the output lists the top 5 features with their importance scores, explicitly highlighting DFT descriptors (shear/bulk modulus).
2. **Given** the feature engineering threshold for including the DFT descriptor (e.g., minimum shear modulus value), **When** the sensitivity analysis sweeps this threshold across values {0.01, 0.05, 0.1} relative to the mean shear modulus, **Then** the system reports the variation in MAE and R² for each sweep value.
3. **Given** the final model, **When** a Permutation Importance Stability analysis is run (10 bootstrapped samples), **Then** the report confirms that the standard deviation of importance scores for key DFT descriptors is < 0.05, indicating stable feature contributions.

### Edge Cases

- What happens when the Materials Project API returns a 404 or rate-limit error for a specific composition? (System should retry 3 times with exponential backoff, then skip the entry and log the failure).
- How does the system handle compositions where the experimental yield strength is reported as a range (e.g., "200-250 MPa")? (System should take the midpoint value and flag the row in a "uncertainty" column).
- What if the merged dataset contains fewer than 20 samples after filtering for BCC stability? (System should halt execution and raise a critical error: "Insufficient sample size for statistical power; minimum 20 samples required").

## Requirements

### Functional Requirements

- **FR-001**: System MUST download experimental yield strength and composition data for BCC Fe-alloys from MatNavi or NIST public repositories in CSV format. (See US-1)
- **FR-002**: System MUST query the Materials Project API to retrieve pre-computed DFT elastic constants (bulk modulus, shear modulus) for compositions matching the experimental dataset. (See US-1)
- **FR-003**: System MUST merge the experimental and computational datasets on chemical formula, filtering exclusively for BCC structure stability. (See US-1)
- **FR-004**: System MUST train a Random Forest regressor (scikit-learn) using both composition features and DFT descriptors as inputs, utilizing 5-fold cross-validation. (See US-2)
- **FR-005**: System MUST evaluate model performance using R² and Mean Absolute Error, and perform a paired t-test on the fold-wise errors to compare the DFT-enhanced model against the composition-only baseline, requiring p < 0.05 for significance. (See US-2)
- **FR-006**: System MUST apply permutation importance analysis and SHAP values to quantify the contribution of DFT descriptors versus composition features. (See US-3)
- **FR-007**: System MUST perform a sensitivity analysis sweeping the feature inclusion threshold for DFT descriptors over a concrete set (e.g., {0.01, 0.05, 0.1} relative to mean shear modulus) and report the variation in MAE and R². (See US-3)
- **FR-008**: System MUST calculate and report Permutation Importance Stability (standard deviation across 10 bootstrapped samples) to diagnose feature reliability, ensuring the standard deviation of key DFT descriptor importance is < 0.05. (See US-3)

### Key Entities

- **AlloyComposition**: Represents a specific BCC iron alloy, containing attributes for chemical formula, elemental percentages, and crystal structure tag.
- **ExperimentalProperty**: Represents the measured macroscopic yield strength (in MPa) and associated metadata (source, temperature, testing method).
- **DFTDescriptor**: Represents the computed atomic-scale properties (bulk modulus, shear modulus in GPa) derived from Density Functional Theory.
- **ModelPerformance**: Represents the statistical metrics (R², MAE, p-value) resulting from the cross-validation and significance testing.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation strength between DFT-derived shear modulus and experimental yield strength is measured against a threshold of Pearson r > 0.5 with p < 0.05. (See FR-005)
- **SC-002**: The predictive accuracy (MAE) of the Random Forest model with DFT descriptors is measured against the composition-only baseline model. (See FR-004, FR-005)
- **SC-003**: The statistical significance of the performance improvement (p-value from paired t-test on fold-wise errors) is measured against the threshold of 0.05 to validate predictive utility. (See FR-005)
- **SC-004**: The model's robustness is measured by the variation in MAE and R² across the sensitivity analysis sweep (thresholds {0.01, 0.05, 0.1}). (See FR-007)
- **SC-005**: The stability of feature importance is measured by the standard deviation of Permutation Importance scores across 10 bootstrapped samples, requiring a value < 0.05. (See FR-008)

## Assumptions

- The Materials Project API provides pre-computed DFT elastic constants for the majority of binary and ternary BCC iron alloys present in the MatNavi/NIST experimental datasets without requiring on-the-fly DFT calculations.
- The experimental yield strength data in public repositories is reported in a consistent unit (MPa) or can be reliably converted to MPa.
- The "BCC structure stability" filter can be accurately determined by matching space group numbers (e.g., 229) or crystal system tags available in the Materials Project metadata.
- The GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) is sufficient to load the merged dataset (expected < 1 GB) and train a Random Forest model with 5-fold cross-validation within the 6-hour limit.
- The dataset size, after merging and filtering, will exceed the minimum sample size (n > 20) required for valid statistical inference and cross-validation.
- The relationship between elastic constants and yield strength is primarily associational; no causal claims are made regarding the effect of DFT descriptors on yield strength without randomization.