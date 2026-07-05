# Feature Specification: Predicting the Glass Forming Region of Metallic Glass Alloys via Machine Learning

**Feature Branch**: `001-glass-forming-region`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting the Glass Forming Region of Metallic Glass Alloys via Machine Learning"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion & Descriptor Computation (Priority: P1)

The system ingests metallic alloy composition data from public repositories (Materials Project, Zenodo GFA-DB) and computes thermodynamic descriptors (mixing enthalpy, atomic size mismatch, valence electron concentration, electronegativity difference) for each sample.

**Why this priority**: This is the foundational data layer; without validated descriptors, no modeling can occur. It delivers the dataset required for all downstream research tasks.

**Independent Test**: Can be fully tested by running the data pipeline script on a sample subset and verifying the output CSV contains the required columns (composition, GFA label, ΔHmix, δ, VEC, Δχ) with no null values in predictor fields.

**Acceptance Scenarios**:

1. **Given** a valid composition file from the source, **When** the pipeline executes, **Then** thermodynamic descriptors are computed using standard elemental property tables.
2. **Given** a composition with missing elemental data, **When** the pipeline executes, **Then** the sample is flagged and excluded from the training set with a log entry.

---

### User Story 2 - Model Training & Cross-System Evaluation (Priority: P1)

The system trains Random Forest and Gradient Boosting classifiers on the computed descriptors, evaluating performance using stratified cross-validation and cross-system validation (distinct chemical families, e.g., Fe-based vs. Zr-based).

**Why this priority**: This addresses the core research question regarding generalization across alloy systems. It delivers the primary performance metrics (Accuracy, AUC).

**Independent Test**: Can be fully tested by running the training script and verifying that model artifacts (pkl files) and a performance report (JSON/CSV) are generated containing accuracy and AUC-ROC metrics.

**Acceptance Scenarios**:

1. **Given** the prepared dataset split into train/test, **When** the model trains, **Then** both Random Forest and Gradient Boosting models are fitted with hyperparameter grid search.
2. **Given** an Fe-based training set, **When** the model tests on a distinct alloy family (e.g., Zr-based), **Then** cross-system AUC is calculated and reported separately.

---

### User Story 3 - Methodological Validation & Sensitivity Analysis (Priority: P2)

The system performs collinearity diagnostics on predictors, executes a sensitivity analysis on classification thresholds, and ensures all findings are framed as associational rather than causal.

**Why this priority**: This ensures the research is methodologically defensible against panel review regarding inference framing, threshold robustness, and predictor independence.

**Independent Test**: Can be fully tested by verifying the output report includes a collinearity matrix (VIF), a threshold sensitivity sweep table, and explicit "associational" language in the Conclusion section of the ValidationReport.

**Acceptance Scenarios**:

1. **Given** the trained model features, **When** diagnostics run, **Then** a Variance Inflation Factor (VIF) check is performed and logged (threshold VIF > 5 flagged).
2. **Given** the classification model, **When** sensitivity analysis runs, **Then** performance metrics are reported for thresholds {0.4, 0.5, 0.6}.

---

### Edge Cases

- What happens when the Zenodo GFA-DB record is temporarily unavailable? (System retries 3 times with exponential backoff, then fails gracefully with error code 503).
- How does system handle class imbalance (e.g., binary 'glass-forming' vs 'non-glass-forming' split)? (System applies stratified sampling and reports F1-score alongside accuracy).
- What happens if elemental property tables change? (System uses a fixed versioned snapshot of periodic table data).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load composition data from Materials Project or Zenodo GFA-DB and compute mixing enthalpy (ΔHmix), atomic size mismatch (δ), valence electron concentration (VEC), and electronegativity difference (Δχ) for every sample (See US-1).
- **FR-002**: System MUST process the dataset within a peak RAM usage of ≤7 GB on CPU-only runners; if the dataset exceeds this limit, the system MUST process data in chunks of ≤1000 samples sequentially (See US-1).
- **FR-003**: System MUST train Random Forest and Gradient Boosting classifiers using scikit-learn without GPU acceleration or CUDA dependencies (See US-2).
- **FR-004**: System MUST perform 5-fold stratified cross-validation and report accuracy and AUC-ROC metrics (See US-2).
- **FR-005**: System MUST execute a cross-system validation split between distinct chemical families (e.g., train on Fe-based, test on Zr-based) to assess transferability (See US-2).
- **FR-006**: System MUST perform a collinearity diagnostic (Variance Inflation Factor) on predictors and flag any VIF > 5 in the report (See US-3).
- **FR-007**: System MUST execute a threshold sensitivity analysis sweeping classification cutoffs over {0.4, 0.5, 0.6} to verify robustness (See US-3).
- **FR-008**: System MUST explicitly label all model findings as "associational" in the Conclusion section of generated reports to reflect observational data limitations (See US-3).
- **FR-009**: System MUST implement a fallback chunking mechanism that processes data in batches of ≤1000 samples if the total dataset size exceeds available memory (See US-1).

### Key Entities *(include if feature involves data)*

- **AlloyComposition**: Represents a specific metallic alloy sample; key attributes include elemental fractions, GFA label (glass/non-glass), and computed descriptors (ΔHmix, δ, VEC, Δχ).
- **ModelArtifact**: Represents a trained classifier; key attributes include algorithm type (RF/GB), hyperparameters, and performance metrics.
- **ValidationReport**: Represents the output of the evaluation phase; key attributes include accuracy, AUC, VIF scores, threshold sensitivity tables, and the "associational" conclusion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Classification accuracy is measured against the held-out test set, targeting [deferred] (See US-2).
- **SC-002**: Cross-system transferability is measured against the AUC-ROC metric on the external alloy family, targeting [deferred] (See US-2).
- **SC-003**: Threshold sensitivity is measured by the variation in false-positive rates across the {0.4, 0.5, 0.6} sweep (See US-3).
- **SC-004**: Computational feasibility is measured by peak RAM usage, ensuring ≤7 GB during training (See US-1).
- **SC-005**: Predictor collinearity is measured by the maximum VIF score across all descriptors, ensuring the system reports any VIF > 5 (See US-3).

## Assumptions

- Public Zenodo GFA-DB record ID (XXXXX) remains accessible and provides labeled GFA data compatible with the Materials Project composition format.
- Elemental property tables (periodic table data) are static and available via local lookup or standard library without external API rate limits.
- GitHub Actions free-tier runners provide consistent Multi-core CPU performance and sufficient RAM availability for the duration of the job.
- The "glass-forming" label in the source datasets is binary (glass-forming vs. non-glass-forming) and does not require continuous conversion.
- Thermodynamic descriptors (ΔHmix, δ, VEC, Δχ) can be computed deterministically from elemental composition without requiring iterative simulation.
- No GPU acceleration is required; scikit-learn implementations of Random Forest and Gradient Boosting are sufficient for the dataset size.