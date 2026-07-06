# Implementation Plan: Reconstructing Early Universe Phase Transitions from CMB B-Mode Polarization

**Branch**: `001-reconstructing-early-universe-phase-transitions` | **Date**: 2026-06-26 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-reconstructing-early-universe-phase-transitions/spec.md`

## Summary

This project implements a computational pipeline to distinguish causal, non-inflationary phase transitions from inflationary gravitational wave signals in CMB B-mode polarization data. The technical approach involves downloading Planck 2015 Q/U maps and BICEP/Keck power spectra, applying masks, deriving B-mode maps via spin-2 harmonic decomposition using `pyhealpix`, computing angular power spectra ($C_\ell^{BB}$), and performing Bayesian model comparison using Nested Sampling (`dynesty`) to calculate Bayes factors. The analysis is constrained to CPU-only execution on GitHub Actions free-tier runners.

**Critical Gating Mechanism**: Phase 0.5 (Synthetic Validation) is a mandatory, gated step. The pipeline **MUST NOT** proceed to process observational data (Phase 1) unless the synthetic validation successfully recovers known ground truth parameters for both Inflation and Phase Transition models AND correctly identifies the model type via Bayes factors. Failure at this stage halts the entire project.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pyhealpix`, `dynesty`, `emcee`, `numpy`, `scipy`, `requests`, `pyyaml`, `astropy`, `astroquery`
**Storage**: Local file system under `data/` (raw maps, masks, derived spectra)
**Testing**: `pytest` with synthetic data generation for validation
**Target Platform**: Linux (GitHub Actions runner)
**Project Type**: Computational Science / Data Analysis Pipeline
**Performance Goals**: Complete full analysis (download + fit + compare) within 6 hours on 2 vCPU, 7GB RAM.
**Constraints**: No GPU usage; no large model training; strict adherence to verified dataset URLs; CPU-tractable Nested Sampling and MCMC.
**Scale/Scope**: Full-sky analysis (Nside=64) split into independent patches for robustness checks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan ensures `random.seed` is pinned in `code/`; datasets fetched from canonical ESA/BICEP sources via `astroquery` and direct HTTPS; `requirements.txt` pins versions.
- **II. Verified Accuracy**: All dataset URLs in `research.md` are restricted to the verified list provided in the user prompt. No hallucinated URLs.
- **III. Data Hygiene**: Plan mandates checksums for all downloads in `data/`; raw data never modified in place.
- **IV. Single Source of Truth**: Output schemas (`contracts/`) define exact structure for derived data; paper figures will trace to these files.
- **V. Versioning Discipline**: Artifacts under `data/` and `code/` will carry content hashes; `state/` updated on changes.
- **VI. Simulation Validation**: Phase 0.5 includes a "Synthetic Data Generator" and "Validation Runner" that MUST pass before any observational data is processed. This includes a specific Phase Transition ground truth test.
- **VII. Statistical Model Comparison**: Plan explicitly implements Bayes factors via Nested Sampling (`dynesty`) as required by FR-006 (replacing TI for stability), with a rigorous validation protocol to ensure numerical stability and multi-modality handling.

## Project Structure

### Documentation (this feature)

```text
specs/001-reconstructing-early-universe-phase-transitions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset_schema.schema.yaml
│   ├── inference_results.schema.yaml
│   └── visualization_schema.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-499-reconstructing-early-universe-phase-tran/
├── data/
│   ├── raw/             # Downloaded Planck/BICEP maps and masks
│   ├── derived/         # Computed power spectra, masked maps
│   └── synthetic/       # Generated synthetic datasets for validation
├── code/
│   ├── __init__.py
│   ├── data_ingestion.py        # FR-001, FR-002
│   ├── spectrum_computation.py  # FR-003
│   ├── model_generation.py      # FR-004
│   ├── inference.py             # FR-005
│   ├── model_comparison.py      # FR-006
│   ├── validation.py            # FR-007, SC-004
│   ├── plotting.py              # Visualization (FR-007 extension)
│   └── utils.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── docs/
└── requirements.txt
```

**Structure Decision**: Single-project structure with clear separation of data (`data/`), logic (`code/`), and tests. This aligns with the "Computational Science" nature and ensures reproducibility via isolated virtual environments.

## Complexity Tracking

No violations detected. The complexity is managed by:
1. **CPU Constraints**: Using `dynesty` (Nested Sampling) with a limited number of live points (e.g., [deferred]) to ensure CPU feasibility and avoid the numerical instability of Thermodynamic Integration.
2.  **Data Size**: Using Nside=64 maps (manageable in RAM) rather than high-resolution Nside=2048 for the initial fitting, with a note to upscale only for final figure generation if needed.
3.  **Model Comparison**: Using Nested Sampling with adaptive stopping criteria and validation against a reduced parameter grid to ensure numerical stability and CPU feasibility.

## Phase Execution Order

1.  **Phase 0.5: Synthetic Validation (GATED)**
    -   Generate synthetic data for both Inflation ($r=0.01$) and Phase Transition ($E_{PT}=10^{15}$ GeV) ground truths.
    -   Run the full pipeline on synthetic data.
    -   **Gate**: Pipeline must recover parameters within a statistically consistent uncertainty range AND correctly identify the ground truth model via Bayes Factor.
    -   *Constitution VI Compliance*: This step MUST pass before observational data is touched. If it fails, the project halts.

2.  **Phase 1: Data Ingestion & Preprocessing**
    -   Download Planck 2015 Q/U maps and BICEP/Keck spectra via `astroquery`/`requests`.
    -   Apply masks and derive B-mode maps using `pyhealpix`.
    -   Compute $C_\ell^{BB}$.

3.  **Phase 2: Inference & Model Comparison**
    -   Run Nested Sampling (`dynesty`) for parameter estimation and evidence calculation.
    -   Compute Bayes Factors.
    -   Perform robustness checks (sky splitting, foreground marginalization).

4.  **Phase 3: Visualization & Reporting**
    -   Generate diagnostic plots (see `contracts/visualization_schema.schema.yaml`).
    -   Compile results into `data/derived/model_comparison_results.json`.