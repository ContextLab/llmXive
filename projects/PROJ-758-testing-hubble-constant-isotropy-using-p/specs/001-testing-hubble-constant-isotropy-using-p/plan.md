# Implementation Plan: Testing Hubble Constant Isotropy Using Pantheon Supernova Sample

**Branch**: `001-testing-hubble-constant-isotropy` | **Date**: 2026-07-06 | **Spec**: `specs/001-testing-hubble-constant-isotropy-using-p/spec.md`
**Input**: Feature specification from `/specs/001-testing-hubble-constant-isotropy-using-p/spec.md`

## Summary

This project implements a rigorous statistical test for the isotropy of the Hubble constant ($H_0$) using the Pantheon+ Type Ia supernova compilation. The primary requirement is to determine if locally measured $H_0$ shows statistically significant directional variation across the sky. The technical approach involves ingesting the Pantheon+ dataset, applying redshift cuts ($z < 0.15$) and quality flags, mapping supernovae to HEALPix pixels (Nside=4), estimating local and global $H_0$ via a linearized Hubble diagram approximation (for speed) and full non-linear fits (for final results), correcting for peculiar velocities, and quantifying anisotropy through spherical harmonic decomposition (dipole/quadrupole) validated by Monte Carlo simulations with False Discovery Rate (FDR) correction.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `astropy`, `healpy`, `scikit-learn`, `matplotlib`, `pecvel` (or equivalent implementation)
**Storage**: Local CSV/Parquet files under `data/` (raw and processed)
**Testing**: `pytest` with contract tests for data schemas
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)
**Project Type**: Computational Research / CLI
**Performance Goals**: Complete analysis (including A sufficient number of Monte Carlo iterations) within 6 hours; memory usage < 6 GB.
**Constraints**: No GPU; no heavy deep learning; dataset subset to fit RAM; strict adherence to Pantheon+ variable availability.
**Scale/Scope**: A substantial sample of supernovae in Pantheon+; ~192 HEALPix pixels at Nside=4; A substantial number of simulation runs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: The plan mandates pinned `requirements.txt`, random seed fixation in `code/`, and fetching external datasets from the canonical Zenodo source on every run.
2.  **II. Verified Accuracy**: The plan requires the Reference-Validator to verify all citations (e.g., Scolnic et al. 2021) against primary sources before review points are awarded.
3.  **III. Data Hygiene**: The plan specifies checksumming raw data, preserving raw files unchanged, and writing derivations to new filenames under `data/`.
4.  **IV. Single Source of Truth**: The plan ensures every figure and statistic traces back to exactly one row in `data/` and one block in `code/`, prohibiting hand-typed numbers.
5.  **V. Versioning Discipline**: The plan explicitly integrates content hashing for artifacts and **updates the `state/projects/PROJ-758-testing-hubble-constant-isotropy-using-p.yaml` file with the `updated_at` timestamp** upon any artifact change, as mandated by Principle V.
6.  **VI. Directional Consistency Verification**: The plan enforces identical methodology (Pantheon+ distance modulus) for both regional and global $H_0$ estimates to ensure spatial structure reflects genuine anisotropy, not methodological artifacts.
7.  **VII. Isotropy Outcome Rigor**: The plan treats both isotropy confirmation and anisotropy detection as scientifically valid outcomes, with distinct interpretative pathways for new physics vs. hidden systematics.

## Project Structure

### Documentation (this feature)

```text
specs/001-testing-hubble-constant-isotropy-using-p/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── ingestion/           # Data loading, cleaning, HEALPix mapping
│   ├── loader.py
│   └── spatial.py
├── analysis/            # H0 estimation, spherical harmonics
│   ├── h0_estimator.py
│   ├── anisotropy.py
│   └── simulations.py
├── utils/               # Logging, config, constants
│   └── constants.py
└── main.py              # CLI entry point

tests/
├── contract/            # Schema validation tests
├── integration/         # End-to-end pipeline tests
└── unit/                # Algorithmic unit tests

data/
├── raw/                 # Pantheon+ CSV (checksummed)
├── processed/           # Cleaned, HEALPix-mapped parquet
└── results/             # Monte Carlo outputs, plots

code/
└── requirements.txt     # Pinned dependencies
```

**Structure Decision**: A modular CLI structure (`src/`) is selected to separate data ingestion, analysis, and simulation logic. This supports the "Single Source of Truth" principle by isolating data transformation steps. The `tests/` directory is split into contract, integration, and unit tests to ensure data integrity and algorithmic correctness. The `data/` directory strictly separates raw (immutable) and processed (derived) files.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Monte Carlo Simulations (runs) | Required by FR-004 to establish a robust null distribution for anisotropy significance. | A single analytical p-value would not account for the complex selection function and non-Gaussian noise of the Pantheon+ sample. |
| HEALPix Nside=4 (192 pixels) | Balances spatial resolution with the number of supernovae per pixel (FR-002). | Lower resolution (Nside=2) loses directional detail; higher resolution (Nside=8) results in too many pixels with N < 30, requiring complex hierarchical modeling that exceeds CPU constraints. |
| Empirical Bayes Shrinkage | Required for pixels with N < 30 to ensure full-sky coverage (FR-003, Edge Cases). | "Skipping" low-N pixels creates a biased sky map (selection bias) and prevents robust dipole/quadrupole calculation. |
| Linearized H0 Approximation | Required for Monte Carlo simulations to fit within 6 hours on CPU. | Full non-linear cosmological fitting [deferred] times is computationally prohibitive (O(N^) matrix inversions) and risks timeout. |
| Benjamini-Hochberg FDR | Required by FR-006 to control family-wise error rate across dipole and quadrupole tests. | Simple Bonferroni correction is too conservative for correlated spherical harmonic modes, potentially masking real anisotropy. |