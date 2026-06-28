# Feature Specification: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Feature Branch**: `001-predict-poissons-ratio`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How does the concentration of specific alloying elements (e.g., Cu, Mg, Si, Zn) influence the Poisson's ratio of monolithic aluminum alloys?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Extraction and Filtering (Priority: P1)

The researcher MUST be able to download compositional and property data for aluminum alloys from public materials databases (Materials Project and NIST Materials Data Repository), then filter to monolithic aluminum alloys with reported Poisson's ratio, Young's modulus, and elemental composition.

**Why this priority**: This is the foundational step; without valid input data, no modeling or analysis is possible. It represents the earliest deliverable that provides research value by establishing the dataset.

**Independent Test**: Can be fully tested by running the data extraction script against the source databases and verifying the filtered dataset contains ≥50 alloy entries with complete composition and property records.

**Acceptance Scenarios**:

1. **Given** the Materials Project and NIST repositories are accessible, **When** the extraction script queries for aluminum alloys, **Then** the script downloads raw data containing composition and property fields without authentication errors.
2. **Given** raw data is downloaded, **When** the filtering step runs, **Then** only monolithic (non-composite) aluminum alloys with non-missing Poisson's ratio, Young's modulus, and elemental composition remain in the filtered dataset.
3. **Given** filtered data exists, **When** unit consistency checks run, **Then** all elastic constants are normalized to GPa and composition values are expressed as atomic fractions summing to 1.0.

---

### User Story 2 - Regression Model Training and Validation (Priority: P2)

The researcher MUST be able to train a Random Forest regressor mapping elemental atomic fractions to Poisson's ratio, perform 5-fold cross-validation, and evaluate performance on a held-out test set.

**Why this priority**: This is the core analytical step that addresses the research question. It delivers the predictive model and generalizability estimate required to claim gap-filling value.

**Independent Test**: Can be fully tested by training the model on the filtered dataset, running 5-fold cross-validation, and verifying the mean absolute error is ≤0.02 on held-out data.

**Acceptance Scenarios**:

1. **Given** the filtered dataset exists, **When** feature vectors are constructed from atomic fractions of Cu, Mg, Si, Zn, and Mn, **Then** each row contains exactly 5 numeric predictors summing to ≤1.0 (allowing for Al as the balance).
2. **Given** feature vectors and target values exist, **When** the Random Forest regressor trains with 5-fold cross-validation, **Then** the cross-validated mean absolute error is computed and logged.
3. **Given** the trained model exists, **When** predictions are made on a [deferred] held-out test set, **Then** the test-set MAE is computed and reported separately from cross-validation metrics.

---

### User Story 3 - Feature Importance and Associational Interpretation (Priority: P3)

The researcher MUST be able to extract feature importance scores ranking alloying elements by their contribution to Poisson's ratio variance, and frame all findings as associational (not causal) given the observational nature of the dataset.

**Why this priority**: This delivers the scientific insight (which elements matter most) while maintaining methodological integrity by avoiding causal claims unsupported by randomization.

**Independent Test**: Can be fully tested by running the feature importance extraction and verifying the output contains ranked elements with non-zero importance scores and an associational framing statement.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model exists, **When** feature importance is extracted, **Then** each alloying element (Cu, Mg, Si, Zn, Mn) receives a numeric importance score summing to 1.0 across all elements.
2. **Given** feature importance results exist, **When** the results are documented, **Then** the documentation explicitly states that relationships are associational (not causal) due to observational data without random assignment.
3. **Given** the importance rankings exist, **When** the researcher reviews them, **Then** the top 2 elements by importance are identified and their relative magnitude compared (e.g., "Cu importance is 2× Mg importance").

---

### Edge Cases

- What happens when the Materials Project or NIST repository returns zero aluminum alloy entries with Poisson's ratio? The pipeline MUST halt with a clear error message and not proceed to modeling.
- How does the system handle entries where atomic fractions do not sum to 1.0 (e.g., due to trace elements)? The system MUST normalize fractions proportionally or exclude the entry with a log warning.
- What happens when cross-validation MAE exceeds 0.05 (indicating poor model fit)? The system MUST flag this as a methodological concern and record it in the results documentation without suppressing the finding.
- How does the system handle collinearity between alloying elements (e.g., Cu and Mg often co-occur in specific alloy series)? The system MUST compute variance inflation factors (VIF) and report if any predictor has VIF >5.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw compositional and property data from Materials Project and NIST Materials Data Repository for aluminum alloys (See US-1)
- **FR-002**: System MUST filter the dataset to monolithic aluminum alloys with non-missing Poisson's ratio, Young's modulus, and elemental composition for Cu, Mg, Si, Zn, and Mn (See US-1)
- **FR-003**: System MUST normalize all elastic constants to GPa and express composition as atomic fractions summing to 1.0 (See US-1)
- **FR-004**: System MUST train a Random Forest regressor mapping 5-element atomic fractions to Poisson's ratio with 5-fold cross-validation (See US-2)
- **FR-005**: System MUST compute and log test-set mean absolute error on a [deferred] held-out validation split (See US-2)
- **FR-006**: System MUST extract feature importance scores for each alloying element and rank them by contribution to variance (See US-3)
- **FR-007**: System MUST compute variance inflation factors (VIF) for all predictors and flag any with VIF >5 (See US-3)
- **FR-008**: System MUST frame all predictive findings as associational (not causal) in the output documentation (See US-3)

### Key Entities

- **AlloyRecord**: A single aluminum alloy entry containing elemental composition (Cu, Mg, Si, Zn, Mn atomic fractions), Poisson's ratio, and Young's modulus (GPa)
- **ModelMetrics**: Cross-validation MAE, test-set MAE, and feature importance scores for the trained Random Forest regressor
- **CollinearityDiagnostic**: Variance inflation factor (VIF) values for each predictor and a pass/fail flag based on threshold VIF >5

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the Materials Project and NIST repository query results (See US-1)
- **SC-002**: Model predictive accuracy (MAE) is measured against the [deferred] held-out test set (See US-2)
- **SC-003**: Feature importance ranking is measured against the trained Random Forest model's internal gain-based importance scores (See US-3)
- **SC-004**: Collinearity risk is measured against variance inflation factor (VIF) computed for each predictor (See US-3)
- **SC-005**: Methodological framing is measured against the presence of explicit associational (not causal) language in all result statements (See US-3)

## Assumptions

- The Materials Project and NIST Materials Data Repository APIs are publicly accessible without authentication for the aluminum alloy subset required for this analysis.
- The filtered dataset will contain ≥50 alloy entries with complete composition and Poisson's ratio data, enabling 5-fold cross-validation with ≥10 samples per fold.
- The Random Forest model will run on CPU-only infrastructure (2 cores, 7 GB RAM) within 6 hours for the expected dataset size (<1000 entries).
- No GPU or CUDA acceleration is available or required for the scikit-learn Random Forest implementation on this dataset scale.
- The dataset contains all required variables (Poisson's ratio, Young's modulus, Cu, Mg, Si, Zn, Mn concentrations); any missing variables will be flagged as [NEEDS CLARIFICATION] during data extraction.
- The observational nature of the dataset means all findings will be framed as associational; no randomization or identification strategy is available for causal claims.
- Multiple-comparison correction is not required for the primary analysis since the research question focuses on a single outcome (Poisson's ratio) rather than multiple hypothesis tests.
- The 0.02 MAE target from the idea is treated as the success threshold; if the model exceeds this, the result will be documented as a limitation rather than suppressing the finding.
- The 5-element feature set (Cu, Mg, Si, Zn, Mn) captures the major alloying elements for standard aluminum series; trace elements are excluded as their concentrations are typically <1 wt%.
