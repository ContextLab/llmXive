# Implementation Plan: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

**Branch**: `001-quantifying-grain-boundary-segregation` | **Date**: 2026-07-25 | **Spec**: `specs/001-quantifying-grain-boundary-segregation/spec.md`
**Input**: Feature specification from `specs/001-quantifying-grain-boundary-segregation/spec.md`

## Summary

This project implements a computational pipeline to quantify composition-dependent grain boundary (GB) segregation in BCC alloys (Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, Fe-Mo-W). The core approach combines a **CPU-tractable surrogate** for DFT segregation energies (using `pymatgen` for geometry and a calibrated empirical model) with the McLean isotherm model to predict equilibrium GB concentrations. The plan addresses the non-linear "cooperative effects" of multicomponent systems by fitting empirical regression models with interaction terms, validated via 5-fold cross-validation. 

**Critical Deviation Note**: The source specification (`spec.md`) requires the use of the proprietary TCFE9 database and full Quantum ESPRESSO DFT calculations. As these are infeasible for a public GitHub Actions free-tier runner (license restrictions and CPU time limits), this plan substitutes:
1.  **Thermodynamics**: An open thermodynamic proxy (e.g., `pycalphad` open databases) consistent with TCFE9 logic.
2.  **DFT**: A literature-calibrated surrogate model for segregation energies.
3.  **Scope**: The project focuses on **Methodological Validation**—proving the pipeline can detect non-linear cooperative effects in a controlled environment—rather than claiming absolute physical quantification of ternary systems without real ternary data.

The implementation strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and consistency.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen`, `ase`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `pycalphad`, `pyyaml`, `requests`.  
**Storage**: Local file system (`data/` for raw/calculated data, `data_manifest.json` for tracking).  
**Testing**: `pytest` (unit tests for McLean calculation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple vCPU, ~7 GB RAM).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: Complete full pipeline (ternary systems, 500-900K range) within 6 hours.  
**Constraints**: CPU-only execution; memory < 7 GB; no GPU access on primary runner.  
**Scale/Scope**: 5 ternary systems, A sufficient number of data points per system (composition/temperature grid).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

1.  **Reproducibility (NON-NEGOTIABLE)**: Plan ensures `random_seed` is pinned in `code/` and external datasets (Open Proxy, surrogate parameters) are fetched/generated from canonical sources with checksums.
    *   *Action*: `data_manifest.json` will track source URLs, generation script hashes, and parameter checksums.
2.  **Verified Accuracy**: Citations for Open Proxy logic and literature experimental values (SC-003) will be validated against primary sources. For synthetic/proxy data, the *generation parameters* are validated against the intended primary source logic.
    *   *Action*: Research phase will verify Open Proxy availability and APT literature sources.
3.  **Data Hygiene**: All data transformations (Surrogate -> McLean -> Regression) will produce new files; raw data remains immutable.
    *   *Action*: Pipeline will append `_v1`, `_v2` to derived filenames.
4.  **Single Source of Truth**: All figures and stats in the final output will trace to specific rows in `data/` and blocks in `code/`.
    *   *Action*: Data model will enforce strict schema for `SegregationProfile`.
5.  **Versioning Discipline**: Artifacts will carry content hashes; `state/` files updated on change.
    *   *Action*: Implementation will include a hash utility to update `state/projects/PROJ-448-quantifying-composition-dependent-grain-.yaml` `artifact_hashes` map.
6.  **Computational Thermodynamics Consistency**: Surrogate inputs and McLean parameters will be explicitly documented to align with Open Proxy logic.
    *   *Action*: `research.md` will detail the Open Proxy version and temperature range alignment.
7.  **Multicomponent Interaction Validation**: Regression models will include interaction terms and be validated via k-fold (k=5) with p<0.05 thresholds.
    *   *Action*: `data-model.md` defines the `RegressionModel` entity; `plan.md` Phase 3 details the validation logic.

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-grain-boundary-segregation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-448-quantifying-composition-dependent-grain-/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, constants
│   ├── data/                  # Data loading and management
│   │   ├── loader.py          # Open Proxy and surrogate data ingestion
│   │   └── manifest.py        # Data manifest generation with hashes
│   ├── models/
│   │   ├── mclean.py          # McLean isotherm implementation
│   │   ├── regression.py      # Linear regression with interaction terms
│   │   └── validation.py      # Cross-validation logic
│   ├── services/
│   │   ├── surrogate_service.py  # Surrogate DFT energy calculation (CPU-tractable)
│   │   └── gb_service.py      # GB supercell generation (pymatgen)
│   └── cli/
│       └── main.py            # Pipeline entry point
├── data/
│   ├── raw/                   # Downloaded Open Proxy, surrogate parameters
│   ├── processed/             # Segregation profiles, regression results
│   └── data_manifest.json
├── tests/
│   ├── unit/
│   │   └── test_mclean.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity and tight coupling between data, models, and CLI. No frontend/backend split required for a computational research pipeline.

## Complexity Tracking

*No violations found in Constitution Check. Complexity is managed by strict phase ordering and CPU-first constraints.*

## Phases

### Phase 0: Research & Data Strategy
*   **Goal**: Verify data availability (Open Proxy, surrogate parameters, APT literature) and define the computational strategy.
*   **FR-001, FR-002, FR-003, SC-003**: Investigate Open Proxy and APT data sources. Define the surrogate energy model and the **Interaction Injection Mechanism**.
*   **Output**: `research.md`.

### Phase 1: Data Model & Contracts
*   **Goal**: Define schemas for `SegregationProfile`, `AlloySystem`, and `RegressionModel`. Ensure contracts allow for 'proxy' sources and ground-truth interaction terms.
*   **FR-007, SC-001, SC-002**: Define JSON/YAML contracts for data validation.
*   **Output**: `data-model.md`, `quickstart.md`, `contracts/`.

### Phase 2: Implementation
*   **Goal**: Build the pipeline (Data loading -> Surrogate/McLean -> Regression -> Validation).
*   **FR-001 to FR-006**: Implement core logic.
*   **Output**: `code/` directory.

### Phase 3: Execution & Validation
*   **Goal**: Run the pipeline, generate heatmaps, and validate against SC-001 to SC-004.
*   **FR-004, FR-005, SC-004**: Execute cross-validation and MSE reduction checks. Update state file hashes.
*   **Output**: Final results and figures.

### Note on Spec Deviations
*   **TCFE9**: The spec requires TCFE9. This plan uses an Open Proxy. The `data_manifest.json` will explicitly flag this deviation.
*   **DFT Convergence**: The spec includes DFT convergence edge cases. As this plan uses a surrogate model, these edge cases are superseded by surrogate generation logic. The code will not implement DFT retry logic.