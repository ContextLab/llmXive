# Feature Specification: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

**Feature Branch**: `001-leptophilic-dm-g2`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Can a minimal leptophilic dark‑matter model generate a loop contribution to the muon anomalous magnetic moment that simultaneously resolves the current (g‑2) discrepancy and satisfies existing cosmological, direct‑detection, and collider bounds?"  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Perform a Complete Parameter Scan (Priority: P1)

A researcher runs the provided analysis script to evaluate the full grid of model parameters and obtains a set of points that satisfy all physics constraints.

**Why this priority**: This is the core scientific deliverable; without a successful scan the question cannot be answered.

**Independent Test**: Execute the script on a fresh runner with default settings and verify that it terminates within the expected runtime and outputs a CSV file of viable points.

**Acceptance Scenarios**:

1. **Given** the analysis repository cloned on a fresh GitHub Actions `ubuntu-latest` runner with a 2‑core CPU, **When** the command `python run_scan.py` is executed, **Then** the script completes in ≤ 30 minutes and writes `viable_points.csv` containing at least one row (or an explicit “no viable region” flag).  
2. **Given** the same execution, **When** the script finishes, **Then** a contour plot `viable_region.png` is produced showing the subset of the (mediator mass, coupling) plane that meets all selection criteria.

---

### User Story 2 – Validate Analytic Δaₘᵤ Implementation (Priority: P2)

A researcher cross‑checks the computed one‑loop contribution against benchmark values published in the 2014 leptophilic DM paper.

**Why this priority**: Correct physics implementation is a prerequisite for any downstream conclusions.

**Independent Test**: Run the validation routine with the benchmark parameter set and compare the result to the published Δaₘᵤ value.

**Acceptance Scenarios**:

1. **Given** the benchmark point ( m_χ = 10 MeV, m_V = 100 MeV, g = 10⁻³ ), **When** `python validate_delta_a.py` is executed, **Then** the reported Δaₘᵤ differs from the reference value (Δaₘᵤ_ref = 2.51 × 10⁻⁹) by ≤ 2 % relative error.

---

### User Story 3 – Generate a Reproducible Report (Priority: P3)

A researcher requests a PDF report summarizing the scan outcomes, including all plots, tables of viable points, and a discussion of which constraints are most restrictive.

**Why this priority**: Enables rapid dissemination of results and ensures transparency for peer review.

**Independent Test**: Invoke the reporting tool and verify that the PDF contains the required sections and matches the latest scan outputs.

**Acceptance Scenarios**:

1. **Given** a completed scan, **When** `python make_report.py` is run, **Then** a file `g2_dm_report.pdf` is created that (a) lists the number of viable points, (b) includes the contour plot, (c) cites the four data sources (Planck, Xenon1T, LEP, SM g‑2), (d) records the scan configuration used, and (e) explicitly states the fallback mechanism used for Xenon1T limits.

---

### User Story 4 – Validate Relic Density and Sommerfeld Implementation (Priority: P4)

A researcher validates the numerical integration of the Boltzmann equation including Sommerfeld enhancement against a known non-perturbative solver or benchmark for a subset of points, particularly in resonance regions.

**Why this priority**: Ensures the physics calculation is accurate and does not produce false positives/negatives due to approximation errors.

**Independent Test**: Run the validation routine with a set of benchmark points in the resonance region and compare the result to the reference.

**Acceptance Scenarios**:

1. **Given** a set of benchmark points in the resonance region (e.g., m_V ~ O(MeV), g ~ 0.1), **When** `python validate_relic_density.py` is executed, **Then** the reported Ω_χ h² differs from the reference by ≤ 5 % relative error.

---

### User Story 5 – Validate Methodological Rigor and Search Space Definition (Priority: P5)

A researcher verifies that the parameter scan grid is dense enough to capture narrow viable bands (e.g., resonance regions) and that no multiplicity corrections are applied to the search space definition.

**Why this priority**: Ensures the scientific validity of the search results and prevents false negatives due to insufficient grid density or false positives due to statistical errors.

**Independent Test**: Run the grid convergence study and verify that the chosen grid density captures viable regions with ≥ 95% confidence. Verify that no multiplicity corrections are applied.

**Acceptance Scenarios**:

1. **Given** the grid convergence study results, **When** the study is executed, **Then** the report confirms that the chosen grid density captures viable regions with ≥ 95% confidence.
2. **Given** the scan results, **When** the results are analyzed, **Then** no multiplicity corrections (e.g., Bonferroni) are applied to the parameter scan results.

---

### Edge Cases

- **No viable points** – If the scan finds zero points that satisfy all constraints, the script must still produce a clear “no viable region” message and a plot indicating the excluded parameter space.  
- **Missing external data** – If any of the required data files (Planck relic‑density limits, Xenon1T limits, LEP mono‑photon tables) fail to download, the script aborts with a descriptive error and does not proceed to the physics calculations.  
- **Numerical overflow** – Extremely large coupling values (≥ 1) can cause overflow in the loop integral; the script caps couplings at 1 and logs a warning for any grid point that would exceed this bound.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute the one‑loop DM contribution Δa_μ(g_χ, g_μ, m_χ, m_V) using the analytic expressions from Ref. [2001]. Although the function signature supports independent couplings, the scan grid is strictly constrained to the diagonal where g_χ = g_μ = g as per the model definition.  
- **FR-002**: System MUST evaluate the thermal relic density Ω_χ h² via numerical integration of the Boltzmann equation including Sommerfeld enhancement using the Hulthen potential approximation. **This integration is performed ONLY during the pre-computation phase to generate lookup tables or for validation (See US-4).** During the main scan, the system MUST use linear interpolation from these pre-computed tables. **The numerical integration MUST use the Runge-Kutta 4th order method with a relative tolerance of ≤ 1e-6.** **The Sommerfeld enhancement factor S MUST be thermally averaged over the Maxwell-Boltzmann velocity distribution to calculate <σv>.**  
- **FR-003**: System MUST calculate the loop-induced spin‑independent scattering cross‑section σ_SI (via photon penguins) using the formula σ_SI = (α² * g² * m_N²) / (π * m_V⁴) * (proton charge radius approximation) and compare it to the Xenon1T limit. **The primary data source for the Xenon1T limit is the hardcoded curve from arXiv:1402.5143 (Ref [2014]).** If a live fetch from the official Xenon1T repository is successful and verified (SHA-256 checksum match), it MAY be used as an update; otherwise, the system MUST fall back to the hardcoded curve from arXiv:1402.5143. (See US-3).
- **FR-004**: System MUST apply LEP mono‑photon constraints on light mediators using the tabulated limits from Ref. [2014].  
- **FR-005**: System MUST retain only those parameter points that satisfy **all** of the following simultaneously:  
  - |Δa_μ – Δa_μ^{exp}| ≤ 2.51 × 10⁻⁹ (using the 2023 SM value).  
  - Ω_χ h² ≤ 0.12 (Planck upper bound).
  - σ_SI ≤ Xenon1T limit (using the hardcoded curve from arXiv:1402.5143 as the primary source, with fallback logic as defined in FR-003).
  - LEP collider limits respected.
  - (See US-1).
- **FR-006**: System MUST generate 2‑D contour visualizations (e.g., m_V vs g) of the viable region and export them as PNG files.  
- **FR-007**: System MUST log the full configuration (grid ranges, spacing, random seeds) and the versions of all external data files (including SHA-256 checksums) to ensure reproducibility (See US-3).  
- **FR-008**: System MUST NOT apply any multiplicity corrections (e.g., Bonferroni) to the parameter scan results; the viable region is defined solely by the physical constraints in FR-005. (See US-5).
- **FR-009**: System MUST use a 2-core CPU runner environment (e.g., GitHub Actions `ubuntu-latest` with 2 cores) for all timing benchmarks.
- **FR-010**: System MUST use the Runge-Kutta 4th order method (or higher) for numerical integration of the Boltzmann equation, with a relative tolerance of ≤ 1e-6.
- **FR-011**: System MUST use pre-computed lookup tables with linear interpolation for the relic density calculation during the main parameter scan to meet the ≤ 30 minute runtime constraint.
- **FR-012**: System MUST perform a grid convergence study (power analysis) before the final scan to determine the minimum grid density required to capture narrow viable bands (e.g., resonance regions) with ≥ 95% confidence.
- **FR-013**: System MUST flag a parameter point as "physically undefined" and exclude it from the viable region if the conversion from lepton-loop to nucleon-level cross-section (hadronic matrix element) is invalid for the given mass range (e.g., if the approximation breaks down).
- **FR-014**: System MUST validate the Hulthen potential approximation against a non-perturbative solver for a subset of points in the resonance region (e.g., m_V < 50 MeV, g > 0.05) and report the maximum relative error. If the error exceeds 10%, the system MUST flag the result as "approximation uncertainty high". **This validation MUST also be performed on the lookup table generation process to ensure the 'fast' table is scientifically valid.**
- **FR-015**: System MUST apply a momentum-dependent form factor (e.g., Helm form factor) when comparing the calculated σ_SI to the Xenon1T limit for light mediators (m_V < 100 MeV) to account for the 1/q⁴ scaling. **This form factor MUST be used to convert the standard Xenon1T contact-interaction limit to the photon-penguin limit for leptophilic models.**

### Key Entities *(include if feature involves data)*

- **ParameterPoint**: Represents a single tuple (m_χ, m_V, g) where g = g_χ = g_μ, together with derived quantities Δa_μ, Ω_χ h², σ_SI, and a Boolean flag for each external constraint.  
- **ConstraintDataset**: Immutable collection of external limits (Planck relic density, Xenon1T σ_SI curve, LEP mono‑photon exclusion map) referenced by FR‑002 – FR‑004.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full interpolated parameter scan completes in ≤ 30 minutes on a 2‑core CPU runner (runtime measured by the script’s built‑in timer).  
- **SC-002**: Analytic Δa_μ values match the benchmark from Ref. [2014] within a relative error of ≤ 2 % (validation logged in `validation.log`).  
- **SC-003**: At least one viable ParameterPoint is identified **or** the system correctly reports “no viable region” with a clear justification (recorded in `summary.txt`). (See US-1).
- **SC-004**: All generated PNG plots have a resolution of ≥ 300 dpi and include axis labels, units, and a legend describing the applied constraints.  
- **SC-005**: The final PDF report (`g2_dm_report.pdf`) contains a reproducibility section that lists data‑source DOIs, script SHA‑256 hash, and the exact grid specifications.  
- **SC-006**: The grid convergence study (FR-012) confirms that the chosen grid density captures viable regions with ≥ 95% confidence.
- **SC-007**: The validation of the Hulthen approximation (FR-014) shows a maximum relative error of ≤ 10% in the resonance region.
- **SC-008**: The validation of the lookup table generation process (FR-014) shows a maximum relative error of ≤ 10% in the resonance region.

## Assumptions

- The Planck 2018 relic‑density upper bound (Ω_χ h² ≤ 0.12) is sufficient; we do not enforce a lower bound because under‑abundance can be compensated by additional DM components.  
- Xenon1T limits are primarily sourced from arXiv:1402.5143 (hardcoded curve) as the verified ground truth. A live fetch from the official Xenon1T repository is attempted for verification but is NOT the primary source.
- LEP mono‑photon exclusion limits from Ref. [2014] are applicable to vector mediators with couplings to muons only; scalar mediators are assumed to have comparable limits.  
- The assumption g_χ = g_μ is a specific model choice for this scan to reduce dimensionality; the system implementation supports the general multidimensional case if needed in future, but the current scan is restricted to the diagonal.  
- Log‑spacing of the grid (on the order of tens of points along the first two dimensions and a smaller number along the third) is dense enough to capture narrow viable bands; finer resolution is deferred to a follow‑up study, subject to the grid convergence study (FR-012).  
- The numerical integration of the Boltzmann equation including Sommerfeld enhancement (via Hulthen potential) is adequate for the parameter space of interest; full non-perturbative calculations are beyond the scope, except for the validation subset (FR-014).  
- All external data files are static during a single run; version changes will be tracked via the reproducibility log.  
- The proton charge radius approximation is sufficient for converting the lepton-loop induced cross-section to a nucleon-level cross-section for the mass range considered, **provided the Helm form factor is applied to convert the contact-interaction limit to the photon-penguin limit as required by FR-015.**
- The conversion of the Xenon1T contact-interaction limit to the photon-penguin limit using the Helm form factor is necessary to avoid a category error in the validation target.

---  

*All cited URLs are taken directly from the Idea Markdown and have not been altered.*