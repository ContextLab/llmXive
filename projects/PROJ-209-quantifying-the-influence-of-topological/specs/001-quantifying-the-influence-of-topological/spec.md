# Feature Specification: Quantifying the Influence of Topological Defects on 2D Material Properties

**Feature Branch**: `001-quantify-defect-influence`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How do specific topological defects (e.g., dislocations, grain boundaries) in atomically thin materials such as graphene and MoS₂ quantitatively alter their electronic conductivity, Young's modulus, and fracture strength?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Synthetic Generation (Priority: P1)

The research team MUST be able to download pre-computed DFT structures of pristine graphene and MoS₂ from the Materials Project API, and if the primary high-throughput defect dataset is missing or invalid, generate a synthetic dataset with physically constrained properties (defect density, conductivity, elastic tensor) to proceed with analysis **ONLY for development and testing purposes**. The scientific analysis MUST halt if the primary real dataset is not available.

**Why this priority**: Without access to foundational structures and a valid dataset (real), no statistical modeling or analysis can proceed. This is the prerequisite for all downstream work. Synthetic data is strictly for pipeline testing.

**Independent Test**: Can be fully tested by successfully downloading pristine structures, attempting to parse the defect dataset (or generating synthetic data if missing for testing), and verifying that all required fields (defect type, defect density, conductivity, elastic tensor, fracture energy) are present and non-null in the resulting dataset.

**Acceptance Scenarios**:

1. **Given** the Materials Project REST API is accessible, **When** the script queries for pristine graphene and MoS₂ structures, **Then** at least 50 DFT-computed structures are retrieved with valid atomic coordinates and unit cell parameters.
2. **Given** the primary defect dataset source is missing or invalid, **When** the system invokes the synthetic data generator, **Then** a dataset of ≥ 100 entries is generated with defect density ∈ [non-negative, 0.1], and property values constrained by physical bounds (e.g., conductivity > 0, Young's modulus > 0). **Note**: This synthetic dataset is flagged for testing only and must not be used for final scientific conclusions.
3. **Given** a defect entry with missing fracture energy in the real dataset, **When** the system flags this entry, **Then** it is excluded from modeling and logged. No mock computation is performed.
4. **Given** the API fails after a limited number of retries with exponential backoff, **When** the system checks for a local cache, **Then** it loads the cached pristine structures; if no cache exists, the workflow halts with `[ERROR: API access unavailable and no cache present]`.

---

### User Story 2 - Statistical Modeling and Permutation Inference (Priority: P2)

The research team MUST be able to train random forest regressors for each target property (conductivity, Young's modulus, fracture strength), evaluate model performance using R² and MAPE against a null model baseline, and perform k-fold cross-validation (k=5) to assess model stability. Additionally, the team MUST generate p-values for feature importance via permutation testing (N=1000 permutations) to enable valid Benjamini-Hochberg FDR control.

**Why this priority**: This is the core analytical work that directly addresses the research question. Without reliable regression models and valid statistical inference (via permutation testing), no quantitative defect-property relationships can be established.

**Independent Test**: Can be fully tested by training the random forest models on a random split (80/20, seed=42), evaluating on the test split, and reporting R² and MAPE for all three target properties, including a comparison against a null model (mean prediction).

**Acceptance Scenarios**:

1. **Given** a normalized dataset with defect descriptors and property targets, **When** the random forest regressor is trained, **Then** the model reports R² and MAPE for all three target properties; if R² > (R²_null + a meaningful improvement threshold) for at least one property, the result is flagged as high-confidence.
2. **Given** k=5 cross-validation folds, **When** the model is evaluated across all folds, **Then** the standard deviation of R² across folds is reported; values > 0.1 indicate high variance requiring sensitivity analysis.
3. **Given** multiple hypothesis tests (one per target property), **When** statistical significance is assessed, **Then** p-values are generated via permutation testing (N=1000 permutations) of feature importance scores, and a False Discovery Rate (FDR) control using the Benjamini-Hochberg procedure is applied to control FDR at q ≤ 0.05 globally across all features and properties.
4. **Given** an independent hold-out set (distinct split of the same high-fidelity dataset), **When** the final model is evaluated, **Then** performance is reported on this independent set to validate predictive power. Validation against a distinct physics engine (e.g., DFTB+) is NOT permitted.

---

### User Story 3 - Validation, Sensitivity Analysis, and Reproducibility (Priority: P3)

The research team MUST be able to conduct permutation importance analysis to identify influential defect descriptors, perform sensitivity analysis on any decision thresholds by sweeping cutoffs over a data-derived set, and package the entire workflow in a reproducible Jupyter notebook that runs within a time-constrained GitHub Actions job. The team MUST also generate a Validation Report documenting the absence of external data if no such dataset exists.

**Why this priority**: This ensures methodological soundness (threshold justification, collinearity diagnostics) and reproducibility, which are required for peer review and downstream validation.

**Independent Test**: Can be fully tested by running the complete notebook end-to-end on a CPU-only runner, verifying that all analyses complete within 6 hours and the sensitivity analysis produces a table showing how R² and MAPE vary across the swept thresholds.

**Acceptance Scenarios**:

1. **Given** a trained random forest model, **When** permutation importance stability is computed, **Then** the top influential defect descriptors are identified and ranked, with stability metrics reported.
2. **Given** any decision cutoff introduced in the analysis (e.g., defect density threshold for "high" vs "low" defect samples), **When** sensitivity analysis is performed, **Then** the cutoff is swept over a data-derived set (deciles of observed density) and the resulting change in R² and MAPE are reported.
3. **Given** the GitHub Actions free-tier runner (CPU, ~7 GB RAM, ≤6 h), **When** the full workflow is executed, **Then** all steps complete successfully with total runtime ≤ 6 hours.
4. **Given** no external validation dataset exists, **When** the validation step is executed, **Then** a `Validation_Report.json` is generated with `status: NO_EXTERNAL_DATA` and `method: internal_only`.

---

### Edge Cases

- **Missing Key Variables**: If a variable is missing from the dataset, the system MUST flag the entry as `[MISSING: requires exclusion]` and exclude it from modeling. No mock computation is performed. The system MUST verify that the log entry count matches the number of excluded entries.
- **Undefined Defect Density**: Filter out entries with defect density ≤ 0 or NaN before modeling; log count of filtered entries.
- **API Failure**: The system MUST implement exponential backoff with a maximum of 3 retries when accessing the Materials Project REST API. If all retries fail, the system MUST switch to a cached local copy of the pristine structures (graphene and MoS₂) if available; if no cache exists, the workflow MUST halt and report `[ERROR: API access unavailable and no cache present]`.
- **Collinearity**: Compute Permutation Importance Stability; if stability metrics indicate high variance due to correlated features (VIF > 5), the system MUST report the collinearity and perform a sensitivity analysis comparing models with and without the correlated feature, rather than automatically excluding it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download pre-computed DFT structures from Materials Project REST API for pristine graphene and MoS₂ (See US-1)
- **FR-002**: System MUST parse the high-throughput defect dataset and extract defect type, defect density, and geometric descriptors for each entry. Missing values MUST be flagged as `[MISSING: requires exclusion]` and entries excluded. No mock computation is permitted (See US-1)
- **FR-003**: System MUST normalize all property values by pristine reference values (σ₀, E₀, σ_f₀) to compute relative changes (Δσ/σ₀, ΔE/E₀, Δσ_f/σ_f₀). If pristine reference values are missing, the entry MUST be excluded from normalization and logged (See US-2)
- **FR-004**: System MUST train random forest regressors for each target property with /20 train/test split (seed=42) and k=5 cross-validation (See US-2)
- **FR-005**: System MUST apply False Discovery Rate (FDR) control using the Benjamini-Hochberg procedure when assessing statistical significance across multiple hypothesis tests (See US-2)
- **FR-006**: System MUST compute permutation importance stability to rank defect descriptor influence on each target property (See US-3)
- **FR-007**: System MUST perform sensitivity analysis sweeping any decision cutoff over deciles of observed density and report how R² and MAPE vary (See US-3)
- **FR-008**: System MUST compute Permutation Importance Stability for all predictor pairs and flag collinearity if VIF > 5; if flagged, the system MUST report the collinearity and perform a sensitivity analysis comparing models with and without the correlated feature (See US-3)
- **FR-009**: System MUST attempt to validate predictions against an external dataset (e.g., experimental data or a distinct DFT dataset with different functionals). If no such public dataset exists for these specific defect configurations, the system MUST generate a `Validation_Report.json` with `status: NO_EXTERNAL_DATA` and `method: internal_only` (See US-3)
- **FR-010**: System MUST generate a synthetic dataset with physically constrained properties (defect density ∈ [0.0, 0.1], property bounds) if the primary defect dataset source is missing or invalid, strictly for development and testing purposes. This data MUST NOT be used for scientific conclusions (See US-1)
- **FR-011**: System MUST generate p-values for feature importance via permutation testing (N=1000 permutations, stratified by defect type) before applying Benjamini-Hochberg FDR control (See US-2)
- **FR-012**: System MUST evaluate the final model performance on an independent hold-out set (distinct split of the same high-fidelity dataset) to validate predictive power (See US-2)
- **FR-013**: System MUST control for confounding by stratifying the dataset by 'synthesis method' or 'grain size' (if available) and reporting results per stratum, or including these as covariates in the model. If these fields are unavailable, the system MUST log a warning and proceed without stratification (See US-2)

### Key Entities *(include if data)*

- **DefectEntry**: A single record from the dataset (real or synthetic) containing defect type (dislocation, grain boundary, vacancy, substitution), defect density (fraction of atoms), and geometric descriptors (e.g., grain-boundary tilt angle). Optional fields: `synthesis_method`, `grain_size`.
- **MaterialProperty**: A computed physical property for a given structure, including electronic conductivity (derived via BoltzTraP if only band gaps are available), elastic tensor components, and fracture energy
- **RegressionModel**: A trained random forest regressor mapping defect descriptors to a single normalized target property (Δσ/σ₀, ΔE/E₀, or Δσ_f/σ_f₀)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: All required variables are either present or successfully flagged as missing (See US-1)
- **SC-002**: Model predictive performance is measured against held-out test set using R² and MAPE; results are reported for all three target properties and compared against a null model baseline (See US-2)
- **SC-003**: Cross-validation stability is measured by standard deviation of R² across k=5 folds; values > 0.1 are reported as high variance (See US-2)
- **SC-004**: Multiple-comparison control is measured by applying Benjamini-Hochberg FDR correction to p-values generated via permutation testing (N=1000 permutations) to control FDR at q ≤ 0.05 across all hypothesis tests (See US-2)
- **SC-005**: Sensitivity analysis completeness is measured by reporting R² and MAPE variation across the swept cutoff set (deciles) (See US-3)
- **SC-006**: Compute feasibility is measured by total runtime on GitHub Actions free-tier runner; must complete within 6 hours with ≤ 7 GB RAM and no GPU (See US-3)
- **SC-007**: External validation is measured by the presence of a `Validation_Report.json`; if no external data exists, the report MUST explicitly document the absence and confirm internal validation was used (See US-3)

## Assumptions

- The primary defect dataset source (if real) contains all required variables: defect type, defect density, electronic conductivity (or band structure for BoltzTraP derivation), elastic tensor, and fracture energy for graphene and MoS₂ structures. If missing, the entry is excluded.
- The Materials Project REST API provides stable access to pre-computed DFT structures of pristine graphene and MoS₂ with valid atomic coordinates and unit cell parameters.
- A local cache of pristine structures is available if the API fails and no cache is present, the workflow halts.
- The random forest regressor implementation (scikit-learn) runs efficiently on CPU-only hardware without requiring GPU acceleration or 8-bit quantization.
- The dataset size fits within available system RAM and disk capacity; if larger, sampling or subset selection is applied to ensure CPU-only feasibility.
- All statistical inferences are framed as ASSOCIATIONAL (not causal) since the data is observational with no random assignment of defect types.
- The GitHub Actions free-tier runner provides consistent CPU cores, ~7 GB RAM, and ~GB disk for the full 6-hour job window.
- Electronic conductivity is derived from band structure data using the Boltzmann transport equation (BoltzTraP) if not directly provided in the dataset.
- Synthetic data is strictly for testing the pipeline and is excluded from all scientific conclusions.