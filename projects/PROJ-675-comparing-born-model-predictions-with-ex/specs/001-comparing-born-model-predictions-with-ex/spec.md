# Feature Specification: Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions

**Feature Branch**: `001-born-model-solvation-comparison`  
**Created**: 2026-06-12  
**Status**: Draft  
**Input**: User description: "Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions chemistry"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compile Experimental Solvation Energy Dataset (Priority: P1)

The researcher compiles a unified dataset containing experimental solvation free energies, solvent dielectric constants, and ionic radii from public chemistry databases (NIST, CRC Handbook, Shannon radii).

**Why this priority**: This forms the foundational data layer without which no model comparison can proceed. All downstream analysis depends on this dataset being complete and consistent.

**Independent Test**: Can be fully tested by verifying the dataset contains ≥30 ion-solvent pairs with complete fields (experimental ΔG, ε, r, charge) and that each value includes an uncertainty estimate or documented source precision.

**Acceptance Scenarios**:

1. **Given** access to NIST Chemistry WebBook and CRC Handbook, **When** the researcher downloads solvation energy data for common ions (Na⁺, K⁺, Cl⁻, etc.) across multiple solvents, **Then** the compiled CSV contains at least 30 complete ion-solvent pairs with uncertainty bounds
2. **Given** the Shannon crystal radii database, **When** ionic radii are extracted for all ions in the experimental dataset, **Then** each radius is specified to ≥0.01 Å precision with source citation
3. **Given** solvent dielectric constants from literature, **When** these are matched to experimental measurement conditions, **Then** each ε value includes temperature specification (±0.5°C) and uncertainty

---

### User Story 2 - Implement and Validate Born Model Calculator (Priority: P2)

The researcher implements the Born equation in Python and validates it against known reference cases before applying it to the full dataset.

**Why this priority**: The computational engine must produce correct results before it can be trusted for regression analysis. Validation against known cases catches implementation errors early.

**Independent Test**: Can be fully tested by computing Born predictions for a small reference set (e.g., a small number of ion-water pairs) and verifying outputs match published analytical values within 1% tolerance.

**Acceptance Scenarios**:

1. **Given** the Born equation implementation ΔG = -(z²e²)/(8πε₀r)(1 - 1/ε), **When** the researcher computes solvation energy for Na⁺ in water (ε=78.4, r=1.02 Å), **Then** the output matches literature reference values within 1% relative error
2. **Given** unit conversion requirements, **When** the calculator processes inputs in mixed units (Å, kcal/mol, dimensionless ε), **Then** all outputs are consistently reported in kcal/mol with documented conversion factors
3. **Given** the dataset with 30+ ion-solvent pairs, **When** the calculator processes all pairs, **Then** computation completes in <10 minutes on 2 CPU cores without GPU dependencies

---

### User Story 3 - Regression Analysis and Breakdown Detection (Priority: P3)

The researcher performs statistical regression of residuals against 1/r and 1/ε, identifies systematic deviation patterns, and determines the breakdown threshold where Born model accuracy falls below acceptable limits.

**Why this priority**: This delivers the core research output—the accuracy map that identifies when continuum dielectric assumptions fail.

**Independent Test**: Can be fully tested by running the regression pipeline and verifying that RMSE, correlation coefficient, and p-values are computed with multiple-comparison correction applied.

**Acceptance Scenarios**:

1. **Given** the computed Born predictions and experimental values, **When** the researcher calculates residuals (experimental - theoretical), **Then** RMSE is computed overall and stratified by solvent class (water, alcohols, aprotic)
2. **Given** multiple hypothesis tests (regression slopes for 1/r, 1/ε, solvent classes), **When** statistical significance is assessed, **Then** family-wise error correction (Bonferroni or Benjamini-Hochberg) is applied with p < 0.05 threshold
3. **Given** the accuracy thresholds (RMSE < 5 kcal/mol, correlation > 0.8), **When** the researcher identifies breakdown regimes, **Then** a sensitivity analysis sweeps the RMSE threshold over {4.5, 5.0, 5.5} kcal/mol and reports how classification rates vary

---

### Edge Cases

- What happens when experimental uncertainty exceeds the residual magnitude (i.e., difference between model and experiment falls within measurement error)?
- How does the system handle ions with ambiguous radii (e.g., multiple coordination environments in Shannon database)?
- What if solvent dielectric constant varies significantly with temperature and measurement conditions are not specified?
- How are outliers (e.g., RMSE > 20 kcal/mol) flagged for manual review versus automatic exclusion?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compile experimental solvation energies from NIST Chemistry WebBook and CRC Handbook with ≥30 complete ion-solvent pairs (See US-1)
- **FR-002**: System MUST extract ionic radii from Shannon crystal radii database with ≥0.01 Å precision for all ions in the dataset (See US-1)
- **FR-003**: System MUST implement the Born equation ΔG = -(z²e²)/(8πε₀r)(1 - 1/ε) in Python without GPU dependencies (See US-2)
- **FR-004**: System MUST validate Born calculator against ≥5 reference ion-water pairs with ≤1% relative error tolerance (See US-2)
- **FR-005**: System MUST compute residuals and RMSE stratified by solvent class (water, alcohols, aprotic) (See US-3)
- **FR-006**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) to all hypothesis tests with p < 0.05 threshold (See US-3)
- **FR-007**: System MUST perform sensitivity analysis on RMSE threshold over {4.5, 5.0, 5.5} kcal/mol and report classification rate variation (See US-3)
- **FR-008**: System MUST document experimental uncertainty bounds for all solvation energy values, or flag pairs where uncertainty is unavailable (See US-1)

### Key Entities *(include if feature involves data)*

- **IonSolventPair**: Represents a single experimental measurement; key attributes include ion identifier, solvent identifier, experimental ΔG (kcal/mol), uncertainty estimate, temperature (°C)
- **BornPrediction**: Represents a theoretical calculation; key attributes include ion identifier, solvent identifier, predicted ΔG (kcal/mol), ionic radius (Å), dielectric constant (dimensionless)
- **ResidualAnalysis**: Represents regression output; key attributes include residual (kcal/mol), 1/r (Å⁻¹), 1/ε (dimensionless), solvent class, statistical significance (p-value)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the requirement of ≥30 complete ion-solvent pairs with uncertainty bounds (See US-1)
- **SC-002**: Born calculator accuracy is measured against literature reference values with ≤1% relative error tolerance (See US-2)
- **SC-003**: Model accuracy breakdown is measured by RMSE threshold (4.5, 5.0, 5.5 kcal/mol) and correlation coefficient (0.8 cutoff) across solvent classes (See US-3)
- **SC-004**: Statistical validity is measured by application of multiple-comparison correction with p < 0.05 significance threshold (See US-3)
- **SC-005**: Experimental uncertainty coverage is measured as the percentage of dataset pairs with documented uncertainty bounds (See US-1)

## Assumptions

- NIST Chemistry WebBook and CRC Handbook contain sufficient experimental solvation energy data for ≥30 ion-solvent pairs with uncertainty estimates
- Shannon crystal radii database provides consistent ionic radius values across all ions in the experimental dataset
- Experimental solvation energies were measured at controlled temperature (±0.5°C) or temperature specifications are available for dielectric constant correction
- All required variables (experimental ΔG, solvent ε, ionic radius r, ion charge z) exist in the compiled dataset; if any are missing, the pair is excluded from analysis
- Computational resources on GitHub Actions free tier (2 CPU cores, ~7 GB RAM) are sufficient for analytical Born calculations and linear regression on the dataset
- The Born model uses macroscopic dielectric constants; no molecular-scale corrections (nonlocal electrostatics) are applied in this baseline comparison
- Single-ion absolute solvation energies are experimentally accessible in the literature; if only relative values exist, they are normalized using a reference ion (e.g., tetraphenylarsonium/tetraphenylborate convention)
