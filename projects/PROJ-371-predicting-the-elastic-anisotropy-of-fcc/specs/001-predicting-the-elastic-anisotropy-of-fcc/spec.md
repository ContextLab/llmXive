# Feature Specification: Predicting the Elastic Anisotropy of FCC Metals from Composition

**Feature Branch**: `001-elastic-anisotropy`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting the Elastic Anisotropy of FCC Metals from Composition"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Feature Engineering (Priority: P1)

The researcher MUST be able to fetch elastic constant data from public databases (Materials Project, AFLOWlib) and compute compositional descriptors automatically without manual intervention.

**Why this priority**: Without clean, structured data linking composition to elastic tensors, no modeling can occur. This is the foundational dependency for all subsequent analysis.

**Independent Test**: Can be fully tested by running the data pipeline script against a static subset of known FCC entries and verifying the output CSV contains the required columns (C11, C12, C44, A1, descriptors).

**Acceptance Scenarios**:

1. **Given** a list of valid material IDs from Materials Project, **When** the script queries the API, **Then** the script returns elastic constants (C11, C12, C44) for at least 80% of requested IDs within 300 seconds.
2. **Given** a valid chemical formula, **When** the script computes descriptors, **Then** the output includes atomic radius variance, electronegativity standard deviation, and valence electron concentration with no null values.

---

### User Story 2 - Model Training and Validation (Priority: P2)

The researcher MUST be able to train regression models (Random Forest, Gradient Boosting, Linear) on the ingested data and evaluate performance using cross-validation.

**Why this priority**: This implements the core hypothesis test (can composition predict anisotropy?). It determines the scientific value of the project.

**Independent Test**: Can be fully tested by executing the training script on the preprocessed dataset and verifying the output JSON contains R², MAE, and RMSE metrics for each model type.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset split into 80/20 train/test sets, **When** the training script runs, **Then** it completes within 1 hour on a standard CPU environment without GPU acceleration.
2. **Given** a trained model, **When** evaluated on the held-out test set, **Then** the system outputs performance metrics (R², MAE, RMSE) for all three model types.

---

### User Story 3 - Physical Consistency and Reporting (Priority: P3)

The researcher MUST be able to verify that predictions adhere to physical bounds and generate a report highlighting feature importance and sensitivity analysis.

**Why this priority**: Ensures scientific validity. Predictions violating physical laws (e.g., negative anisotropy) invalidate the model regardless of statistical metrics.

**Independent Test**: Can be fully tested by running the validation script on the model predictions and verifying the report flags any values outside the theoretical range (0 < A₁ < 3).

**Acceptance Scenarios**:

1. **Given** a set of predicted anisotropy values, **When** the consistency check runs, **Then** it flags any prediction outside the range 0 < A₁ < 3 and logs the count.
2. **Given** the final model, **When** the report is generated, **Then** it includes a sensitivity analysis sweeping the outlier removal threshold over {2.5, 3.0, 3.5} standard deviations.

---

### Edge Cases

- What happens when the API returns missing elastic constants (e.g., C11 is null)? The system MUST skip the entry and log the ID.
- How does the system handle division by zero in A₁ calculation (C11 = C12)? The system MUST exclude the entry and log a warning.
- What happens if the dataset contains non-FCC phases? The system MUST filter entries based on crystal structure metadata before processing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch elastic constants (C11, C12, C44) from Materials Project and AFLOWlib APIs for identified FCC entries without requiring manual data entry (See US-1).
- **FR-002**: System MUST compute compositional descriptors (atomic radius variance, electronegativity variance, valence electron concentration) using standard periodic table values (See US-1).
- **FR-003**: System MUST execute all model training and inference using CPU-only resources (no GPU/CUDA) to ensure compatibility with free-tier CI runners (See US-2).
- **FR-004**: System MUST enforce associational framing in all output reports, explicitly stating that findings reflect correlations, not causal mechanisms (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis on the outlier removal threshold, sweeping values ∈ {2.5, 3.0, 3.5} standard deviations and reporting the variance in R² (See US-3).

### Key Entities

- **MaterialEntry**: Represents a single alloy composition with attributes: ID, Formula, C11, C12, C44, A1, Descriptors.
- **ModelRun**: Represents a training execution with attributes: ModelType, Hyperparameters, R², MAE, RMSE, Timestamp.
- **ValidationReport**: Represents the final output with attributes: PhysicalViolations, SensitivityResults, FeatureImportance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data coverage is measured against the expected dataset size to ensure sufficient power for regression analysis (See US-1).
- **SC-002**: Model predictive performance (R²) is measured against the hypothesis target of ≥ 0.5 to validate the composition-anisotropy relationship (See US-2).
- **SC-003**: Physical consistency is measured against the theoretical bound 0 < A₁ < 3, with ≤ 5% of predictions violating this range (See US-3).

## Assumptions

- Materials Project and AFLOWlib APIs provide public access to elastic constant tensors for single-phase FCC metals without requiring authentication tokens.
- The total dataset size (approx. 100 entries) will fit within 7 GB RAM and 14 GB disk constraints of the free-tier CI runner.
- Elemental properties (atomic radius, electronegativity) are available from a standard periodic table library (e.g., `mendeleev` or `pymatgen`) without external API calls.
- The data is observational; therefore, all statistical inferences regarding composition and anisotropy are framed as associational, not causal.
- The definition of "single-phase FCC" is consistent across both Materials Project and AFLOWlib metadata tags.
