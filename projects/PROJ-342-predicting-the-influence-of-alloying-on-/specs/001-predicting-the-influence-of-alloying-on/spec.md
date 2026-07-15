# Feature Specification: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Feature Branch**: `001-predict-tg-metallic-glasses`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Validation (Priority: P1)

The system MUST load public metallic glass composition and Tg datasets, verify the presence of required compositional and thermal variables, and filter for valid records before any analysis begins.

**Why this priority**: Without verified data containing both composition and Tg, no modeling can occur. This is the foundational step for the research validity.

**Independent Test**: Can be fully tested by executing the data loading script and verifying the output dataframe contains > 0 rows, no null Tg or composition fields remain, and a log reports the retention rate.

**Acceptance Scenarios**:

1. **Given** a raw dataset from Materials Project or Zenodo, **When** the ingestion script runs, **Then** records missing Tg or full composition are removed, and a log reports the retention rate.
2. **Given** a dataset with missing atomic property data, **When** the feature engineering step runs, **Then** records are flagged or imputed according to the defined strategy (listwise deletion).

---

### User Story 2 - Model Training, Feature Engineering, and Sensitivity Analysis (Priority: P2)

The system MUST compute atomic-scale descriptors (radius mismatch, electronegativity difference, VEC, and weighted mean radius for diagnostics), train a Gradient Boosting Regressor using Leave-One-Family-Out cross-validation, and perform a sensitivity analysis on hyperparameters to report performance variance.

**Why this priority**: This delivers the core predictive capability, feature importance analysis, and robustness verification required to answer the research question reliably.

**Independent Test**: Can be fully tested by running the training pipeline and confirming the model artifacts contain performance metrics (R², MAE), feature importances, a sensitivity analysis report, and a diagnostic log containing the weighted mean radius.

**Acceptance Scenarios**:

1. **Given** the validated dataset, **When** the training job executes, **Then** the total runtime does not exceed the allocated CI runner time budget (default 6h) on a CPU-only environment.
2. **Given** multiple alloy families, **When** the model is trained, **Then** the Leave-One-Family-Out split ensures no family appears in both training and test sets simultaneously.
3. **Given** the computed descriptors, **When** the feature engineering step runs, **Then** the 'weighted mean radius' is calculated and written to a diagnostic log for review.

---

### User Story 3 - Result Interpretation, Reporting, and Statistical Validation (Priority: P3)

The system MUST generate reports that quantify feature importance, visualize non-linear relationships, perform linear dependency analysis with FDR correction, and explicitly frame findings as associational.

**Why this priority**: This delivers the scientific insight (which descriptors matter), ensures methodological compliance (no causal overclaiming), and validates statistical rigor.

**Independent Test**: Can be fully tested by reviewing the generated report for the presence of partial dependence plots, a correlation matrix with FDR-corrected p-values, and the exact phrase: "These findings are associational only".

**Acceptance Scenarios**:

1. **Given** the trained model, **When** the report is generated, **Then** feature importance rankings are presented with 95% confidence intervals via bootstrapping.
2. **Given** the correlation matrix of predictors, **When** the statistical validation runs, **Then** p-values are adjusted using the Benjamini-Hochberg procedure at α ≤ 0.05.
3. **Given** the research findings, **When** the text is reviewed, **Then** no causal language (e.g., "causes", "determines") is used regarding the relationship between descriptors and Tg.

---

### Edge Cases

- What happens when the dataset contains < 50 records for a specific alloy family (stratification failure)?
- How does the system handle collinearity between atomic radius mismatch and valence electron concentration?
- What occurs if the Zenodo DOI provided in the idea is invalid or the dataset lacks Tg values?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load composition-Tg pairs from the 'Metallic Glass Database' (DOI: 10.5281/zenodo.10043838) compiled by Pauly et al. If this DOI is unavailable, the system MUST fall back to the 'MatNVP Metallic Glass' subset (DOI: 10.5281/zenodo.11023456). Records with missing Tg or incomplete composition MUST be excluded. (See US-1).
- **FR-002**: System MUST compute atomic descriptors: weighted mean radius (for diagnostic logging only), radius mismatch, electronegativity difference, and VEC using standard periodic table values. The 'weighted mean radius' MUST NOT be used as a predictor in the model. (See US-2).
- **FR-003**: System MUST train a GradientBoostingRegressor using Leave-One-Family-Out (LOFO) cross-validation to ensure generalization to unseen alloy families. Hyperparameters MUST be optimized via grid search over ≤ 10 combinations. (See US-2).
- **FR-004**: System MUST frame all output findings as ASSOCIATIONAL only, prohibiting causal claims (e.g., "influences" allowed, "causes" forbidden). (See US-3).
- **FR-005**: System MUST enforce a hard runtime limit of ≤ 6 hours and memory limit of ≤ 7 GB RAM, or complete within the allocated CI runner time budget if the environment differs. (See US-2).
- **FR-006**: System MUST perform a post-hoc sensitivity analysis on the `max_depth` hyperparameter of the best model from FR-003 by sweeping values ∈ {3, 5, 7} and reporting the statistical variance (σ²) of the R² scores across the sweep to verify model stability. (See US-2).
- **FR-007**: System MUST calculate Variance Inflation Factor (VIF) for all 3 model predictors (radius mismatch, electronegativity difference, VEC) and flag any with VIF > 5 for diagnostic review. The 'weighted mean radius' is excluded from this calculation. (See US-2).
- **FR-008**: System MUST apply False Discovery Rate (FDR) correction using the Benjamini-Hochberg procedure at α ≤ 0.05 when testing significance of multiple feature correlations to control false positives in linear dependency analysis. (See US-3).
- **FR-009**: System MUST calculate Pearson and Spearman correlation coefficients and p-values for all pairs of the 3 model predictors (radius mismatch, electronegativity difference, VEC) to support FR-008. (See US-3).

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
- **SC-004**: Computational resource usage (CPU time, RAM peak) is measured against the CI runner limits (a small number of cores, limited RAM) (See US-2).

## Assumptions

- Atomic property data (atomic radius, electronegativity, valence electron count) is available from a standard, open-source periodic table library (e.g., `mendeleev` or `pymatgen`).
- The public dataset provided by Materials Project or Zenodo contains sufficient records to support a valid Leave-One-Family-Out cross-validation.
- The analysis relies on CPU-only execution; no GPU-accelerated libraries (e.g., CuPy, PyTorch with CUDA) are permitted.
- Alloy family labels (Zr-based, Pd-based, etc.) are available in the metadata or can be inferred from the primary element.