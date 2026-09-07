# Implementation Plan: Testing the Equivalence Principle with Satellite Laser Ranging

**Branch**: `001-testing-equivalence-principle` | **Date**: 2026-06-25 | **Spec**: `specs/001-testing-equivalence-principle/spec.md`
**Input**: Feature specification from `specs/001-testing-equivalence-principle/spec.md`

## Summary

This project implements a computational pipeline to test the Weak Equivalence Principle (WEP) using Satellite Laser Ranging (SLR) data. The primary requirement is to determine if geodetic satellites of differing composition (LAGEOS, Etalon, Starlette) exhibit measurable differential accelerations. The technical approach involves ingesting open SLR normal-point data, constructing high-fidelity dynamical models (geopotential, drag, SRP, relativity), and performing a **joint weighted least-squares estimation** to directly estimate the composition-dependent differential acceleration parameter ($a_c$) and the Eötvös parameter ($\eta$).

**Critical Methodological Note**: The original spec (FR-003) mandates "two separate weighted least-squares fits". This plan adopts a **Joint Estimation** strategy to avoid collinearity and numerical instability in the differential calculation. A formal **Spec Amendment** (see `Spec Amendment` section below) is required to update FR-003 before implementation proceeds. The plan includes a "Consistency Check" to validate the joint estimate against the separate-fit baseline.

The plan prioritizes CPU-tractable methods (scipy, numpy, classical statistics) to ensure feasibility on GitHub Actions free-tier runners, with a fallback to scaled-down GPU runs only if specific CUDA-accelerated solvers are strictly required (though classical orbit determination is primarily CPU-bound).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy` (least_squares), `pandas`, `astropy`, `huggingface_hub` (dataset loading), `pyyaml`, `pytest`  
**Storage**: Local filesystem (`data/`), GitHub Actions ephemeral storage  
**Testing**: `pytest` (unit, integration, contract validation)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`), CPU-first  
**Project Type**: Scientific computing / Data analysis pipeline  
**Performance Goals**: Complete full pipeline (ingestion, estimation, validation) on 1-year subset within 6 hours; memory usage < 7 GB.  
**Constraints**: No local GPU; must handle ILRS archive errors gracefully; strict adherence to Constitution (checksums in state YAML, verified URLs only).  
**Scale/Scope**: A small cohort of target satellites

The specific value to remove/generalize: 'small cohort'

Rewritten passage:
A small cohort of target satellites, multi-year data (streamed), Multiple geopotential models for sensitivity analysis, systematic error models.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Spec Amendment

**Requirement**: The following spec requirements are superseded or amended by this plan. A `spec_amendment_<ID>.md` artifact must be generated before implementation.

1.  **FR-003 (Separate vs. Joint Fits)**:
    *   *Original*: "System MUST perform two separate weighted least-squares fits... then calculate the differential acceleration."
    *   *Amendment*: "System MUST perform a **joint weighted least-squares estimation** for each satellite pair to directly estimate the differential acceleration parameter ($a_c$). A **Consistency Check** must be performed to verify that the joint estimate of $a_c$ is within 2-sigma of the difference of separate-fit estimates (calculated for validation only)."
    *   *Rationale*: Separate fits amplify numerical noise and fail to account for correlated errors between satellites in the same orbital regime. Joint estimation is scientifically superior and required for valid covariance propagation.

2.  **FR-001 (Data Source)**:
    *   *Original*: "System MUST download... for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette."
    *   *Amendment*: "System MUST attempt to download data for all five satellites. If a satellite is missing from the verified source, the system MUST log a 'Missing Data' warning, exclude that satellite from the differential analysis, and flag the final report as 'Incomplete'."
    *   *Rationale*: Strict adherence to the original requirement is impossible if the verified source lacks data. This amendment ensures feasibility while maintaining transparency.

3.  **FR-007 (Chi-Square Improvement)**:
    *   *Original*: "System MUST output a diagnostic report including the $\chi^2$ improvement..."
    *   *Amendment*: "System MUST output a diagnostic report including the **$\chi^2$ improvement** ($\Delta \chi^2 = \chi^2_{null} - \chi^2_{alt}$) as a primary metric, alongside the F-statistic and p-value."
    *   *Rationale*: Explicitly mandates the comparative metric required by the spec.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan ensures all random seeds are pinned in `code/` and external datasets are fetched from canonical sources (verified HF datasets and ILRS).
- **Principle II (Verified Accuracy)**: Plan explicitly rejects hardcoded URLs. Data ingestion will only proceed using URLs from the `# Verified datasets` block or programmatic loaders for those specific sources. The **official ILRS URL** is included in the verified block. If a required satellite (e.g., LAGEOS-1) has no verified source in the block, the plan mandates an explicit "Missing Data" state rather than fabrication. The Reference-Validator Agent MUST verify the HF dataset URL and the ILRS fallback URL before ingestion.
- **Principle III (Data Hygiene)**: Checksums will be written to `state/projects/PROJ-752-testing-the-equivalence-principle-with-s.yaml` under `artifact_hashes`, not to a local JSON file.
- **Principle IV (Single Source of Truth)**: All figures and statistics will be derived programmatically from `data/` and `code/`.
- **Principle V (Versioning)**: Content hashes for artifacts will be managed via the project state file.
- **Principle VI (Instrument Calibration)**: Preprocessing steps (outlier removal) will be documented in scripts under `code/` with recorded parameters.
- **Principle VII (Statistical Rigor)**: The plan includes explicit steps for confidence interval calculation, F-tests, Holm-Bonferroni correction (for the defined family of pairs), and sensitivity analysis (geopotential and systematic error sweep).

## Project Structure

### Documentation (this feature)

```text
specs/001-testing-equivalence-principle/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── normal_point.schema.yaml
    ├── orbit_solution.schema.yaml
    └── eotvos_result.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── ingestion.py       # Fetches SLR data from verified sources
│   └── preprocessing.py   # Cleaning, outlier removal, alignment
├── models/
│   ├── dynamics.py        # Dynamical model construction (geopotential, drag, SRP)
│   └── estimator.py       # Joint weighted least-squares solver
├── analysis/
│   ├── eotvos.py          # Calculation of η and confidence intervals
│   └── validation.py      # Sensitivity analysis, F-tests, BIC
├── utils/
│   ├── logging.py         # Standardized error handling and progress logging
│   └── checksums.py       # Helper to update state YAML with hashes
├── cli/
│   └── main.py            # Entry point orchestrating the pipeline
└── tests/
    ├── unit/
    ├── integration/
    └── contract/          # Validates outputs against schema.yaml

data/
├── raw/                   # Downloaded parquet files (read-only)
└── processed/             # Cleaned CSVs, residuals (derived)

state/
└── projects/
    └── PROJ-752-testing-the-equivalence-principle-with-s.yaml
```

**Structure Decision**: Selected a modular "src/data", "src/models", "src/analysis" structure to separate concerns (ingestion vs. modeling vs. statistics) and ensure testability. This aligns with the Constitution's requirement for reproducible, isolated code blocks.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Joint Estimation (vs Separate Fits) | Spec FR-003 initially suggested separate fits, but scientific rigor and the "Dataset-variable fit" constraint (avoiding collinearity issues in differential calculations) necessitate a joint estimation of the differential parameter $a_c$ directly. | Separate fits would require subtracting two large covariance matrices, amplifying numerical noise and failing to properly account for correlated errors between satellites in the same orbital regime. |
| Geopotential & Systematic Sweep | Required by FR-005 and SC-004 to ensure robustness against model misspecification. | A single geopotential model (e.g., GGM05C) is insufficient to claim a WEP limit, as unmodeled gravity errors could mimic a differential acceleration. |
| CPU-First Strategy | Target environment is GitHub Actions free-tier (no GPU). | GPU acceleration is unnecessary for classical orbit determination (linear algebra on <1M rows) and would introduce complexity (CUDA dependencies) that breaks the "CPU-first" feasibility constraint. |
| Simulation Validation | Required to avoid tautological validation. | Without an independent ground truth (simulated data with known injected $\eta$), the analysis can only confirm that the data is better fit by a model with an extra parameter, not that the WEP is violated. |