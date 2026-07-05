# Feature Specification: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

**Feature Branch**: `001-predict-yield-strength-bcc`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory"

## User Scenarios & Testing

### User Story 1 - Data Integration and Validation (Priority: P1)

As a materials researcher, I need to successfully merge experimental yield strength data from public repositories (MatNavi/NIST) with pre-computed DFT elastic constants from the Materials Project API, so that I can establish a unified dataset linking atomic-scale properties to macroscopic strength.

**Why this priority**: Without a validated, merged dataset containing both the predictor (DFT elastic constants) and the outcome (experimental yield strength), no modeling or analysis can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: The system can be tested by executing the data ingestion script and verifying that the resulting merged CSV contains at least 20 valid rows where both experimental yield strength and DFT shear modulus values are non-null. If the dataset contains fewer than 20 rows, the system MUST halt execution and raise the error `ERR_INSUFFICIENT_DATA`. No synthetic or mock data is permitted as a fallback. The system MUST halt if the Materials Project API or MatNavi/NIST repositories do not contain the specific BCC Fe-alloy data required.

**Acceptance Scenarios**:

1. **Given** a list of BCC iron alloy compositions from MatNavi, **When** the system queries the Materials Project API for matching elastic constants, **Then** the output CSV contains at least 20 rows with both `yield_strength_MPa` and `shear_modulus_GPa` populated. If rows < 20, the system halts with `ERR_INSUFFICIENT_DATA`.
2. **Given** a composition with no matching DFT data in the Materials Project, **When** the system attempts to merge, **Then** that specific row is excluded from the final dataset with a logged warning, ensuring no null values propagate to the model. If the total count of valid rows falls below 20, the system halts.
3. **Given** a composition with multiple polymorphs in the database, **When** the system filters for BCC stability, **Then** only the entry with the BCC crystal structure (space group 229 or equivalent) is retained.
4. **Given** the merged dataset, **When** the row count is evaluated, **Then** if count < 20, the system halts with `ERR_INSUFFICIENT_DATA`.

---

### User Story 2 - Predictive Modeling and Baseline Comparison (Priority: P2)

As a data scientist, I need to train a Random Forest regressor using both composition features and DFT elastic descriptors, and compare its performance against a composition-only baseline, so that I can quantify the added predictive value of atomic-scale physics.

**Why this priority**: This directly addresses the research question by testing the hypothesis that DFT descriptors improve prediction. It requires the dataset from US-1 and produces the primary statistical evidence (R², MAE) needed to validate the gap analysis.

**Independent Test**: The system can be tested by running the training pipeline with 5-fold cross-validation and verifying that the system successfully calculates and reports the Mean Absolute Error (MAE) for both the Random Forest model (with DFT features) and the composition-only baseline, and performs a paired t-test on the fold-wise errors to calculate the p-value. The analysis must be capable of returning a null result if the real data does not support the hypothesis.

**Acceptance Scenarios**:

1. **Given** the merged dataset from US-1, **When** the Random Forest model is trained with 5-fold cross-validation, **Then** the system reports an R² score and Mean Absolute Error (MAE) for each fold.
2. **Given** the same dataset, **When** a composition-only baseline model is trained, **Then** the baseline's MAE is recorded for direct comparison.
3. **Given** the performance metrics from both models, **When** a paired t-test is performed on the fold-wise errors, **Then** the system calculates and reports the p-value.

---

### User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

As a domain expert, I need to view permutation importance rankings, TreeSHAP values, and a bootstrap stability analysis, so that I can understand which atomic-scale properties drive the predictions and ensure the model is robust to sample variations.

**Why this priority**: This satisfies the methodological soundness requirement for "threshold justification & sensitivity analysis" and "measurement validity." It moves beyond simple prediction to explainability, ensuring the findings are scientifically defensible.

**Independent Test**: The system can be tested by generating a permutation importance plot, a TreeSHAP summary plot, and a stability report showing the standard deviation of feature importance across 10 bootstrapped samples. The test passes if the report is generated and contains the required columns. This analysis is performed ONLY on the real merged dataset; if the dataset is insufficient, the system halts before this step.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model, **When** permutation importance and TreeSHAP values are calculated, **Then** the output lists the top 5 features with their importance scores, explicitly highlighting DFT descriptors (shear/bulk modulus).
2. **Given** the model, **When** a Bootstrap Stability analysis is run (sweeping sample size from 10 to 50), **Then** the system reports the standard deviation of importance scores for key DFT descriptors.
3. **Given** the final model, **When** a Permutation Importance Stability analysis is run (10 bootstrapped samples), **Then** the system reports if the standard deviation of importance scores for key DFT descriptors is < 0.05.

### Edge Cases

- What happens when the Materials Project API returns a 404 or rate-limit error for a specific composition? (System should retry 3 times with exponential backoff, then skip the entry and log the failure. If total valid rows < 20, halt).
- How does the system handle compositions where the experimental yield strength is reported as a range (e.g., "200-250 MPa")? (System should take the midpoint value and flag the row in a "uncertainty" column).
- What if the merged dataset contains fewer than 20 samples after filtering for BCC stability? (System MUST halt execution and raise a critical error: `ERR_INSUFFICIENT_DATA`).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download experimental yield strength and composition data for BCC Fe-alloys from MatNavi or NIST Materials Data Repository (verified sources) in CSV format. If no verified source contains the specific BCC Fe-alloy data, the system MUST halt. (See US-1)
- **FR-002**: System MUST query the Materials Project API to retrieve pre-computed DFT elastic constants (bulk modulus, shear modulus) for compositions matching the experimental dataset. If the merged dataset contains fewer than 20 valid rows, the system MUST halt and raise `ERR_INSUFFICIENT_DATA`. No synthetic or mock data is permitted as a fallback. This requirement enforces Constitution Principle VII: All elastic-constant descriptors MUST be obtained directly from the Materials Project API. (See US-1)
- **FR-003**: System MUST merge the experimental and computational datasets on chemical formula, filtering exclusively for BCC structure stability. (See US-1)
- **FR-004**: System MUST train a Random Forest regressor (scikit-learn) using both composition features and DFT descriptors as inputs, utilizing 5-fold cross-validation. (See US-2)
- **FR-005**: System MUST evaluate model performance using R² and Mean Absolute Error, and perform a paired t-test on the fold-wise errors to compare the DFT-enhanced model against the composition-only baseline, and report the resulting p-value. The analysis must be capable of returning a null result if the real data does not support the hypothesis. (See US-2)
- **FR-006**: System MUST apply permutation importance analysis and TreeSHAP values to quantify the contribution of DFT descriptors versus composition features. TreeSHAP is explicitly required for Random Forest models to ensure efficient and accurate interpretability on small datasets. (See US-3)
- **FR-007**: System MUST perform a Bootstrap Stability analysis by re-sampling the REAL dataset (n=10 to n=50) and reporting the standard deviation of feature importance scores for key DFT descriptors. This analysis is performed ONLY on real data; synthetic data is not permitted. (See US-3)
- **FR-008**: System MUST calculate and report the standard deviation of Permutation Importance scores across 10 bootstrapped samples to diagnose feature reliability. This analysis is performed ONLY on real data. (See US-3)
- **FR-009**: System MUST calculate and report the statistical power (1 - beta) of the paired t-test given the sample size and observed effect size. If power is < 0.8, the system MUST explicitly report this limitation in the final output. (See US-2)

### Key Entities

- **AlloyComposition**: Represents a specific BCC iron alloy, containing attributes for chemical formula, elemental percentages, and crystal structure tag.
- **ExperimentalProperty**: Represents the measured macroscopic yield strength (in MPa) and associated metadata (source, temperature, testing method).
- **DFTDescriptor**: Represents the computed atomic-scale properties (bulk modulus, shear modulus in GPa) derived from Density Functional Theory.
- **ModelPerformance**: Represents the statistical metrics (R², MAE, p-value) resulting from the cross-validation and significance testing.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system MUST calculate and report the Pearson correlation coefficient between DFT-derived shear modulus and experimental yield strength. (See FR-005)
- **SC-002**: The system MUST calculate and report the Mean Absolute Error (MAE) for both the Random Forest model with DFT descriptors and the composition-only baseline model. (See FR-004, FR-005)
- **SC-003**: The system MUST calculate and report the p-value from the paired t-test on fold-wise errors. (See FR-005)
- **SC-004**: The system MUST calculate and report the standard deviation of feature importance scores across the Bootstrap Stability analysis (n=10 to n=50). (See FR-007)
- **SC-005**: The system MUST calculate and report if the standard deviation of Permutation Importance scores across 10 bootstrapped samples is < 0.05. (See FR-008)
- **SC-006**: The system MUST verify and report the final row count of the merged dataset, passing if count >= 20 and halting with `ERR_INSUFFICIENT_DATA` if count < 20. (See FR-002)
- **SC-007**: The system MUST report the difference in MAE between the DFT-enhanced model and the composition-only baseline. (See FR-005)
- **SC-008**: The system MUST calculate and report the statistical power of the paired t-test, explicitly stating if power is < 0.8. (See FR-009)

## Assumptions

- The Materials Project API provides pre-computed DFT elastic constants for the majority of binary and ternary BCC iron alloys present in the MatNavi/NIST experimental datasets without requiring on-the-fly DFT calculations.
- The experimental yield strength data in public repositories is reported in a consistent unit (MPa) or can be reliably converted to MPa.
- The "BCC structure stability" filter can be accurately determined by matching space group numbers (e.g., 229) or crystal system tags available in the Materials Project metadata.
- The GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) is sufficient to load the merged dataset (expected < 1 GB) and train a Random Forest model with 5-fold cross-validation within the 6-hour limit.
- The dataset size, after merging and filtering, will exceed the minimum sample size (n >= 20) required for valid statistical inference and cross-validation. If this assumption is violated, the project halts as per FR-002. No synthetic data is generated to meet this threshold.
- The relationship between elastic constants and yield strength is primarily associational; no causal claims are made regarding the effect of DFT descriptors on yield strength without randomization.
- Synthetic data is explicitly FORBIDDEN as a fallback for data ingestion, modeling, or analysis. The system MUST halt if real data from verified sources is insufficient.