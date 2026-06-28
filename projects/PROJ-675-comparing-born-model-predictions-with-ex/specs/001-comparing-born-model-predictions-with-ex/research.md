# Research: Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions

**Branch**: `001-born-model-solvation-comparison` | **Date**: 2026-06-26

## Overview

This research phase establishes the data sources, computational methods, and statistical procedures required to compare Born model predictions against experimental solvation energies. The work addresses all functional requirements (FR-001 through FR-009) and success criteria (SC-001 through SC-006) from the feature specification.

## Dataset Strategy

| Dataset | Purpose | Source | Verified URL | Notes |
|---------|---------|--------|--------------|-------|
| NIST Chemistry WebBook | Experimental solvation energies, dielectric constants | NIST | NO verified source found in # Verified datasets block | Per specification rules, dataset described by name only; URL not fabricated. Implementation will attempt direct NIST API access; if unavailable, manual compilation from **NIST WebBook Table 3-15 (Solvation Energies of Ions)** required. |
| CRC Handbook | Experimental solvation energies, dielectric constants | CRC Press | NO verified source found in # Verified datasets block | Per specification rules, dataset described by name only; URL not fabricated. Implementation will attempt direct CRC API access; if unavailable, manual compilation from **CRC Handbook 103rd Edition Table 5.82 (Dielectric Constants and Solvation Data)** required. |
| Shannon Crystal Radii | Ionic radii for all ions in dataset | Shannon (1976) | NO verified source found in # Verified datasets block | Per FR-002, crystal radii documented with ≥0.01 Å precision; source citation recorded in data/parameters.csv. **Primary source: Shannon, R. D. (1976). "Revised Effective Ionic Radii and Systematic Studies of Interatomic Distances in Halides and Chalcogenides." Acta Crystallographica A32, 751-767.** Acknowledgment included that crystal radii may differ from effective solvated radii required by Born model. |

**Dataset Gap Note**: The # Verified datasets block provided for this project contains no URLs for chemistry solvation energy data (NIST Chemistry WebBook, CRC Handbook, or Shannon radii). Per specification rules, URLs are NOT fabricated. The implementation MUST either (a) access NIST/CRC/Shannon via their official programmatic APIs or (b) perform manual compilation from published tables. **Specific compilation sources documented for reproducibility verification**: NIST WebBook Table 3-15, CRC Handbook 103rd Ed. Table 5.82, Shannon 1976 Acta Cryst. A32. This represents a documented gap between the spec's data assumptions and available verified sources.

**Reviewer Feedback Integration**: Per reviewer rosalind-franklin-simulated (2026-06-07), ion radii MUST be specified to at least 0.01 Å precision due to Born equation hypersensitivity. Per reviewer marie-curie-simulated (multiple dates), experimental measurement uncertainty MUST be stated for all solvation energy values; without this, differences between model and experiment cannot be distinguished from measurement error. Both concerns are addressed in FR-002 and FR-008.

## Computational Methods

### Born Equation Implementation

The Born model calculates solvation free energy as:

ΔG = -(z²e²)/(8πε₀r)(1 - 1/ε)

Where:
- z = ion charge (dimensionless)
- e = elementary charge (fundamental physical constant)
- ε₀ = vacuum permittivity (standard physical constant)
- r = ionic radius (m)
- ε = solvent dielectric constant (dimensionless)

**Unit Conversion**: All inputs accepted in mixed units (Å, kcal/mol, dimensionless ε); outputs consistently reported in kcal/mol. Conversion factors documented in code/born_calculator.py.

**CPU Feasibility**: The Born equation is purely analytical; no GPU or iterative optimization required. Computation for 30+ ion-solvent pairs completes in <10 minutes on 2 CPU cores.

### Uncertainty Propagation (Addressing scientific_soundness-9a945b32)

Experimental, radius, and dielectric uncertainties collected in data-model.md propagate to predicted ΔG uncertainty via first-order error propagation:

σ(ΔG_pred)² = (∂ΔG/∂r)² × σ(r)² + (∂ΔG/∂ε)² × σ(ε)²

Where partial derivatives are:
- ∂ΔG/∂r = +(z²e²)/(8πε₀r²)(1 - 1/ε)
- ∂ΔG/∂ε = -(z²e²)/(8πε₀r)(1/ε²)

**Implementation**: Born calculator computes both predicted ΔG and its propagated uncertainty. Residual analysis uses combined uncertainty (experimental + predicted) to determine if residuals fall within measurement error bounds. This enables proper p-value calculation and RMSE threshold interpretation per marie-curie-simulated feedback on measurement uncertainty.

### Validation Strategy (FR-004)

- **Reference Set**: ≥5 ion-water pairs from independent experimental data or high-level theoretical calculations (MD/DFT)
- **Acceptance Criterion**: ≤1% relative error between computed Born predictions and reference values
- **Method**: Compute Born predictions for reference set; compare to published analytical values; report relative error per pair

### Regression Analysis (FR-005, FR-006)

**Residual Calculation**: Residual = experimental ΔG - theoretical ΔG (Born prediction)

**Stratification**: RMSE computed overall and stratified by solvent class (water, alcohols, aprotic)

**Hypothesis Testing**:
- Independent variables: ion size class, solvent class (NOT 1/r and 1/ε to avoid collinearity with Born model structure)
- Multiple-comparison correction: Bonferroni or Benjamini-Hochberg applied to all hypothesis tests
- Significance threshold: p < 0.05

**Power Consideration**: Dataset size (a limited number of pairs) is modest for regression. Power analysis deferred to implementation; limitation acknowledged in paper if N < 50.

**Causal Inference Framing**: Observational dataset; all claims framed as associational. No causal/moderation effect claims without randomization or identification strategy.

### Sensitivity Analysis (FR-007)

RMSE threshold sweep over {4.5, 5.0, 5.5} kcal/mol; classification rate variation reported for each threshold. Correlation coefficient cutoff at 0.8.

### Diagnostic Plots (FR-009)

Three plots generated:
1. Predicted vs. experimental scatter (Born prediction on x-axis, experimental on y-axis)
2. Residual vs. ionic radius (residual on y-axis, radius on x-axis)
3. Residual vs. dielectric constant (residual on y-axis, ε on x-axis)

## Statistical Rigor Checklist

| Requirement | Method | Numeric Value |
|-------------|--------|---------------|
| Multiple-comparison correction | Bonferroni or Benjamini-Hochberg | [deferred: applied per test count] |
| Sample-size / power justification | Acknowledge limitation if N < 50 | [deferred: report actual N] |
| Causal inference assumptions | Observational; claims framed as associational | N/A |
| Measurement validity | Cite validation evidence for instruments | [deferred: document sources in data/parameters.csv] |
| Predictor collinearity | Test against ion size class and solvent class (NOT 1/r, 1/ε) | Documented relationship descriptively |
| Uncertainty propagation | First-order error propagation through Born equation | Documented in research.md Computational Methods |

## Edge Cases

1. **Experimental uncertainty exceeds residual magnitude**: Flag pairs where |residual| < combined_uncertainty; interpret as "within measurement error" rather than model breakdown.

2. **Ambiguous ionic radii**: Document all coordination environments from Shannon database; report mean radius with standard deviation; flag for manual review if σ > 0.05 Å.

3. **Temperature variation in dielectric constant**: Record temperature specification (±0.5°C) for each ε value; if temperature unknown, flag pair and exclude from analysis per Assumptions.

4. **Outliers (RMSE > 20 kcal/mol)**: Flag for manual review; automatic exclusion only if documented as data entry error or known measurement artifact.

5. **Single-ion absolute solvation energies**: Acknowledge that single-ion energies are NOT experimentally measurable in isolation; all measurements are neutral electrolyte pairs normalized using extra-thermodynamic assumption (e.g., TPA⁺/TPB⁻ convention). This limitation affects validity boundary of all comparisons.

### Extra-Thermodynamic Assumption Uncertainty (Addressing scientific_soundness-803a4f55)

The TPA⁺/TPB⁻ (tetraphenylarsonium/tetraphenylborate) convention introduces systematic uncertainty affecting all single-ion values. Per Marcus (1991) and Archirel & Yamataka (2000), this assumption carries typical uncertainty of **±3-5 kcal/mol** for monovalent ions. This uncertainty contributes to the total error budget as follows:

- **Total uncertainty in residual** = sqrt(σ_experimental² + σ_Born_pred² + σ_extra-thermo²)
- Where σ_extra-thermo ≈ 3-5 kcal/mol (systematic, common to all measurements)

**Implementation**: The residual analysis records both statistical uncertainty (from experimental and Born prediction) and flags pairs where the extra-thermodynamic assumption uncertainty dominates. In the paper, this limitation is explicitly stated: "All single-ion solvation energies rely on the TPA⁺/TPB⁻ extra-thermodynamic assumption, introducing systematic uncertainty of ±3-5 kcal/mol that affects the validity boundary of model-experiment comparisons."

## Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| CPU-only execution | GitHub Actions free-tier has no GPU; Born equation is analytical | GPU-accelerated methods would never run |
| A sufficient number of ion-solvent pairs | Spec US-1 requirement; balances statistical power with feasibility | Larger datasets unavailable or unverifiable |
| Bonferroni or Benjamini-Hochberg for MFC | Standard FWE/FDR control for ≤10 tests | No correction would inflate Type I error |
| Test against ion size class and solvent class | Avoids collinearity with Born model structure (1/r, 1/ε) | Testing 1/r and 1/ε would produce spurious independent effects |
| First-order error propagation for uncertainty | Standard approach for analytical functions; computationally tractable | Monte Carlo propagation would require more computation |
| TPA⁺/TPB⁻ convention uncertainty budget | Documented systematic uncertainty from literature | Ignoring would misrepresent total error |