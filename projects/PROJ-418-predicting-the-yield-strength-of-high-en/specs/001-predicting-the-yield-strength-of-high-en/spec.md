# Feature Specification: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

**Feature Branch**: `001-predict-hea-yield-strength`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Descriptor Engineering (Priority: P1)

Researcher downloads HEA composition and yield strength data from open repositories, calculates compositional descriptors (atomic size mismatch δ, electronegativity variance Δχ, valence electron concentration VEC, mixing entropy, melting temperature variance), and filters to single-phase alloys at room temperature.

**Why this priority**: Without validated input data and correctly calculated descriptors, no downstream modeling is possible. This forms the foundational dataset for all subsequent analysis.

**Independent Test**: Can be fully tested by executing the data pipeline and verifying that the system reports the count of available single-phase HEA compositions with complete descriptor values and yield strength measurements in a CSV file.

**Acceptance Scenarios**:

1. **Given** access to the NIST HEA database (primary test target) or Materials Project/Zenodo/figshare datasets, **When** the researcher runs the data acquisition script, **Then** a merged dataset is produced and the system reports the count of single-phase room-temperature HEA compositions. The system MUST support at least one of these sources.
2. **Given** elemental property data (atomic radii, electronegativity, valence electron counts), **When** the descriptor calculation module runs, **Then** each alloy composition has δ, Δχ, VEC, mixing entropy, and melting temperature variance computed with no missing values.
3. **Given** raw HEA data with phase and temperature annotations, **When** filtering criteria are applied, **Then** only single-phase alloys tested at room temperature (20-25°C) remain in the output dataset.

---

### User Story 2 - Model Training and Predictive Performance Evaluation (Priority: P2)

Researcher trains random forest and gradient boosting models using 5-fold cross-validation with hyperparameter tuning (100-200 trees for RF, 50-100 for GBM, depth ≤ 6), evaluates on a stratified 80/20 hold-out test set (seed=42), and compares R², MAE, and RMSE against a baseline Ordinary Least Squares (OLS) linear regression model on the same 5 descriptors.

**Why this priority**: The core predictive capability determines whether compositional descriptors carry sufficient signal for practical alloy screening. This delivers the primary quantitative result.

**Independent Test**: Can be fully tested by executing model training and evaluation scripts, then verifying that R², MAE, and RMSE values are recorded in a JSON report file at `output/metrics.json` with keys `R2`, `MAE`, `RMSE` for both tree-based models and the linear baseline on the held-out test set, and that the total runtime is ≤3 hours.

**Acceptance Scenarios**:

1. **Given** the prepared dataset with descriptors and yield strength values, **When** random forest and gradient boosting models are trained with 5-fold cross-validation (seed=42), **Then** both models complete within ≤3 hours on a CPU-only environment.
2. **Given** trained models, **When** evaluation runs on a stratified 80/20 hold-out test set (seed=42), **Then** the tree-based model's R² is compared against the OLS baseline R² to quantify improvement.
3. **Given** multiple model outputs, **When** performance metrics are compared, **Then** the best tree-based model's R², MAE, and RMSE are documented alongside the linear regression baseline for direct comparison.

---

### User Story 3 - Statistical Validation and Significance Reporting (Priority: P3)

Researcher performs permutation importance testing with 1000 permutations (seed=42), conducts bootstrap resampling for model stability (seed=42), applies multiple-comparison correction for the filtered set of descriptors (VIF < 10), conducts sensitivity analysis on the significance threshold (α ∈ {0.01, 0.05, 0.1}), and documents collinearity diagnostics among predictors.

**Why this priority**: Statistical rigor ensures findings are methodologically defensible and reproducible. This addresses the methodology panel's concerns about inference framing and threshold justification.

**Independent Test**: Can be fully tested by executing statistical validation scripts and verifying that permutation p-values, bootstrap confidence intervals, multiple-comparison corrected significance levels, and threshold sensitivity results are all recorded in the output report.

**Acceptance Scenarios**:

1. **Given** fitted models with descriptor importance scores, **When** permutation testing runs with 1000 permutations (seed=42), **Then** p-values are calculated for all descriptors.
2. **Given** ≥5 hypothesis tests across descriptors, **When** multiple-comparison correction applies (Bonferroni or Benjamini-Hochberg) to the set of descriptors with VIF < 10, **Then** corrected p-values are reported to control family-wise error rate.
3. **Given** the significance threshold α = 0.05 as the primary cutoff, **When** sensitivity analysis sweeps α ∈ {0.01, 0.05, 0.1}, **Then** the report documents how the count of significant descriptors and R² values vary across thresholds.

---

### Edge Cases

- What happens when the downloaded dataset contains <500 single-phase room-temperature HEA compositions? The pipeline flags this as a data limitation and reports the actual N achieved; the model proceeds with available data but notes reduced statistical power.
- How does the system handle missing elemental property values (e.g., electronegativity not available for a rare element)? The pipeline excludes compositions containing elements with incomplete property data and logs the count of excluded entries.
- What happens when descriptor collinearity exceeds VIF > 10? The system flags the collinear descriptor pair, reports the variance inflation factor, and recommends joint descriptive reporting rather than claims of independent predictive effects.
- How does the system handle yield strength values reported in different units (MPa vs. GPa)? The pipeline normalizes all yield strength values to MPa before model training, logging the conversion factor applied.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download HEA composition and yield strength data from at least one open repository (NIST HEA database as primary test target, or Materials Project, or Zenodo/figshare DOI), filter for single-phase room-temperature entries, and report the count of available entries; if count < 500, the system MUST flag a data limitation (See US-1)
- **FR-002**: System MUST calculate five compositional descriptors per alloy: atomic size mismatch δ, electronegativity variance Δχ, valence electron concentration VEC, mixing entropy, and melting temperature variance (See US-1)
- **FR-003**: System MUST filter the dataset to retain only single-phase high-entropy alloys tested at room temperature (20-25°C), excluding entries with missing yield strength values or non-standard testing conditions (See US-1)
- **FR-004**: System MUST train random forest (100-200 trees) and gradient boosting (50-100 trees) models with 5-fold cross-validation (seed=42), hyperparameter grid search constrained to depth ≤ 6, completing within ≤3 hours on CPU-only hardware (See US-2)
- **FR-005**: System MUST evaluate model performance on a stratified 80/20 hold-out test set (seed=42), reporting R², MAE, and RMSE for both tree-based models and a baseline Ordinary Least Squares (OLS) linear regression model on the same 5 descriptors (See US-2)
- **FR-006**: System MUST calculate permutation p-values for all descriptors using 1000 permutations (seed=42) by shuffling the target variable y to assess feature relevance (See US-3)
- **FR-007**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) ONLY to the filtered set of descriptors with VIF < 10 to control family-wise error rate (See US-3)
- **FR-008**: System MUST conduct sensitivity analysis on the significance threshold by sweeping α ∈ {0.01, 0.05, 0.1} and reporting how the count of significant descriptors and R² values vary (See US-3)
- **FR-009**: System MUST compute variance inflation factors (VIF) for each descriptor within the full multiple regression model and flag any VIF > 10; descriptors with VIF > 10 MUST be excluded from significance claims or reported as collinear (See US-3)
- **FR-010**: System MUST append a mandatory disclaimer string "Associational analysis only; no causal inference" to all generated plots and the final report summary (See US-3)
- **FR-011**: System MUST perform bootstrap resampling (1000 resamples, seed=42) of the full model to assess the stability of performance metrics and report 95% confidence intervals (See US-3)
- **FR-012**: System MUST generate a README.md file containing installation steps, usage instructions, and data source requirements (See US-1)
- **FR-013**: System MUST generate a quickstart.md file containing a step-by-step walkthrough of the pipeline execution (See US-1)

### Key Entities *(include if feature involves data)*

- **HEA Composition**: Represents a high-entropy alloy with key attributes including elemental fractions (atomic percent for each element), phase structure (single-phase designation), and testing temperature
- **Descriptor Set**: Represents the five compositional features calculated per alloy: δ (atomic size mismatch), Δχ (electronegativity variance), VEC (valence electron concentration), mixing entropy, and melting temperature variance
- **Yield Strength Measurement**: Represents the experimentally measured mechanical property with units standardized to MPa, including metadata for testing protocol and source repository

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Test-set R² is measured against the baseline OLS linear regression R² to quantify improvement from tree-based models (See US-2)
- **SC-002**: Descriptor correlation significance (p-values from permutation testing) is measured against the α = 0.05 threshold with multiple-comparison correction applied to the VIF-filtered set (See US-3)
- **SC-003**: Threshold sensitivity results are measured against the headline R² and significant descriptor count to quantify stability across α ∈ {0.01, 0.05, 0.1} (See US-3)
- **SC-004**: Collinearity diagnostics (VIF values) are measured against the VIF > 10 threshold to flag predictors that cannot claim independent effects (See US-3)
- **SC-005**: Computational runtime is measured against the 3-hour target defined in FR-004, noting the 6-hour GitHub Actions free-tier limit as the infrastructure cap (See US-2)
- **SC-006**: Model stability is measured by the width of the 95% confidence interval for R² derived from 1000 bootstrap resamples (seed=42) (See US-3)
- **SC-007**: Quickstart.md validation is measured by the presence of a validation log or report confirming successful execution of the quickstart steps (See US-1)

## Assumptions

- HEA datasets from Materials Project, NIST, or Zenodo contain ≥500 single-phase room-temperature compositions with complete elemental property data (atomic radii, electronegativity, valence electron counts) for all constituent elements
- Yield strength values in source datasets are reported in standardized units or can be reliably converted to MPa with documented conversion factors
- The observational dataset contains no random assignment of compositions; all reported relationships will be framed as associational rather than causal
- CPU-only execution on GitHub Actions free-tier (2 cores, ~7 GB RAM) can complete model training and statistical validation within ≤3 hours total
- The significance threshold α = 0.05 follows community standards for hypothesis testing in materials property prediction; sensitivity analysis will sweep {0.01, 0.05, 0.1} to assess robustness
- Elemental property databases (e.g., WebElements, Materials Project) provide complete data for all elements appearing in the HEA dataset; any missing values result in composition exclusion
- Multiple-comparison correction using Bonferroni or Benjamini-Hochberg is appropriate for the number of hypothesis tests (≥5 descriptors) conducted in this analysis, applied only to the VIF-filtered set
- A tree-based model achieving R² > linear baseline R² is the primary research hypothesis; a target of R² ≥ 0.6 is a desired outcome but not a software acceptance criterion
- **Directory Structure**: The repository MUST contain the following directories: `code/`, `data/raw`, `data/processed`, `output/`, `tests/`, `output/plots`. Each `code/` and `tests/` subdirectory MUST contain an `__init__.py` file to ensure package initialization.
- **Documentation**: A `README.md` with installation, usage, and data source sections, and a `quickstart.md` with a step-by-step walkthrough, MUST be generated and validated.

# Feature Specification: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

**Feature Branch**: `001-predict-hea-yield-strength`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Descriptor Engineering (Priority: P1)

Researcher downloads HEA composition and yield strength data from open repositories, calculates compositional descriptors (atomic size mismatch δ, electronegativity variance Δχ, valence electron concentration VEC, mixing entropy, melting temperature variance), and filters to single-phase alloys at room temperature.

**Why this priority**: Without validated input data and correctly calculated descriptors, no downstream modeling is possible. This forms the foundational dataset for all subsequent analysis.

**Independent Test**: Can be fully tested by executing the data pipeline and verifying that the system reports the count of available single-phase HEA compositions with complete descriptor values and yield strength measurements in a CSV file.

**Acceptance Scenarios**:

1. **Given** access to the NIST HEA database (primary test target) or Materials Project/Zenodo/figshare datasets, **When** the researcher runs the data acquisition script, **Then** a merged dataset is produced and the system reports the count of single-phase room-temperature HEA compositions. The system MUST support at least one of these sources.
2. **Given** elemental property data (atomic radii, electronegativity, valence electron counts), **When** the descriptor calculation module runs, **Then** each alloy composition has δ, Δχ, VEC, mixing entropy, and melting temperature variance computed with no missing values.
3. **Given** raw HEA data with phase and temperature annotations, **When** filtering criteria are applied, **Then** only single-phase alloys tested at room temperature (20-25°C) remain in the output dataset.

---

### User Story 2 - Model Training and Predictive Performance Evaluation (Priority: P2)

Researcher trains random forest and gradient boosting models using 5-fold cross-validation with hyperparameter tuning (100-200 trees for RF, 50-100 for GBM, depth ≤ 6), evaluates on a stratified 80/20 hold-out test set (seed=42), and compares R², MAE, and RMSE against a baseline Ordinary Least Squares (OLS) linear regression model on the same 5 descriptors.

**Why this priority**: The core predictive capability determines whether compositional descriptors carry sufficient signal for practical alloy screening. This delivers the primary quantitative result.

**Independent Test**: Can be fully tested by executing model training and evaluation scripts, then verifying that R², MAE, and RMSE values are recorded in a JSON report file at `output/metrics.json` with keys `R2`, `MAE`, `RMSE` for both tree-based models and the linear baseline on the held-out test set, and that the total runtime is ≤3 hours.

**Acceptance Scenarios**:

1. **Given** the prepared dataset with descriptors and yield strength values, **When** random forest and gradient boosting models are trained with 5-fold cross-validation (seed=42), **Then** both models complete within ≤3 hours on a CPU-only environment.
2. **Given** trained models, **When** evaluation runs on a stratified 80/20 hold-out test set (seed=42), **Then** the tree-based model's R² is compared against the OLS baseline R² to quantify improvement.
3. **Given** multiple model outputs, **When** performance metrics are compared, **Then** the best tree-based model's R², MAE, and RMSE are documented alongside the linear regression baseline for direct comparison.

---

### User Story 3 - Statistical Validation and Significance Reporting (Priority: P3)

Researcher performs permutation importance testing with 1000 permutations (seed=42), conducts bootstrap resampling for model stability (seed=42), applies multiple-comparison correction for the filtered set of descriptors (VIF < 10), conducts sensitivity analysis on the significance threshold (α ∈ {0.01, 0.05, 0.1}), and documents collinearity diagnostics among predictors.

**Why this priority**: Statistical rigor ensures findings are methodologically defensible and reproducible. This addresses the methodology panel's concerns about inference framing and threshold justification.

**Independent Test**: Can be fully tested by executing statistical validation scripts and verifying that permutation p-values, bootstrap confidence intervals, multiple-comparison corrected significance levels, and threshold sensitivity results are all recorded in the output report.

**Acceptance Scenarios**:

1. **Given** fitted models with descriptor importance scores, **When** permutation testing runs with 1000 permutations (seed=42), **Then** p-values are calculated for all descriptors.
2. **Given** ≥5 hypothesis tests across descriptors, **When** multiple-comparison correction applies (Bonferroni or Benjamini-Hochberg) to the set of descriptors with VIF < 10, **Then** corrected p-values are reported to control family-wise error rate.
3. **Given** the significance threshold α = 0.05 as the primary cutoff, **When** sensitivity analysis sweeps α ∈ {0.01, 0.05, 0.1}, **Then** the report documents how the count of significant descriptors and R² values vary across thresholds.

---

### Edge Cases

- What happens when the downloaded dataset contains <500 single-phase room-temperature HEA compositions? The pipeline flags this as a data limitation and reports the actual N achieved; the model proceeds with available data but notes reduced statistical power.
- How does the system handle missing elemental property values (e.g., electronegativity not available for a rare element)? The pipeline excludes compositions containing elements with incomplete property data and logs the count of excluded entries.
- What happens when descriptor collinearity exceeds VIF > 10? The system flags the collinear descriptor pair, reports the variance inflation factor, and recommends joint descriptive reporting rather than claims of independent predictive effects.
- How does the system handle yield strength values reported in different units (MPa vs. GPa)? The pipeline normalizes all yield strength values to MPa before model training, logging the conversion factor applied.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download HEA composition and yield strength data from at least one open repository (NIST HEA database as primary test target, or Materials Project, or Zenodo/figshare DOI), filter for single-phase room-temperature entries, and report the count of available entries; if count < 500, the system MUST flag a data limitation (See US-1)
- **FR-002**: System MUST calculate five compositional descriptors per alloy: atomic size mismatch δ, electronegativity variance Δχ, valence electron concentration VEC, mixing entropy, and melting temperature variance (See US-1)
- **FR-003**: System MUST filter the dataset to retain only single-phase high-entropy alloys tested at room temperature (20-25°C), excluding entries with missing yield strength values or non-standard testing conditions (See US-1)
- **FR-004**: System MUST train random forest (100-200 trees) and gradient boosting (50-100 trees) models with 5-fold cross-validation (seed=42), hyperparameter grid search constrained to depth ≤ 6, completing within ≤3 hours on CPU-only hardware (See US-2)
- **FR-005**: System MUST evaluate model performance on a stratified 80/20 hold-out test set (seed=42), reporting R², MAE, and RMSE for both tree-based models and a baseline Ordinary Least Squares (OLS) linear regression model on the same 5 descriptors (See US-2)
- **FR-006**: System MUST calculate permutation p-values for all descriptors using 1000 permutations (seed=42) by shuffling the target variable y to assess feature relevance (See US-3)
- **FR-007**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) ONLY to the filtered set of descriptors with VIF < 10 to control family-wise error rate (See US-3)
- **FR-008**: System MUST conduct sensitivity analysis on the significance threshold by sweeping α ∈ {0.01, 0.05, 0.1} and reporting how the count of significant descriptors and R² values vary (See US-3)
- **FR-009**: System MUST compute variance inflation factors (VIF) for each descriptor within the full multiple regression model and flag any VIF > 10; descriptors with VIF > 10 MUST be excluded from significance claims or reported as collinear (See US-3)
- **FR-010**: System MUST append a mandatory disclaimer string "Associational analysis only; no causal inference" to all generated plots and the final report summary (See US-3)
- **FR-011**: System MUST perform bootstrap resampling (1000 resamples, seed=42) of the full model to assess the stability of performance metrics and report 95% confidence intervals (See US-3)
- **FR-012**: System MUST generate a README.md file containing installation steps, usage instructions, and data source requirements (See US-1)
- **FR-013**: System MUST generate a quickstart.md file containing a step-by-step walkthrough of the pipeline execution (See US-1)

### Key Entities *(include if feature involves data)*

- **HEA Composition**: Represents a high-entropy alloy with key attributes including elemental fractions (atomic percent for each element), phase structure (single-phase designation), and testing temperature
- **Descriptor Set**: Represents the five compositional features calculated per alloy: δ (atomic size mismatch), Δχ (electronegativity variance), VEC (valence electron concentration), mixing entropy, and melting temperature variance
- **Yield Strength Measurement**: Represents the experimentally measured mechanical property with units standardized to MPa, including metadata for testing protocol and source repository

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Test-set R² is measured against the baseline OLS linear regression R² to quantify improvement from tree-based models (See US-2)
- **SC-002**: Descriptor correlation significance (p-values from permutation testing) is measured against the α = 0.05 threshold with multiple-comparison correction applied to the VIF-filtered set (See US-3)
- **SC-003**: Threshold sensitivity results are measured against the headline R² and significant descriptor count to quantify stability across α ∈ {0.01, 0.05, 0.1} (See US-3)
- **SC-004**: Collinearity diagnostics (VIF values) are measured against the VIF > 10 threshold to flag predictors that cannot claim independent effects (See US-3)
- **SC-005**: Computational runtime is measured against the 3-hour target defined in FR-004, noting the 6-hour GitHub Actions free-tier limit as the infrastructure cap (See US-2)
- **SC-006**: Model stability is measured by the width of the 95% confidence interval for R² derived from 1000 bootstrap resamples (seed=42) (See US-3)
- **SC-007**: Quickstart.md validation is measured by the presence of a validation log or report confirming successful execution of the quickstart steps (See US-1)

## Assumptions

- HEA datasets from Materials Project, NIST, or Zenodo contain ≥500 single-phase room-temperature compositions with complete elemental property data (atomic radii, electronegativity, valence electron counts) for all constituent elements
- Yield strength values in source datasets are reported in standardized units or can be reliably converted to MPa with documented conversion factors
- The observational dataset contains no random assignment of compositions; all reported relationships will be framed as associational rather than causal
- CPU-only execution on GitHub Actions free-tier (2 cores, ~7 GB RAM) can complete model training and statistical validation within ≤3 hours total
- The significance threshold α = 0.05 follows community standards for hypothesis testing in materials property prediction; sensitivity analysis will sweep {0.01, 0.05, 0.1} to assess robustness
- Elemental property databases (e.g., WebElements, Materials Project) provide complete data for all elements appearing in the HEA dataset; any missing values result in composition exclusion
- Multiple-comparison correction using Bonferroni or Benjamini-Hochberg is appropriate for the number of hypothesis tests (≥5 descriptors) conducted in this analysis, applied only to the VIF-filtered set
- A tree-based model achieving R² > linear baseline R² is the primary research hypothesis; a target of R² ≥ 0.6 is a desired outcome but not a software acceptance criterion
- **Directory Structure**: The repository MUST contain the following directories: `code/`, `data/raw`, `data/processed`, `output/`, `tests/`, `output/plots`. Each `code/` and `tests/` subdirectory MUST contain an `__init__.py` file to ensure package initialization.
- **Documentation**: A `README.md` with installation, usage, and data source sections, and a `quickstart.md` with a step-by-step walkthrough, MUST be generated and validated.