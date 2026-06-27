# Feature Specification: Defect Chemistry and Ionic Conductivity Analysis

**Feature Branch**: `001-defect-chemistry-conductivity`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Defect Chemistry and Ionic Conductivity in Solid Electrolytes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Pipeline and Validation (Priority: P1)

Download crystal structures and experimental ionic conductivity data from OBELiX and Materials Project, then validate dataset completeness for all required variables (defect types, formation energies, migration barriers, conductivity values).

**Why this priority**: This is the foundational step; without verified data availability, no analysis can proceed. It delivers immediate value by confirming feasibility before expensive computations begin.

**Independent Test**: Can be fully tested by running the data download and validation script and producing a dataset completeness report without executing any DFT calculations.

**Acceptance Scenarios**:

1. **Given** a list of 15 oxide-based solid electrolyte compositions, **When** the data pipeline runs, **Then** all crystal structures are downloaded and stored with ≥95% success rate (at least 14 of 15 structures retrieved).
2. **Given** downloaded structures, **When** the validation script runs, **Then** a completeness report is generated listing each required variable (vacancy formation energy, interstitial formation energy, antisite formation energy, migration barrier, ionic conductivity) with its availability status per composition.
3. **Given** missing variables in the dataset, **When** the validation script completes, **Then** a `[NEEDS CLARIFICATION]` marker is logged for each missing variable with the specific dataset name and variable name.

---

### User Story 2 - Defect Energy and Barrier Calculations (Priority: P2)

Compute defect formation energies for Li vacancies, interstitials, and antisites, and estimate migration barriers using NEB method for representative defect configurations, all within CPU-only constraints.

**Why this priority**: This delivers the core computational research output; it depends on P1 data availability but is independent of the statistical analysis layer.

**Independent Test**: Can be fully tested by running the calculation module on 2-3 pre-selected test systems and verifying output energy values match expected ranges from literature (within 0.5 eV tolerance for defect energies).

**Acceptance Scenarios**:

1. **Given** a validated crystal structure from US-1, **When** defect calculations run for vacancy, interstitial, and antisite configurations, **Then** defect formation energies are computed and stored with units in eV for each defect type.
2. **Given** completed defect energy calculations, **When** NEB migration barrier calculations execute for 2-3 representative defect configurations, **Then** activation energies (Eₐ) are computed with convergence criteria met (force tolerance ≤0.05 eV/Å) within the 6-hour job time limit.
3. **Given** CPU-only execution constraints, **When** calculations run, **Then** all supercell systems contain ≤8 atoms per defect system to fit within 7 GB RAM, with explicit logging of atom counts for each calculation.

---

### User Story 3 - Statistical Analysis and Correlation (Priority: P3)

Perform linear regression analysis between defect formation energies and predicted ionic conductivity, apply multiple-comparison correction, and generate correlation plots with statistical significance testing (p < 0.05).

**Why this priority**: This synthesizes computational outputs into research findings; it depends on P1 and P2 completion but can be tested independently using synthetic or cached calculation data.

**Independent Test**: Can be fully tested by running the analysis module on a cached dataset of 15 compositions and verifying regression outputs, p-values, and correlation plots are generated.

**Acceptance Scenarios**:

1. **Given** defect formation energies and conductivity values from US-1 and US-2, **When** linear regression executes, **Then** correlation coefficients (R²) and p-values are computed for each defect type (vacancy, interstitial, antisite) with results stored in a structured format.
2. **Given** multiple hypothesis tests (≥3 defect types × ≥15 compositions), **When** multiple-comparison correction applies, **Then** family-wise error rate is controlled using Bonferroni or Benjamini-Hochberg procedure with adjusted p-values reported.
3. **Given** a statistical significance threshold (p < 0.05), **When** sensitivity analysis runs, **Then** the threshold is swept over {0.01, 0.05, 0.1} and headline false-positive rates are reported for each cutoff value.

---

### Edge Cases

- What happens when OBELiX lacks defect-specific data for certain compositions? → The validation script logs `[NEEDS CLARIFICATION: does OBELiX contain defect formation energies for <composition>?]` and the pipeline continues with available data.
- How does the system handle DFT calculation failures on GitHub Actions? → Failed calculations are retried up to 2 times with exponential backoff; after 2 failures, the system logs the failure and marks the composition as incomplete in the results report.
- What happens when the 6-hour job time limit is exceeded? → The workflow detects timeout and logs which calculations were incomplete; partial results are preserved for resumption in a subsequent job.
- How does the system handle collinearity between defect types (e.g., vacancy and interstitial concentrations are inversely related)? → The analysis includes a variance inflation factor (VIF) diagnostic and reports collinearity warnings when VIF > 5 for any predictor.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download crystal structures for ≥15 oxide-based solid electrolyte compositions from OBELiX and Materials Project with ≥95% retrieval success rate (See US-1)
- **FR-002**: System MUST validate that all required variables (vacancy formation energy, interstitial formation energy, antisite formation energy, migration barrier, ionic conductivity) are present in the dataset for ≥12 compositions (See US-1)
- **FR-003**: System MUST compute defect formation energies for vacancy, interstitial, and antisite defects using DFT single-point energy calculations with supercell size ≤8 atoms per defect system (See US-2)
- **FR-004**: System MUST estimate migration barriers using NEB method for ≥2 representative defect configurations per electrolyte system with force convergence ≤0.05 eV/Å (See US-2)
- **FR-005**: System MUST perform linear regression analysis between defect formation energies and predicted ionic conductivity using scikit-learn with R² and p-value outputs (See US-3)
- **FR-006**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) when >1 hypothesis test is executed, reporting adjusted p-values (See US-3)
- **FR-007**: System MUST sweep statistical significance threshold over {0.01, 0.05, 0.1} and report false-positive rate variation across cutoffs (See US-3)

### Key Entities

- **ElectrolyteComposition**: Represents a solid electrolyte material with attributes (composition formula, crystal structure file path, experimental conductivity value)
- **DefectConfiguration**: Represents a specific defect type (vacancy, interstitial, antisite) with attributes (defect_type, formation_energy_eV, supercell_atoms, calculation_status)
- **MigrationBarrier**: Represents NEB-computed activation energy with attributes (electrolyte_id, defect_type, activation_energy_eV, convergence_status)
- **AnalysisResult**: Stores statistical outputs with attributes (defect_type, R_squared, p_value, adjusted_p_value, significance_flag)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness rate is measured against the required variable set (vacancy, interstitial, antisite, migration barrier, conductivity) for ≥15 electrolyte compositions (See US-1)
- **SC-002**: Defect formation energy calculation accuracy is measured against literature values from OBELiX and related work citations, with tolerance ≤0.5 eV (See US-2)
- **SC-003**: Statistical power is measured against the sample size (n ≥ 15 compositions) with acknowledgment of limitation for regression analysis (See US-3)
- **SC-004**: Multiple-comparison correction is measured against family-wise error rate control using Bonferroni or Benjamini-Hochberg with adjusted p-values reported (See US-3)
- **SC-005**: Threshold sensitivity is measured against the sweep set {0.01, 0.05, 0.1} with false-positive rate variation documented for each cutoff (See US-3)

## Assumptions

- OBELiX dataset contains experimentally measured ionic conductivity values for ≥12 of the 15 target electrolyte compositions; if fewer are available, the analysis proceeds with available data and documents the limitation.
- DFT calculations using Quantum ESPRESSO (open-source) are feasible on GitHub Actions CPU-only runners; VASP is not used due to licensing constraints and GPU requirements.
- Super-cells of ≤8 atoms per defect system will fit within 7 GB RAM; if larger supercells are required for accuracy, the system will sample a subset of compositions to maintain feasibility.
- The 6-hour GitHub Actions job time limit is sufficient for 15 compositions × 3 defect types × 2 NEB configurations; if exceeded, partial results are preserved and logged for resumption.
- Migration barriers will be estimated using the Arrhenius relationship σ = σ₀ exp(-Eₐ/kT) with Eₐ from NEB calculations; σ₀ will be set to a literature-standard default value of target conductivity magnitude (S·cm⁻¹·K) with sensitivity analysis over {0.5×10⁻³, 10⁻³, 2×10⁻³} S·cm⁻¹·K.
- The analysis is framed as associational (observational) rather than causal, given the computational/experimental nature of the data; no causal claims are made without randomization or identification strategy.
- Statistical power is limited by n ≥ 15 compositions; the analysis will document this limitation and interpret effect sizes cautiously.
- Predictor collinearity between defect types will be diagnosed using variance inflation factor (VIF); if VIF > 5, the analysis will frame joint relationships descriptively rather than claiming independent predictive effects.

---

**[NEEDS CLARIFICATION]**: Does the OBELiX dataset contain defect formation energies for the specific 15 electrolyte compositions selected, or only bulk ionic conductivity measurements? If defect-specific data is missing, the analysis will rely on DFT-computed values with a `[NEEDS CLARIFICATION]` marker for each missing composition.

**[NEEDS CLARIFICATION]**: Is the Quantum ESPRESSO DFT code available on GitHub Actions free-tier runners, or will an alternative CPU-tractable method (e.g., pre-computed data from Materials Project, semi-empirical methods) be required?

**[NEEDS CLARIFICATION]**: What is the expected range of defect formation energies for the target compositions (e.g., 0.5-3.0 eV), to validate calculation outputs against literature benchmarks?
