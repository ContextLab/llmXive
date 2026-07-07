# Implementation Plan: Testing Cosmic Ray Arrival Direction Isotropy

**Branch**: `001-testing-cosmic-ray-arrival-direction-iso` | **Date**: 2026-06-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-testing-cosmic-ray-arrival-direction-iso/spec.md`

## Summary

This project tests the hypothesis that Ultra-High-Energy Cosmic Rays (UHECRs, E > 50 EeV) arrive isotropically from all directions. The approach involves ingesting public event catalogs from the Pierre Auger Observatory and Telescope Array, converting coordinates to HEALPix format (Nside=64), and computing the angular power spectrum ($C_\ell$) for multipoles $\ell=1$ to $5$. A global statistical significance test will be performed using 1,000 isotropic Monte Carlo simulations to control the false discovery rate at $\alpha=0.05$, strictly adhering to the project's reproducibility and data hygiene principles. The analysis utilizes the exposure-corrected intensity map ($N_{obs}/N_{exp}$) with explicit shot-noise subtraction to ensure statistical validity for low-count data, avoiding the bias introduced by simple residual subtraction.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `healpy`, `numpy`, `pandas`, `scipy`, `astropy`, `requests`, `tqdm`
**Storage**: Local filesystem (`data/raw/`, `data/processed/`), CSV/Parquet formats
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM, No GPU)
**Project Type**: Computational Physics / Data Analysis Pipeline
**Performance Goals**: Complete end-to-end analysis (including 1,000 MC simulations) within 6 hours on CPU-only runner.
**Constraints**: No GPU usage; memory footprint must remain < 7 GB; strict handling of missing data; **NO synthetic fallbacks** for primary scientific results.
**Scale/Scope**: Analysis of ~100-200 events (E > 50 EeV); Monte Carlo realizations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|:--- |:--- |
| **I. Reproducibility** | All random seeds pinned in `code/config.yaml`. External datasets fetched via deterministic scripts using specific DOIs/Release IDs (Auger:; TA: 2023-01). `requirements.txt` pins exact versions. Pipeline halts if data unavailable. |
| **II. Verified Accuracy** | Citations for detector exposure and statistical methods validated against primary sources (arXiv/observatory docs) before review. Specific dataset URLs verified. |
| **III. Data Hygiene** | Raw data downloaded to `data/raw/` with checksums recorded. Transformations create new files in `data/processed/`. No in-place edits. |
| **IV. Single Source of Truth** | All figures and statistics in the final report will be generated directly from `data/processed/` artifacts. |
| **V. Versioning** | Artifacts tracked via content hashes in `state/projects/...yaml`. |
| **VI. Simulation-Driven Null Validation** | Monte Carlo simulations use pinned seeds and documented exposure maps; simulation outputs treated as code artifacts. |

## Project Structure

### Documentation (this feature)

```text
specs/001-testing-cosmic-ray-arrival-direction-iso/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-772-testing-cosmic-ray-arrival-direction-iso/
├── code/
│ ├── __init__.py
│ ├── config.yaml # Pinned seeds, dataset versions, paths
│ ├── requirements.txt # Dependency pins
│ ├── ingestion/
│ │ ├── download_events.py # FR-001: Fetch Auger/TA data (Real data only)
│ │ └── preprocess.py # FR-001: Filter E>50, clean coords
│ ├── analysis/
│ │ ├── healpix_conversion.py # FR-002: RA/Dec -> HEALPix
│ │ ├── power_spectrum.py # FR-003: Compute C_l (with shot-noise correction)
│ │ └── monte_carlo.py # FR-004: Generate null distribution (N=1000)
│ ├── stats/
│ │ └── significance_test.py # FR-005: Global p-value calculation
│ └── main.py # Pipeline orchestrator
├── data/
│ ├── raw/ # Unmodified downloads (checksummed)
│ └── processed/ # HEALPix maps, exposure maps, results
└── tests/
 ├── unit/
 └── integration/
```

**Structure Decision**: Single project structure selected. The workflow is linear (Download -> Preprocess -> Analyze -> Test), making a monolithic `code/` directory with modular sub-packages the most efficient approach for a computational physics pipeline. This minimizes overhead and simplifies dependency management for the CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Monte Carlo Scale (1,000 sims)** | Required to estimate p-value at $\alpha=0.05$ within the 6-hour CI limit on a 2-CPU runner. N=1000 provides a standard error of ~0.022 for p=0.05, sufficient for the binary decision. A large number of simulations were identified as likely exceeding the 6-hour runtime limit. due to the cost of `map2alm` for Nside=64. | Reducing to <1000 would increase uncertainty too much; increasing to [deferred] would exceed the 6-hour runtime limit for `map2alm` on Nside=64. |
| **HEALPix Nside=64** | Balances angular resolution (approx 1 degree) with computational cost for spherical harmonic transforms. | Nside=128 would quadruple memory usage and computation time, risking timeout. Nside=32 would be too coarse for $\ell=5$ precision. |
| **Exposure Correction & Shot-Noise Subtraction** | Essential to distinguish true anisotropy from detector geometry and Poisson noise (US-2). Using $N_{obs}/N_{exp}$ and subtracting $1/N_{tot}$ avoids the non-stationary noise bias of simple residuals. | Ignoring exposure or noise bias leads to false positives; simple subtraction ($N_{obs}-N_{exp}$) is statistically invalid for low counts. |
| **No Synthetic Fallback** | The research question requires real UHECR data. | Synthetic data cannot answer the hypothesis about real cosmic ray arrival directions. |

## Data Source Pinning

To satisfy Constitution Principle I (Reproducibility) and Principle II (Verified Accuracy), the following canonical sources are pinned:

1. **Pierre Auger Observatory (Open Data 2020)**:
 * **DOI**: `` (Auger Open Data 2020 Release)
 * **URL**: `
 * **Content**: Event catalog (E > 50 EeV) and Exposure Map.
 * **Version**: `2020.1` (Pinned in `code/config.yaml`).

2. **Telescope Array (Public Data)**:
 * **URL**: `
 * **Content**: Event catalog (E > 50 EeV) and Exposure Map.
 * **Version**: `2023-01` (Pinned in `code/config.yaml` based on release date).

*Note: If these specific versions are unavailable, the pipeline will halt with a clear error message rather than proceeding with fallback data. Synthetic data is strictly prohibited for the primary scientific result.*

## Statistical Methodology Note

The analysis computes the Angular Power Spectrum from the **exposure-corrected intensity map** ($I = N_{obs}/N_{exp}$) rather than simple residuals ($N_{obs} - N_{exp}$). This is critical for low-count data (limited events) where Poisson noise dominates. The raw $C_\ell$ derived from the intensity map includes a shot-noise bias term ($1/N_{tot}$), which is explicitly subtracted to isolate the anisotropy signal. The null distribution is generated by simulating isotropic events *weighted by the exact same exposure map* and applying the same shot-noise subtraction, ensuring a valid comparison.