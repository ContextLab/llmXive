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

1. **Given** the analysis repository cloned on a fresh Ubuntu 22.04 runner with Python 3.11, **When** the command `python run_scan.py` is executed, **Then** the script completes in ≤ 30 minutes on a 2‑core CPU and writes `viable_points.csv` containing at least one row (or an explicit “no viable region” flag).  
2. **Given** the same execution, **When** the script finishes, **Then** a contour plot `viable_region.png` is produced showing the subset of the (mediator mass, coupling) plane that meets all selection criteria.

---

### User Story 2 – Validate Analytic Δaₘᵤ Implementation (Priority: P2)

A researcher cross‑checks the computed one‑loop contribution against benchmark values published in the 2014 leptophilic DM paper.

**Why this priority**: Correct physics implementation is a prerequisite for any downstream conclusions.

**Independent Test**: Run the validation routine with the benchmark parameter set and compare the result to the published Δaₘᵤ value.

**Acceptance Scenarios**:

1. **Given** the benchmark point ( m_χ = 10 MeV, m_V = 100 MeV, g_χ = g_μ = 10⁻³ ), **When** `python validate_delta_a.py` is executed, **Then** the reported Δaₘᵤ differs from the reference by ≤ 2 % relative error.

---

### User Story 3 – Generate a Reproducible Report (Priority: P3)

A researcher requests a PDF report summarizing the scan outcomes, including all plots, tables of viable points, and a discussion of which constraints are most restrictive.

**Why this priority**: Enables rapid dissemination of results and ensures transparency for peer review.

**Independent Test**: Invoke the reporting tool and verify that the PDF contains the required sections and matches the latest scan outputs.

**Acceptance Scenarios**:

1. **Given** a completed scan, **When** `python make_report.py` is run, **Then** a file `g2_dm_report.pdf` is created that (a) lists the number of viable points, (b) includes the contour plot, (c) cites the four data sources (Planck, Xenon1T, LEP, SM g‑2), and (d) records the scan configuration used.

---

### Edge Cases

- **No viable points** – If the scan finds zero points that satisfy all constraints, the script must still produce a clear “no viable region” message and a plot indicating the excluded parameter space.  
- **Missing external data** – If any of the required data files (Planck relic‑density limits, Xenon1T limits, LEP mono‑photon tables) fail to download, the script aborts with a descriptive error and does not proceed to the physics calculations.  
- **Numerical overflow** – Extremely large coupling values (≥ 1) can cause overflow in the loop integral; the script caps couplings at 1 and logs a warning for any grid point that would exceed this bound.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute the one‑loop DM contribution Δa_μ(g_χ, g_μ, m_χ, m_V) using the analytic expressions from Ref. [2001] for any point on the scan grid.  
- **FR-002**: System MUST evaluate the thermal relic density Ω_χ h² via the analytic s‑wave approximation described in the Planck 2018 analysis.  
- **FR-003**: System MUST calculate the spin‑independent scattering cross‑section σ_SI and compare it to the Xenon1T [deferred] CL limit for the corresponding DM mass.
- **FR-004**: System MUST apply LEP mono‑photon constraints on light mediators using the tabulated limits from Ref. [2014].  
- **FR-005**: System MUST retain only those parameter points that satisfy **all** of the following simultaneously:  
  - |Δa_μ – Δa_μ^{exp}| ≤ 1 σ (using the 2023 SM value).  
  - Ω_χ h² ≤ 0.12 (Planck upper bound).  
  - σ_SI ≤ Xenon1T limit.  
  - LEP collider limits respected.  
- **FR-006**: System MUST generate 2‑D contour visualizations (e.g., m_V vs g_μ) of the viable region and export them as PNG files.  
- **FR-007**: System MUST log the full configuration (grid ranges, spacing, random seeds) and the versions of all external data files to ensure reproducibility.  
- **FR-008**: System MUST apply a Bonferroni correction for the family‑wise error rate when evaluating the Δa_μ ≤ 1 σ condition across the ≈ 75 k grid points.  

### Key Entities *(include if feature involves data)*

- **ParameterPoint**: Represents a single tuple (m_χ, m_V, g_χ, g_μ) together with derived quantities Δa_μ, Ω_χ h², σ_SI, and a Boolean flag for each external constraint.  
- **ConstraintDataset**: Immutable collection of external limits (Planck relic density, Xenon1T σ_SI curve, LEP mono‑photon exclusion map) referenced by FR‑002 – FR‑004.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full scan completes in ≤ 30 minutes on a 2‑core CPU runner (runtime measured by the script’s built‑in timer).  
- **SC-002**: Analytic Δa_μ values match the benchmark from Ref. [2014] within a relative error of ≤ 2 % (validation logged in `validation.log`).  
- **SC-003**: At least one viable ParameterPoint is identified **or** the system correctly reports “no viable region” with a clear justification (recorded in `summary.txt`).  
- **SC-004**: All generated PNG plots have a resolution of ≥ 300 dpi and include axis labels, units, and a legend describing the applied constraints.  
- **SC-005**: The final PDF report (`g2_dm_report.pdf`) contains a reproducibility section that lists data‑source DOIs, script SHA‑256 hash, and the exact grid specifications.  

## Assumptions

- The Planck 2018 relic‑density upper bound (Ω_χ h² ≤ 0.12) is sufficient; we do not enforce a lower bound because under‑abundance can be compensated by additional DM components.  
- Xenon1T [deferred] CL limits are available as a downloadable CSV from the official Xenon1T public repository and are valid for the entire DM‑mass range considered (1 MeV–1 TeV).
- LEP mono‑photon exclusion limits from Ref. [2014] are applicable to vector mediators with couplings to muons only; scalar mediators are assumed to have comparable limits.  
- Couplings are taken to be equal (g_χ = g_μ) as specified in the methodology sketch; any deviation would require a separate scan.  
- Log‑spacing of the grid (on the order of tens of points along the first two dimensions and a smaller number along the third). is dense enough to capture narrow viable bands; finer resolution is deferred to a follow‑up study.  
- The analytic s‑wave approximation for relic density is adequate for the parameter space of interest; more detailed Boltzmann‑solver calculations are beyond the scope of this feature.  
- All external data files are static during a single run; version changes will be tracked via the reproducibility log.  

---  

*All cited URLs are taken directly from the Idea Markdown and have not been altered.*
