# Implementation Plan: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

**Branch**: `001-leptophilic-dm-g2` | **Date**: 2026-06-24 | **Spec**: `specs/001-leptophilic-dm-g2/spec.md`
**Input**: Feature specification from `/specs/001-leptophilic-dm-g2/spec.md`

## Summary

This project implements a parameter scan for a minimal leptophilic dark matter model to determine if it can simultaneously resolve the muon $(g-2)$ anomaly and satisfy cosmological (Planck), direct-detection (Xenon1T long-range), and collider (LEP) constraints. The approach involves computing one-loop $\Delta a_\mu$, numerical relic density integration with Sommerfeld enhancement (with thermal averaging), and loop-induced spin-independent scattering, all constrained to a 2-core CPU runner with strict runtime limits (≤30 mins) via a two-stage adaptive scanning strategy. The Xenon constraint uses a static, versioned CSV file derived from the 2014 reference, verified at runtime.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scipy` (numerical integration), `numpy` (array ops), `matplotlib` (plotting), `pandas` (data handling), `requests` (data fetching), `reportlab` (PDF generation). No GPU libraries.  
**Storage**: Local `data/` directory for cached external limits; `code/` for scripts.  
**Testing**: `pytest` for unit tests (benchmark validation) and integration tests (scan completion).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`), CPU-only.  
**Project Type**: Scientific computing / CLI tool.  
**Performance Goals**: Full grid scan ≤ 30 minutes on 2 CPU cores; memory footprint < 2 GB.  
**Constraints**: No GPU/CUDA; no heavy LLM training; strict adherence to spec-defined physics formulas; dataset availability must be verified at runtime.  
**Scale/Scope**: Two-stage adaptive scan: Stage 1 (coarse grid: a low-resolution discretization) to identify candidates; Stage (local refinement: ~50 points per candidate region) to resolve narrow viable bands. Generation of CSV, PNG, and PDF files. Pre-computed lookup tables for Sommerfeld and relic density integrals are used *only* for the coarse grid; refinement is performed on-the-fly.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | `requirements.txt` will pin versions. `run_scan.py` will accept a `--seed` flag (default fixed). Data fetching will use hardcoded canonical URLs (LEP) and explicit checksums for Xenon1T/Planck if available. |
| **II. Verified Accuracy** | ✅ Pass | All citations in `research.md` will be validated against the "Verified datasets" block. The Xenon limit is derived from the leptophilic DM paper (Ref. [2014]), which is the verified source for this specific model. The LEP data URL is provided. The `data/xenon1t_limits_2014.csv` file is a static, versioned artifact with a recorded SHA-256 checksum, ensuring verified accuracy. |
| **III. Data Hygiene** | ✅ Pass | External data files will be saved to `data/` with SHA-256 checksums recorded in a `data_manifest.json`. The `download_data.py` script will verify checksums against the manifest before processing. If a checksum mismatch occurs, the script will abort with a clear error message. The `xenon1t_limits_2014.csv` file is included in the repo and verified at runtime. |
| **IV. Single Source of Truth** | ✅ Pass | All plots and tables in the final PDF will be generated programmatically from the `viable_points.csv` and `summary.txt`. No manual entry. |
| **V. Versioning Discipline** | ✅ Pass | `code/` scripts will output their own SHA-256 hash into the PDF report. |
| **VI. Analytic-Numeric Consistency** | ✅ Pass | `validate_delta_a.py` will run against the benchmark point (MeV, 100 MeV, $10^{-3}$) with a 2% tolerance check before the full scan proceeds. A separate validation step for the Sommerfeld calculation against a non-perturbative solver will also be performed. |
| **VII. Phenomenological Constraint Integrity** | ✅ Pass | The plan will explicitly code the constraints from Planck., Xenon1T (long-range limit from 2014 paper, stored in `data/xenon1t_limits_2014.csv`), and LEP (lookup from JSON) as defined in the spec. The Xenon limit is the specific long-range curve from the 2014 paper. No alternative datasets are used. |

## Project Structure

### Documentation (this feature)

```text
specs/001-leptophilic-dm-g2/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset_schema.yaml
│   └── output_schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── physics/
│   ├── __init__.py
│   ├── delta_a_mu.py       # FR-001: One-loop calculation
│   ├── relic_density.py    # FR-002: Boltzmann + Sommerfeld + Thermal Averaging
│   ├── scattering.py       # FR-003: Sigma_SI calculation + Nucleon Conversion
│   ├── constraints.py      # FR-004/005: Constraint logic
│   └── lookup_tables.py    # Pre-computed tables for coarse grid
├── data/
│   ├── lepaute_data.json   # LEP constraints (downloaded)
│   ├── xenon1t_limits_2014.csv  # Xenon1T long-range limits (static, versioned)
│   └── planck_limits.json  # Planck constant
├── scripts/
│   ├── run_scan.py         # Main scanner (FR-001, 005, 006) - Two-stage
│   ├── validate_delta_a.py # Validation (US-2)
│   ├── validate_sommerfeld.py # Sommerfeld validation
│   ├── make_report.py      # Report generation (US-3)
│   └── download_data.py    # Data fetching with checksums
├── utils/
│   ├── logging.py
│   └── plot_utils.py
├── requirements.txt
└── README.md

tests/
├── unit/
│   ├── test_delta_a_mu.py
│   ├── test_sommerfeld.py
│   └── test_constraints.py
└── integration/
    └── test_scan.py
```

**Structure Decision**: Single project structure (`code/`) selected to minimize overhead for a scientific calculation script. Separation of `physics/` logic from `scripts/` ensures testability and reproducibility. `data/` is distinct for hygiene. `lookup_tables.py` is added for performance optimization.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Two-Stage Adaptive Scan** | Required to capture narrow viable bands (resonances) without excessive runtime. | A fixed fine grid would exceed the 30-minute runtime constraint. A fixed coarse grid risks missing viable regions. |
| **Pre-computed Lookup Tables (Coarse Only)** | Required to perform numerical integration of the Boltzmann equation with Sommerfeld enhancement for the coarse grid within 30 minutes. | Performing the full numerical integration for every point in the coarse grid is necessary for accuracy, but limited to 1000 points to fit runtime. |
| **Sommerfeld Validation** | Required to ensure the Hulthen approximation is accurate for the parameter space. | Relying solely on the approximation without validation risks systematic errors that could invalidate the results. |
| **Nucleon-Level Conversion** | Required to correctly compare the leptophilic model's cross-section to Xenon1T limits. | Using the standard contact-interaction limit would be a category error and physically invalid. |
| **Thermal Averaging** | Required to correctly calculate the relic density in the early universe. | Using a fixed velocity approximation is a known methodological error for light mediators. |
| **On-the-Fly Refinement** | Required to resolve narrow viable bands identified by the coarse grid. | Pre-computing tables for the refinement density would exceed the 30-minute budget. The number of refinement points is small enough for on-the-fly calculation. |
