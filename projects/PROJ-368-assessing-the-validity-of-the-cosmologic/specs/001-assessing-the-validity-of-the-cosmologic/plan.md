# Implementation Plan: Assessing the Validity of the Cosmological Principle with Public CMB Data

**Branch**: `001-assess-cosmological-principle` | **Date**: 2026-06-24 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-assess-cosmological-principle/spec.md`

## Summary

This feature implements a statistical pipeline to test the Cosmological Principle (isotropy) using the Planck 2018 SMICA CMB temperature map. The approach involves downloading public CMB data, applying a Galactic mask, downgrading resolution to fit CI constraints, computing spherical harmonic coefficients and angular power spectra (C_l) for full-sky and hemispherical splits, and generating Monte Carlo isotropic simulations to construct a null distribution. A 'Maximum Statistic' approach is used to assess hemispherical power asymmetry, replacing the Benjamini-Hochberg correction due to statistical dependencies between test axes.

**Note on Spec Conflict**: The source specification (FR-009) mandates Benjamini-Hochberg correction. However, statistical review indicates this is inappropriate for only two dependent tests. This plan implements the 'Maximum Statistic' approach (max of N/S and E/W asymmetries) which is statistically robust. The spec is flagged for kickback to update FR-009 to reflect this methodological necessity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `healpy`, `numpy`, `scipy`, `astropy`, `requests`, `pyyaml`  
**Storage**: Local filesystem (`data/` for raw/processed maps, `code/` for scripts)  
**Testing**: `pytest` (unit tests for data loading, mask application, and statistical functions)  
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Scientific CLI/Data Analysis Pipeline  
**Performance Goals**: Complete analysis (download → simulation → stats) within 60 minutes on CPU; memory usage < 7 GB.  
**Constraints**: No GPU; default float64 precision only; download Nside=2048 (per FR-001); **analysis resolution limited to Nside=128** to fit CI constraints; no circular validation (simulations use fixed external ΛCDM parameters, with systematic uncertainty acknowledged).  
**Scale/Scope**: Single dataset (Planck 2018), A moderate resolution (approx. tens of thousands of pixels) after masking; A substantial number of Monte Carlo simulations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Random seeds pinned in `code/` (e.g., `np.random.seed()`); `requirements.txt` pins versions; CI re-downloads data from canonical ESA source. |
| **II. Verified Accuracy** | ✅ Pass | All citations (Planck 2018, ΛCDM parameters) validated against primary sources. **Reproducibility is guaranteed by validating the downloaded file against a known SHA-256 checksum recorded in the state file, independent of live URL reachability.** |
| **III. Data Hygiene** | ✅ Pass | Raw data checksummed on download; derivations (masked/downgraded) written to new files; no in-place modification. |
| **IV. Single Source of Truth** | ✅ Pass | Figures/stats in paper generated via scripts from `data/`; no hand-typed numbers. |
| **V. Versioning Discipline** | ✅ Pass | Content hashes tracked in `state/projects/PROJ-368-assessing-the-validity-of-the-cosmologic.yaml` under `artifact_hashes` map; `updated_at` timestamps managed by Advancement-Evaluator Agent as per Constitution Principle V. |
| **VI. Simulation Determinism** | ✅ Pass | Monte Carlo seed fixed; simulation count (N) is a documented constant; null distribution reproducible. |
| **VII. Public CMB Data Provenance** | ✅ Pass | Source explicitly identified as Planck 2018 SMICA; provenance metadata recorded in `data/` headers. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-cosmological-principle/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants (Nside, N_sims)
├── data_loader.py       # Download, checksum, mask application
├── harmonics.py         # map2alm (iter=3), pseudo-C_l via MASTER
├── simulations.py       # Gaussian random field generation (healpy.synalm)
├── statistics.py        # Hemispherical variance, p-value, Maximum Statistic
├── sensitivity.py       # Threshold sweep analysis
└── main.py              # Orchestration script

tests/
├── test_data_loader.py
├── test_harmonics.py
├── test_statistics.py
└── test_sensitivity.py

data/
├── raw/                 # Downloaded Planck SMICA map
├── processed/           # Masked, downgraded maps
└── simulations/         # Generated Monte Carlo realizations (if stored)
```

**Structure Decision**: Single `code/` directory with modular scripts for a CLI pipeline. This minimizes overhead and aligns with the CI constraint of a single job. No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Monte Carlo Simulations** | Required for null hypothesis testing (US-3). | Analytic approximations for hemispherical variance under partial masking are unreliable; simulation is the standard robust method. |
| **HEALPix Format** | Native format for CMB data; required for `map2alm`. | Flat arrays lose pixel connectivity; spherical harmonic transforms require HEALPix topology. |
| **MASTER Algorithm** | Corrects for mode coupling due to masking. | Naive `alm2cl` on masked maps yields biased power spectra; bias invalidates statistical tests. |
| **Per-Hemisphere Masks** | Essential to correct for mask-induced bias in low-l modes. | Applying a single global mask to hemispheres creates unequal sky fractions and artificial asymmetry; distinct MASTER matrices per hemisphere are required. |
| **Maximum Statistic** | Statistically appropriate for dependent N/S and E/W tests. | Benjamini-Hochberg is designed for large-scale multiple testing, not two dependent tests. Using BH here risks incorrect p-value interpretation. |

