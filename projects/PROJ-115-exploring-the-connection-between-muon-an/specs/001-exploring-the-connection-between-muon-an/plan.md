# Implementation Plan: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

**Branch**: `001-leptophilic-dm-g2` | **Date**: 2026-06-24 | **Spec**: `specs/001-leptophilic-dm-g2/spec.md`
**Input**: Feature specification from `/specs/001-leptophilic-dm-g2/spec.md`

## Summary

This project implements a CPU-tractable parameter scan for a minimal leptophilic dark matter (DM) model to determine if it can simultaneously resolve the muon anomalous magnetic moment ($g-2$) discrepancy and satisfy cosmological (Planck), direct detection (Xenon1T), and collider (LEP) constraints. The implementation relies on analytic loop calculations for $\Delta a_\mu$, pre-computed lookup tables with linear interpolation for relic density (including Sommerfeld enhancement via Hulthen potential), and hardcoded constraints for Xenon1T and LEP limits. The system is designed to run within 30 minutes on a 2-core GitHub Actions runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy` (for `integrate.ode` or manual RK4), `pandas`, `matplotlib`, `scikit-learn` (for interpolation), `pytest`.  
**Storage**: Local CSV/Parquet files in `data/` (checksummed) and `code/` (scripts).  
**Testing**: `pytest` (unit tests for physics functions, integration tests for scan pipeline).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`, 2 CPU, 7GB RAM).  
**Project Type**: CLI / Scientific Analysis Script  
**Performance Goals**: Full scan ≤ 30 minutes; Validation steps ≤ 5 minutes.  
**Constraints**: No GPU; No heavy LLM inference; Memory ≤ 7GB; Disk ≤ 14GB.  
**Scale/Scope**: Grid scan of approximately k to tens of thousands of points; Pre-computed tables for relic density.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Enforced via pinned `requirements.txt`, random seeds in `run_scan.py`, and checksumming of all `data/` artifacts.
- **II. Verified Accuracy**: All citations (Ref [Year], Ref [2001], Planck 2018) are explicitly tracked. The "Verified datasets" block confirms LEP data sources; Xenon1T and Planck are handled via hardcoded curves or standard cosmological constants as per spec, with no fabricated URLs. **The Reference-Validator Agent MUST be run at the end of Phase 0 and Phase 4 to ensure all citations are verified.**
- **III. Data Hygiene**: Raw data (LEP parquet) fetched via verified URLs only. Derived data (lookup tables) written to new files with checksums. No in-place modification.
- **IV. Single Source of Truth**: All figures and statistics in the final report trace to `data/viable_points.csv` and `data/relic_tables.csv`.
- **V. Versioning Discipline**: Content hashes for scripts and data files will be recorded in `state/` artifacts.
- **VI. Analytic-Numeric Consistency**: The plan mandates a validation step (`validate_delta_a.py`) comparing numeric implementation against Ref [2014] benchmarks (US-2).
- **VII. Phenomenological Constraint Integrity**: Constraints (Planck, Xenon1T, LEP) are implemented exactly as defined in FR-003, FR-004, and FR-005. The fallback to hardcoded Xenon1T curves is explicit. **The convolution method for Xenon1T limits is explicitly implemented.**

## Project Structure

### Documentation (this feature)

```text
specs/001-leptophilic-dm-g2/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-115-exploring-the-connection-between-muon-an/
├── code/
│   ├── __init__.py
│   ├── physics/
│   │   ├── __init__.py
│   │   ├── delta_a_mu.py       # Analytic loop calc (FR-001)
│   │   ├── relic_density.py    # Boltzmann eq + Sommerfeld (FR-002, FR-010, FR-014)
│   │   ├── cross_section.py    # Spin-independent scattering (FR-003, FR-015)
│   │   └── constraints.py      # LEP, Xenon1T, Planck checks (FR-004, FR-005)
│   ├── scan/
│   │   ├── __init__.py
│   │   ├── grid_generator.py   # Grid creation (FR-012)
│   │   ├── run_scan.py         # Main entry point (US-1)
│   │   └── interpolate.py      # Lookup table logic (FR-011)
│   ├── validation/
│   │   ├── validate_delta_a.py # US-2
│   │   └── validate_relic_density.py # US-4, FR-014
│   ├── reporting/
│   │   ├── make_report.py      # US-3
│   │   └── plot_utils.py       # FR-006, SC-004
│   └── config.py               # Global constants, seeds
├── data/
│   ├── raw/
│   │   └── lep_limits.parquet  # From verified URL
│   ├── processed/
│   │   ├── relic_lookup.csv    # Pre-computed tables
│   │   └── viable_points.csv   # Scan output
│   └── checksums.json          # Data hygiene (Constitution III)
├── tests/
│   ├── unit/
│   │   ├── test_delta_a.py
│   │   └── test_constraints.py
│   └── integration/
│       └── test_scan_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular `code/` directory with separation of concerns (`physics`, `scan`, `validation`, `reporting`) ensures maintainability and testability. The `data/` directory strictly separates raw external inputs from processed outputs, adhering to Constitution Principle III.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Pre-computed Lookup Tables (FR-011) | Real-time Boltzmann integration for large-scale point sets exceeds practical time constraints on a 2-core CPU. | Direct integration for every point would take hours, violating SC-001. |
| Hardcoded Xenon1T Curves (FR-003) | No verified live URL for the specific 2014 curve; live fetch is optional fallback only. | Relying on a guessed URL would violate Constitution II (Verified Accuracy). |
| Linear Interpolation (FR-011) | Balances speed and accuracy; higher-order interpolation adds negligible benefit vs. lookup noise. | Cubic interpolation adds complexity without significant accuracy gain for this physics regime. |
| Convolution for Xenon1T (FR-015) | Helm form factor multiplication is physically incorrect for 1/q^4 interactions. | Simple multiplication would yield orders-of-magnitude errors. |

## Phase Breakdown & FR/SC Mapping

### Phase 0: Research & Data Strategy
- **Goal**: Verify dataset availability and define physics constants.
- **FR/SC Mapping**:
  - FR-002, FR-014: Validate Hulthen potential implementation strategy.
  - FR-003, FR-004: Confirm LEP and Xenon1T data sources.
  - SC-002: Define benchmark points for validation.
  - **Task 0.1**: Run Reference-Validator Agent on all citations.
  - **Task 0.2**: Implement numerical Yukawa potential solver for validation.
  - **Task 0.3**: Define Adaptive Mesh Refinement (AMR) strategy for grid convergence.

### Phase 1: Data Model & Contracts
- **Goal**: Define schemas for inputs/outputs.
- **FR/SC Mapping**:
  - FR-001, FR-005: Define `ParameterPoint` schema.
  - FR-007: Define `ConstraintDataset` schema.
  - SC-004: Define output image formats.
  - **Task 1.1**: Generate and validate `LEP_Exclusion_Data` schema.
  - **Task 1.2**: Define `RelicLookupTable` schema.

### Phase 2: Core Physics Implementation
- **Goal**: Implement analytic and numeric functions.
- **FR/SC Mapping**:
  - FR-001: `delta_a_mu.py` (analytic).
  - FR-002, FR-010, FR-014: `relic_density.py` (RK4, Sommerfeld, validation).
  - FR-003, FR-015: `cross_section.py` (convolution method).
  - FR-004: `constraints.py` (LEP/Xenon1T logic).
  - SC-002, SC-007, SC-008: Validation scripts.
  - **Task 2.1**: Implement analytic $\Delta a_\mu$ with corrected benchmark point.
  - **Task 2.2**: Implement RK4 integration for relic density.
  - **Task 2.3**: Implement LEP constraint logic and validate `LEP_Exclusion_Data` schema.
  - **Task 2.4**: Implement convolution method for Xenon1T limits (FR-015).
  - **Task 2.5**: Implement numerical Yukawa solver and validate Hulthen approximation (FR-014, SC-007, SC-008).
  - **Task 2.6**: Implement logic to flag "physically undefined" points (FR-013).

### Phase 3: Scan Pipeline & Optimization
- **Goal**: Build the grid and interpolation system.
- **FR/SC Mapping**:
  - FR-012: Grid convergence study logic (AMR).
  - FR-011: Lookup table generation and interpolation.
  - FR-005: Constraint application logic.
  - SC-001: Optimize for 30min runtime.
  - **Task 3.1**: Generate lookup tables using Hulthen approximation.
  - **Task 3.2**: Implement Adaptive Mesh Refinement (AMR) for grid convergence (FR-012).
  - **Task 3.3**: Implement main scan loop with interpolation.
  - **Task 3.4**: Apply constraints and generate `ParameterPoint` objects (FR-005, `parameter_point.schema.yaml`).

### Phase 4: Reporting & Visualization
- **Goal**: Generate plots and PDF report.
- **FR/SC Mapping**:
  - FR-006: Contour plots.
  - FR-007: Reproducibility log.
  - FR-008: Ensure no multiplicity corrections.
  - US-3, SC-005: PDF generation.
  - SC-004: Ensure 300 DPI plots.
  - **Task 4.1**: Generate contour plots with correct labels and legends.
  - **Task 4.2**: Generate PDF report with reproducibility section.
  - **Task 4.3**: Run Reference-Validator Agent on final report citations.
  - **Task 4.4**: Log configuration and data checksums (FR-007).