# Implementation Plan: Mesh Network Supercomputer Using Pooled Idle Computing Resources

**Branch**: `001-mesh-supercomputer` | **Date**: 2026-07-31 | **Spec**: `specs/001-mesh-supercomputer/spec.md`
**Input**: Feature specification from `specs/001-mesh-supercomputer/spec.md`

## Summary

This project implements a physical testbed for a mesh network supercomputer that pools idle computing resources from heterogeneous consumer devices (laptops, Raspberry Pis, mobile devices) over a local Wi-Fi network. The system orchestrates Monte Carlo integration benchmarks, instruments nodes to capture wall-clock time, packet counts, and CPU utilization, and performs statistical regression analysis to validate scaling laws against the Ong & Motani theoretical capacity bounds. The implementation prioritizes reproducibility, data hygiene, and strict adherence to a time-constrained CI limit on free-tier runners.

**Key Methodological Update**: The project now includes a **Discrete-Event Simulation (DES)** phase. The physical testbed data will be used to calibrate and validate the simulation model, satisfying Constitution Principle VI. The statistical analysis uses Generalized Additive Models (GAMs) to capture non-linear interactions and redefines the outcome metric to avoid tautological regression.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `paramiko` (SSH orchestration), `scikit-learn` (regression/ANOVA), `pandas` (data manipulation), `pygam` (Generalized Additive Models), `statsmodels` (statistical testing), `pytest` (testing), `pyyaml` (configuration), `numpy` (numerical operations), `simpy` (discrete-event simulation)  
**Storage**: Local CSV/JSON logs, no external database required for CI execution  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions runner) for orchestration; remote Linux/ARM devices for workers  
**Project Type**: Research CLI / Orchestration System  
**Performance Goals**: Complete full parameter sweep and analysis within 6 hours; minimize coordination overhead in scheduling  
**Constraints**: Multiple CPU cores, sufficient RAM, Substantial disk space on CI; no GPU required (statistical analysis is CPU-tractable); physical testbed availability assumed for local runs but mocked for CI validation  
**Scale/Scope**: A heterogeneous set of nodes; multiple granularity settings (fine/medium/coarse); Multiple independent runs (Multiple replicates per Multiple configs + stress tests)  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action / Note |
|-----------|-------------------|---------------|
| **I. Reproducibility** | **COMPLIANT** | Random seeds pinned in `code/`; all external data (if any) fetched from canonical sources; `requirements.txt` pins dependencies. |
| **II. Verified Accuracy** | **COMPLIANT** | Ong & Motani (2007) citation will be validated against primary source; title overlap ≥ 0.7 enforced. |
| **III. Data Hygiene** | **COMPLIANT** | Raw execution logs preserved unchanged; derived statistics written to new files with checksums recorded in state YAML. |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures/statistics trace to `data/` rows and `code/` blocks; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **COMPLIANT** | Content hashes tracked; `updated_at` timestamps updated on artifact changes. |
| **VI. Simulation Fidelity and Validation** | **COMPLIANT** | **PHASE 4**: A discrete-event simulation model will be built and calibrated against the physical testbed data (a small-scale node cluster) to ensure internal state does not produce circular predictions. Validation requires comparing simulation outputs to the "golden" physical dataset. |
| **VII. Heterogeneity-Aware Scheduling** | **COMPLIANT** | Scheduler explicitly models CPU speed variance, latency, and dropout; regression captures interaction effects via GAMs. |

## Project Structure

### Current Artifacts (Inputs to this Review)

The following documents are the result of the planning phase and serve as inputs for the implementation:
- `plan.md` (This file)
- `research.md`
- `data-model.md`
- `quickstart.md`
- `contracts/` (Schema definitions)

### Source Code (Repository Root - Future Implementation)

```text
code/
├── orchestrator/
│   ├── __init__.py
│   ├── scheduler.py          # Dynamic task granularity logic
│   ├── node_manager.py       # SSH/heartbeat management
│   └── instrumentor.py       # tcpdump/mpstat collection
├── analysis/
│   ├── __init__.py
│   ├── regression.py         # GAM regression & ANOVA
│   └── theoretical_bound.py  # Ong & Motani (2007) validation
├── simulation/
│   ├── __init__.py
│   └── des_model.py          # Discrete-event simulation for validation
├── data/
│   ├── raw/                  # Raw execution logs (CSV)
│   └── processed/            # Aggregated metrics (JSON/CSV)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/             # Schema validation tests
└── requirements.txt
```

**Structure Decision**: Single project structure under `code/` chosen for simplicity and alignment with research CLI pattern. Orchestrator, analysis, and simulation modules separated for clarity. No frontend/backend split required as per Assumption about target users.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Simulation Model** | Required by Constitution Principle VI to validate internal state against physical reality. | A pure physical approach cannot scale to the full parameter space required for the final paper; simulation allows extrapolation once validated. |
| **GAMs over Linear Regression** | Required to capture non-linear interaction effects between heterogeneity and granularity (H1). | Linear models fail to detect inflection points and "sweet spots" in non-linear scaling laws. |

## Execution Strategy & CI Constraints

- **CI Mocking**: Unit and contract tests run on the GitHub Actions runner using mocked SSH nodes.
- **Physical Validation**: A dedicated "Physical Validation" job is triggered manually or via a gated CI step when physical hardware is available. This job runs the full parameter sweep on the real mesh.
- **Data Flow**: Physical data generated in the "Physical Validation" step is treated as the "Golden Dataset" and is used to calibrate the `des_model.py` simulation.
- **Time Budget**: 82 runs × [deferred]/run = [deferred]. This leaves a sufficient buffer for data aggregation, analysis, and simulation calibration, fitting within the 6-hour limit.