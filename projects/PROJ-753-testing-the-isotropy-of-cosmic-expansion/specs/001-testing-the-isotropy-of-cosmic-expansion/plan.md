# Implementation Plan: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

**Branch**: `001-testing-isotropy-cosmic-expansion` | **Date**: 2026-06-30 | **Spec**: `specs/001-testing-the-isotropy-of-cosmic-expansion/spec.md`
**Input**: Feature specification from `/specs/001-testing-the-isotropy-of-cosmic-expansion/spec.md`

## Summary

This project implements a rigorous statistical test for the isotropy of cosmic expansion using the Pantheon+ Type Ia Supernova dataset. The approach involves ingesting the Pantheon+ release, calculating distance-modulus residuals against a model-independent spline fit to the Hubble diagram (to avoid residualization bias), projecting these residuals onto a HEALPix grid (Nside=16), and extracting dipole ($\ell=1$) and quadrupole ($\ell=2$) amplitudes via the pseudo-$C_\ell$ method with MASTER correction. Statistical significance is assessed by comparing observed amplitudes against a null distribution generated via random 3D rotation of celestial coordinates, preserving redshift and selection probability distributions. The implementation strictly adheres to the functional requirements (FR-001 to FR-006) and addresses all unresolved panel concerns by adjusting HEALPix resolution, refining mask definition, correcting convergence criteria, and adding explicit constitutional compliance steps.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `astropy`, `healpy`, `numpy`, `scipy`, `pandas`, `matplotlib`, `pytest`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/reports`)  
**Testing**: `pytest` with unit tests for residual calculation, spherical harmonic decomposition, and simulation logic.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7 GB RAM, no GPU).  
**Project Type**: Scientific CLI / Data Analysis Pipeline  
**Performance Goals**: Full analysis (including 10,000 simulations) must complete within 6 hours on CPU-only hardware.  
**Constraints**: No GPU usage; no deep learning models; strict memory limits (~7 GB RAM); deterministic results via fixed seeds.  
**Scale/Scope**: [deferred] supernovae in Pantheon+ sample; ~10,000 Monte Carlo simulations.

> The Pantheon+ dataset contains a large sample of supernovae, but after filtering for valid RA, Dec, redshift, and distance modulus, the effective sample size is expected to be a substantial subset. The HEALPix resolution is set to Nside=16 ([deferred] pixels) to ensure sufficient average occupancy (~0.5 SNe/pixel) for stable pseudo-$C_\ell$ estimation, addressing sparsity concerns. The simulation count (N=10,000) is a target, but the loop will continue until p-value convergence is met or the runtime limit is reached.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds are pinned (seed=42). External datasets are fetched from the canonical Pantheon+ repository. Code is runnable end-to-end on a fresh runner.
- **II. Verified Accuracy**: Citations to the Pantheon+ paper and HEALPix documentation are verified against primary sources. **Task Added**: Phase 0 includes running the Reference-Validator Agent on all citations.
- **III. Data Hygiene**: Raw data is checksummed; transformations produce new files with documented derivations. **Task Added**: Phase 0 includes checksumming raw data and recording in `state/` map.
- **IV. Single Source of Truth**: All figures and statistics trace back to `data/processed` artifacts and `code/` blocks.
- **V. Versioning Discipline**: Content hashes are recorded for all artifacts. **Task Added**: Phase 4 includes generating and recording artifact hashes in `state/` map.
- **VI. Anisotropy Signal Quantification**: Dipole and quadrupole amplitudes are the sole metrics for anisotropy claims, as mandated.
- **VII. Pantheon+ Data Versioning**: The specific release version is recorded in `data/` metadata.

**Violations Addressed**:
- Removed MLE and GRF implementations (Tasks T030, T031, T038, T039) as they were unbacked by FRs and contradicted the Spec.
- Removed "Update spec.md" task (T018) as spec changes require a formal amendment process.
- Clarified redshift filtering logic based on Spec assumptions (no arbitrary upper bound of 2.3).
- Defined simulation count (N=10,000) and mask threshold based on Spec requirements and standard practice.
- Adjusted HEALPix resolution to Nside=16 to address sparsity concerns.
- Updated residual calculation to use model-independent spline fit.
- Updated mask definition to use official Pantheon+ selection function.
- Added explicit tasks for constitutional compliance (checksums, hashes, citation validation).

## Project Structure

### Documentation (this feature)

```text
specs/001-testing-the-isotropy-of-cosmic-expansion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/
├── code/
│   ├── __init__.py
│   ├── ingestion.py           # FR-001, FR-002: Data download, parsing, residual calculation
│   ├── spherical_harmonics.py # FR-003, FR-004: HEALPix projection, pseudo-C_l, amplitude extraction
│   ├── simulations.py         # FR-005: Rotation-based null distribution generation
│   ├── analysis.py            # FR-006: Significance assessment, p-value calculation
│   └── utils.py               # Helper functions (cosmology, HEALPix masks)
├── data/
│   ├── raw/                   # Pantheon+ release files (checksummed)
│   ├── processed/             # residuals.csv, healpix_map.fits, simulation_results.csv
│   └── reports/               # Final analysis reports, plots
├── tests/
│   ├── test_ingestion.py
│   ├── test_spherical_harmonics.py
│   └── test_simulations.py
├── requirements.txt           # Pinned dependencies
└── README.md
```

**Structure Decision**: A single `code/` directory with modular scripts aligns with the CLI nature of the project and ensures all data flow is explicit. The `data/` directory is strictly separated into `raw` (immutable) and `processed` (derived).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The current structure is minimal and strictly follows the Spec. | No unnecessary complexity was introduced. |

## Phase Breakdown

### Phase 0: Research & Data Verification
- Verify Pantheon+ dataset availability and variable completeness (RA, Dec, z, $\mu$).
- Confirm HEALPix and `healpy` compatibility with CPU-only environment.
- Validate pseudo-$C_\ell$ method implementation strategy for sparse point source catalogs.
- **Task**: Run Reference-Validator Agent on all citations (Constitution Principle II).
- **Task**: Checksum raw data and record in `state/` map (Constitution Principle III).

### Phase 1: Data Model & Contracts
- Define schemas for `residuals.csv`, `healpix_map.fits`, and `simulation_results.csv`.
- Establish data contracts for input/output formats.
- **Task**: Create `data-model.md`.
- **Task**: Create `contracts/*.yaml` files.

### Phase 2: Implementation
- Implement ingestion and residual calculation (FR-001, FR-002).
- Implement HEALPix projection and pseudo-$C_\ell$ analysis (FR-003, FR-004).
- Implement rotation-based simulation loop (FR-005).
- Implement significance assessment and reporting (FR-006).

### Phase 3: Testing & Validation
- Unit tests for each component.
- Integration test with synthetic data (injected dipole).
- Convergence test for null distribution (SC-003).

### Phase 4: Execution & Reporting
- Run full analysis on Pantheon+ data.
- Generate final report with p-values and amplitude estimates.
- **Task**: Generate and record artifact hashes in `state/` map (Constitution Principle V).
- **Task**: Measure and record runtime in final report (SC-004).

### Phase 5: Final Review
- Review results against Spec and Constitution.
- Archive artifacts with checksums.
