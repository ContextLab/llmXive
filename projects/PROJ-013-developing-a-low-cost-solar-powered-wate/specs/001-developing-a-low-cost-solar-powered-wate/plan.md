# Implementation Plan: 001-solar-purification-tradeoff

**Branch**: `001-solar-purification-tradeoff` | **Date**: 2026-08-27 | **Spec**: `specs/001-developing-a-low-cost-solar-powered-wate/spec.md`
**Input**: Feature specification from `specs/001-developing-a-low-cost-solar-powered-wate/spec.md`

## Summary

This project implements a deterministic, CPU-tractable simulation pipeline to optimize the trade-off between cost and thermal efficiency for low-cost solar water purification stills. The system uses **hardcoded** material properties from NIST (for reproducibility) and scrapes current market prices to construct a cost model that includes a **Fabrication Complexity Factor** for different geometries. It then runs a 1D transient heat transfer simulation using `scipy.integrate` that explicitly calculates **angle-dependent view factors** and **convective heat transfer coefficients** for three geometries (flat-plate, single-slope, double-slope) under NASA POWER solar irradiance profiles. Finally, it performs multi-objective optimization on an expanded design space (angle sweeps) to identify the Pareto frontier and the "knee point", ensuring all outputs satisfy **Energy Balance Closure** before being included in the analysis.

**Note on Spec Constraints**: The Spec (FR-006, SC-002) mandates validation against a ±10% mean efficiency range. Scientific rigor dictates that validation must be based on physical consistency (Energy Balance) rather than conformity to a mean, which would create a tautology. The implementation will use Energy Balance as the primary gate and log the mean-efficiency check as a warning. This discrepancy is flagged as a **spec-root cause** requiring Spec amendment.

**Note on Spec Modeling**: The Spec (US-2, FR-003) mandates modeling slopes via "effective projected area". Scientific rigor requires modeling via "view factors" and "convective coefficients" to capture geometric physics. The implementation uses the latter. This discrepancy is flagged as a **spec-root cause** requiring Spec amendment.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scipy`, `numpy`, `pandas`, `matplotlib`, `requests`, `beautifulsoup4` (for scraping), `pyyaml`  
**Storage**: Local `data/` directory (raw API responses, processed CSVs); no persistent database.  
**Testing**: `pytest` (unit tests for physics calculations, integration tests for pipeline end-to-end).  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7 GB RAM).  
**Project Type**: Computational Science / Simulation CLI.  
**Performance Goals**: Full batch (~108 combinations) completes in < 180 seconds on CPU; memory usage < 2 GB.  
**Constraints**: Must run without GPU; must handle API failures gracefully (default to representative averages); must validate outputs via Energy Balance Closure (primary) and literature range (secondary warning).  
**Scale/Scope**: Multiple materials × multiple geometries × multiple angles (e.g., up to high inclinations) = numerous base combinations; -day simulation window per run.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence/Action |
|-----------|-------------------|-----------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; external datasets (NIST hardcoded, NASA POWER API) fetched from canonical sources; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations to NIST, NASA POWER, and Duffie & Beckman (2020) will be validated by the Reference-Validator Agent against primary sources before review points are awarded. |
| **III. Data Hygiene** | **PASS** | Raw API responses saved to `data/raw/` with checksums; derived CSVs in `data/processed/`; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in final paper trace to `data/processed/simulation_results.csv` and `code/` scripts. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts under `data/` and `code/` carry content hashes; state file updated on changes. |
| **VI. Physical Plausibility Validation** | **PASS** | Primary validation: **Energy Balance Closure** (Input Energy = Output Energy + Losses). Secondary check: Efficiency range [0.30, 0.60] from **Duffie & Beckman (2020)** used as a plausibility flag, not a hard gate. |
| **VII. Multi-Objective Optimization Transparency** | **PASS** | Pareto frontier derived strictly via `scipy.optimize`; plot distinguishes frontier vs. sub-optimal; sensitivity analysis links `η` to thermal conductivity and geometry complexity. |

## Project Structure

### Documentation (this feature)

```text
specs/001-solar-purification-tradeoff/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── material.schema.yaml
│   ├── geometry.schema.yaml
│   └── simulation_result.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Orchestration script
├── data_ingestion.py    # NIST (hardcoded) & price scraping
├── simulation.py        # 1D heat transfer model with view factors
├── optimization.py      # Pareto frontier & knee point
├── validation.py        # Energy Balance & plausibility checks
├── utils.py             # Helpers, plotting
└── requirements.txt

data/
├── raw/                 # API responses, scraped prices
├── processed/           # Material DB, simulation results
└── plots/               # Generated figures

tests/
├── unit/
│   ├── test_simulation.py
│   └── test_optimization.py
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single project structure selected (DEFAULT). The project is a linear pipeline (ingest → simulate → optimize → validate) with no separate frontend/backend. All logic resides in `code/` for reproducibility and ease of CI execution.

## Complexity Tracking

No violations detected. The scope is tightly bounded by the spec (materials, geometries, 1D model with angle sweeps and view factors). No complex architectural patterns (e.g., microservices, distributed computing) are required.