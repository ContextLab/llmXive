# Feature Specification: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Feature Branch**: `001-predict-tg-metallic-glasses`
**Created**: 2024-05-21
**Status**: Draft
**Input**: User description: "Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Validation (Priority: P1)

The system MUST load public metallic glass composition and Tg datasets, verify the presence of required compositional and thermal variables, and filter for valid records before any analysis begins.

**Why this priority**: Without verified data containing both composition and Tg, no modeling can occur. This is the foundational step for the research validity.

**Independent Test**: Can be fully tested by executing the data loading script and verifying the output dataframe contains ≥ 100 rows with non-null Tg and composition fields.

**Acceptance Scenarios**:

1. **Given** a raw dataset from Materials Project or Zenodo, **When** the ingestion script runs, **Then** records missing Tg or full composition are removed, and a log reports the retention rate.
2. **Given** a dataset with missing atomic property data, **When** the feature engineering step runs, **Then** records are flagged or imputed according to the defined strategy (listwise deletion).

---

### User Story 2 - Model Training and Feature Engineering (Priority: P2)

The system MUST compute atomic-scale descriptors (radius mismatch, electronegativity difference, VEC) and train a Gradient Boosting Regressor using 5-fold cross-validation within the compute budget.

**Why this priority**: This delivers the core predictive capability and feature importance analysis required to answer the research question.

**Independent Test**: Can be fully tested by running the training pipeline and confirming the model artifacts (pickle/JSON) contain performance metrics (R², MAE) and feature importances.

**Acceptance Scenarios**:

1. **Given** the validated dataset, **When** the training job executes, **Then** the total runtime does not exceed 6 hours on a CPU-only environment.
2. **Given** multiple alloy families, **When** the model is trained, **Then** the train/test split maintains stratification by alloy family to prevent family-specific bias.

---

### User Story 3 - Result Interpretation and Reporting (Priority: P3)

The system MUST generate reports that quantify feature importance and visualize non-linear relationships while explicitly framing findings as associational.

**Why this priority**: This delivers the scientific insight (which descriptors matter) and ensures methodological compliance (no causal overclaiming).

**Independent Test**: Can be fully tested by reviewing the generated report for the presence of partial dependence plots and explicit associational language disclaimers.

**Acceptance Scenarios**:

1. **Given** the trained model, **When** the report is generated, **Then** feature importance rankings are presented with 95% confidence intervals via bootstrapping.
2. **Given** the research findings, **When** the text is reviewed, **Then** no causal language (e.g., "causes", "determines") is used regarding the relationship between descriptors and Tg.

---

### Edge Cases

- What happens when the dataset contains < 50 records for a specific alloy family (stratification failure)?
- How does the system handle collinearity between atomic radius mismatch and valence electron concentration?
- What occurs if the Zenodo DOI provided in the idea is invalid or the dataset lacks Tg values?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load composition-Tg pairs and exclude records where Tg is missing or composition is incomplete (See US-1).
- **FR-002**: System MUST compute atomic descriptors (weighted mean radius, radius mismatch, electronegativity difference, VEC) using standard periodic table values (See US-2).
- **FR-003**: System MUST train a GradientBoostingRegressor with 5-fold cross-validation and optimize hyperparameters via grid search over ≤ 10 combinations (See US-2).
- **FR-004**: System MUST frame all output findings as ASSOCIATIONAL only, prohibiting causal claims (e.g., "influences" allowed, "causes" forbidden) (See US-3).
- **FR-005**: System MUST enforce a hard runtime limit of ≤ 6 hours and memory limit of ≤ 7 GB RAM during execution (See US-2).
- **FR-006**: System MUST perform a sensitivity analysis on the `max_depth` hyperparameter by sweeping values ∈ {3, 5, 7} and reporting R² variance (See US-2).
- **FR-007**: System MUST calculate Variance Inflation Factor (VIF) for all predictors and flag any with VIF > 5 for diagnostic review (See US-2).
- **FR-008**: System MUST apply False Discovery Rate (FDR) correction when testing significance of multiple feature correlations (See US-3).

### Key Entities

- **CompositionRecord**: Represents a single metallic glass entry; attributes include elemental fractions and Tg value.
- **DescriptorSet**: Represents computed atomic features for a composition; attributes include radius mismatch, VEC, electronegativity difference.
- **ModelArtifact**: Represents the trained regressor and metadata; attributes include hyperparameters, feature importances, and performance metrics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Test-set R² is measured against the baseline null model (mean prediction) (See US-2).
- **SC-002**: Feature importance stability is measured against 1000 bootstrapped resamples (See US-3).
- **SC-003**: Data completeness (records with Tg + composition) is measured against the raw downloaded dataset size (See US-1).
- **SC-004**: Computational resource usage (CPU time, RAM peak) is measured against the CI runner limits (2 cores, 7 GB) (See US-2).

## Assumptions

- Atomic property data (atomic radius, electronegativity, valence electron count) is available from a standard, open-source periodic table library (e.g., `mendeleev` or `pymatgen`).
- The public dataset provided by Materials Project or Zenodo contains sufficient records (≥ 100) to support a valid 80/20 train/test split.
- The specific Zenodo DOI `` in the idea is a placeholder and [NEEDS CLARIFICATION: which specific Zenodo dataset ID contains the Tg compilation?].
- The analysis relies on CPU-only execution; no GPU-accelerated libraries (e.g., CuPy, PyTorch with CUDA) are permitted.
- Alloy family labels (Zr-based, Pd-based, etc.) are available in the metadata or can be inferred from the primary element.
