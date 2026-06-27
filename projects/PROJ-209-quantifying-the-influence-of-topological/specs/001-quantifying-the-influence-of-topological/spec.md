# Feature Specification: Quantifying the Influence of Topological Defects on 2D Material Properties

**Feature Branch**: `001-quantify-defect-influence`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How do specific topological defects (e.g., dislocations, grain boundaries) in atomically thin materials such as graphene and MoS₂ quantitatively alter their electronic conductivity, Young's modulus, and fracture strength?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Defect Characterization (Priority: P1)

The research team MUST be able to download pre-computed DFT structures of pristine graphene and MoS₂, retrieve the high-throughput defect dataset from the supplementary material of *Unveiling the complex structure‑property correlation of defects in 2D materials*, and parse each defect entry to extract defect type, defect density, and geometric descriptors.

**Why this priority**: Without access to the foundational dataset and properly extracted features, no statistical modeling or analysis can proceed. This is the prerequisite for all downstream work.

**Independent Test**: Can be fully tested by successfully downloading the dataset, parsing at least 100 defect entries, and verifying that all required fields (defect type, defect density, conductivity, elastic tensor, fracture energy) are present and non-null.

**Acceptance Scenarios**:

1. **Given** the Materials Project REST API is accessible, **When** the script queries for pristine graphene and MoS₂ structures, **Then** at least 50 DFT-computed structures are retrieved with valid atomic coordinates and unit cell parameters.
2. **Given** the high-throughput defect dataset CSV/JSON files are available, **When** the parser processes the files, **Then** The majority of defect entries are successfully parsed with non-missing defect type and defect density values.
3. **Given** a defect entry with missing fracture energy, **When** the system flags this entry, **Then** it is either computed using DFTB+ (≤5 minutes on single CPU) or marked as `[MISSING: requires manual computation]`.

---

### User Story 2 - Statistical Modeling and Regression Analysis (Priority: P2)

The research team MUST be able to train random forest regressors for each target property (conductivity, Young's modulus, fracture strength), evaluate model performance using R² and MAPE, and perform k-fold cross-validation (k=5) to assess model stability.

**Why this priority**: This is the core analytical work that directly addresses the research question. Without reliable regression models, no quantitative defect-property relationships can be established.

**Independent Test**: Can be fully tested by training the random forest models on the [deferred] training split, evaluating on the [deferred] test split, and reporting R² ≥ 0.5 for at least one target property with MAPE ≤ 15%.

**Acceptance Scenarios**:

1. **Given** a normalized dataset with defect descriptors and property targets, **When** the random forest regressor is trained, **Then** the model achieves R² ≥ 0.5 on the held-out test set for at least one of the three target properties.
2. **Given** k=5 cross-validation folds, **When** the model is evaluated across all folds, **Then** the standard deviation of R² across folds is ≤ 0.1, indicating stable performance.
3. **Given** multiple hypothesis tests (one per target property), **When** statistical significance is assessed, **Then** a Bonferroni correction is applied to control family-wise error rate at α ≤ 0.05.

---

### User Story 3 - Validation, Sensitivity Analysis, and Reproducibility (Priority: P3)

The research team MUST be able to conduct permutation importance analysis to identify influential defect descriptors, perform sensitivity analysis on any decision thresholds by sweeping cutoffs over a concrete set (e.g., defect density ∈ {0.01, 0.05, 0.1}), and package the entire workflow in a reproducible Jupyter notebook that runs within a 6-hour GitHub Actions job.

**Why this priority**: This ensures methodological soundness (threshold justification, collinearity diagnostics) and reproducibility, which are required for peer review and downstream validation.

**Independent Test**: Can be fully tested by running the complete notebook end-to-end on a CPU-only runner, verifying that all analyses complete within 6 hours and the sensitivity analysis produces a table showing how headline rates vary across the swept thresholds.

**Acceptance Scenarios**:

1. **Given** a trained random forest model, **When** permutation importance is computed, **Then** the top 3 most influential defect descriptors are identified and ranked.
2. **Given** any decision cutoff introduced in the analysis (e.g., defect density threshold for "high" vs "low" defect samples), **When** sensitivity analysis is performed, **Then** the cutoff is swept over {0.01, 0.05, 0.1} and the resulting false-positive/false-negative rates are reported.
3. **Given** the GitHub Actions free-tier runner (2 CPU, ~7 GB RAM, ≤6 h), **When** the full workflow is executed, **Then** all steps complete successfully with total runtime ≤ 6 hours.

---

### Edge Cases

- What happens when the high-throughput defect dataset is missing key variables (e.g., fracture energy not provided)? → Flag as `[NEEDS CLARIFICATION: does dataset contain <variable>?]` and attempt DFTB+ computation; if that fails, mark as missing.
- How does system handle dataset entries with undefined defect density (e.g., 0 or NaN)? → Filter out entries with defect density ≤ 0 or NaN before modeling; log count of filtered entries.
- What happens when the Materials Project API rate limit is exceeded? → Implement exponential backoff with maximum 3 retries; if all fail, use cached local copy or mark as `[NEEDS CLARIFICATION: API access unavailable]`.
- How does system handle collinearity between predictors (e.g., defect density and grain-boundary tilt angle)? → Compute variance inflation factor (VIF); if VIF > 5, frame joint relationship as descriptive rather than claiming independent effects.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download pre-computed DFT structures from Materials Project REST API for pristine graphene and MoS₂ (See US-1)
- **FR-002**: System MUST parse the high-throughput defect dataset and extract defect type, defect density, and geometric descriptors for each entry (See US-1)
- **FR-003**: System MUST normalize all property values by pristine reference values (σ₀, E₀, σ_f₀) to compute relative changes (Δσ/σ₀, ΔE/E₀, Δσ_f/σ_f₀) (See US-2)
- **FR-004**: System MUST train random forest regressors for each target property with 80/20 train-test split and k=5 cross-validation (See US-2)
- **FR-005**: System MUST apply Bonferroni correction when assessing statistical significance across multiple hypothesis tests (See US-2)
- **FR-006**: System MUST compute permutation importance to rank defect descriptor influence on each target property (See US-3)
- **FR-007**: System MUST perform sensitivity analysis sweeping any decision cutoff over {0.01, 0.05, 0.1} and report how headline rates vary (See US-3)
- **FR-008**: System MUST compute variance inflation factor (VIF) for all predictor pairs and flag collinearity if VIF > 5 (See US-3)

### Key Entities *(include if feature involves data)*

- **DefectEntry**: A single record from the high-throughput dataset containing defect type (dislocation, grain boundary, vacancy, substitution), defect density (fraction of atoms), and geometric descriptors (e.g., grain-boundary tilt angle)
- **MaterialProperty**: A computed physical property for a given structure, including electronic conductivity, elastic tensor components, and fracture energy
- **RegressionModel**: A trained random forest regressor mapping defect descriptors to a single normalized target property (Δσ/σ₀, ΔE/E₀, or Δσ_f/σ_f₀)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the high-throughput defect dataset's documented variable inventory; all required predictors and outcomes must be present or flagged as `[NEEDS CLARIFICATION]` (See US-1)
- **SC-002**: Model predictive performance is measured against held-out test set using R² and MAPE; at least one target property must achieve R² ≥ 0.5 with MAPE ≤ 15% (See US-2)
- **SC-003**: Cross-validation stability is measured by standard deviation of R² across k=5 folds; must be ≤ 0.1 to indicate stable performance (See US-2)
- **SC-004**: Multiple-comparison control is measured by applying Bonferroni correction to family-wise error rate at α ≤ 0.05 across all hypothesis tests (See US-2)
- **SC-005**: Sensitivity analysis completeness is measured by reporting headline rate variation across the swept cutoff set {0.01, 0.05, 0.1} for any decision threshold introduced (See US-3)
- **SC-006**: Compute feasibility is measured by total runtime on GitHub Actions free-tier runner; must complete within 6 hours with ≤ 7 GB RAM and no GPU (See US-3)

## Assumptions

- The high-throughput defect dataset from *Unveiling the complex structure‑property correlation of defects in 2D materials* (arXiv:2212.02110v1) contains all required variables: defect type, defect density, electronic conductivity, elastic tensor, and fracture energy for graphene and MoS₂ structures
- The Materials Project REST API provides stable access to pre-computed DFT structures of pristine graphene and MoS₂ with valid atomic coordinates and unit cell parameters
- DFTB+ calculations (≤5 minutes per structure on single CPU) are computationally feasible as a fallback for missing property values in the high-throughput dataset
- The random forest regressor implementation (scikit-learn) runs efficiently on CPU-only hardware without requiring GPU acceleration or 8-bit quantization
- The dataset size fits within ~7 GB RAM and ~14 GB disk; if larger, sampling or subset selection is applied to ensure CPU-only feasibility
- All statistical inferences are framed as ASSOCIATIONAL (not causal) since the data is observational with no random assignment of defect types
- The GitHub Actions free-tier runner provides consistent 2 CPU cores, ~7 GB RAM, and ~14 GB disk for the full 6-hour job window
