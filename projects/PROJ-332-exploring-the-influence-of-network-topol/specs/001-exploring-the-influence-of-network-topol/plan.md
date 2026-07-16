# Implementation Plan: Influence of Network Topology on Thermal Conductivity in Nanomaterials

**Branch**: `001-network-topology-thermal` | **Date**: 2026-06-25 | **Spec**: `specs/001-network-topology-thermal/spec.md`
**Input**: Feature specification from `/specs/001-network-topology-thermal/spec.md`

## Summary

This project implements a synthetic simulation pipeline to quantify how the connectivity distribution of randomly assembled nanowire networks modulates effective thermal conductivity. The system generates random geometric graphs (NetworkX) with prescribed average node degrees within a fixed unit square domain, assigns thermal resistances based on material properties (NIST defaults + Fuchs-Sondheimer size correction), solves Kirchhoff heat-flow equations (SciPy linear solvers) with standardized boundary conditions (max-distance nodes), and performs statistical regression to identify scaling laws and percolation thresholds using critical scaling laws ($k_{eff} \propto (\langle k \rangle - \langle k \rangle_c)^t$). The pipeline is designed to run entirely on CPU within the 6-hour CI limit (2 cores, 7GB RAM) and adheres strictly to the project constitution regarding reproducibility and data hygiene.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx`, `scipy`, `numpy`, `pandas`, `matplotlib`, `pytest`  
**Storage**: Local filesystem (`data/` for CSV outputs, `code/` for scripts). No external database.  
**Testing**: `pytest` (unit tests for graph generation, solver convergence, and regression logic).  
**Target Platform**: Linux (GitHub Actions CPU runner).  
**Project Type**: Scientific simulation library / CLI tool.  
**Performance Goals**: Complete 100 simulations × 10 connectivity levels within 6 hours.
**Constraints**: No GPU usage; double-precision arithmetic only; strict adherence to NIST defaults for missing materials; runtime abort on convergence failure >1%.  
**Scale/Scope**: synthetic network graphs; **N=1000 nodes** per graph (default); parameter sweep for sensitivity analysis.  
**Timeout Mechanism**: A Python `signal`-based watchdog (Task T008) enforces the 6-hour limit.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Addressed by pinning `random_seed` in all generation tasks, logging all parameters to CSV, and ensuring `requirements.txt` pins exact versions. **No pre-staged data files**; `simulation_results.csv` is generated at runtime by the solver script (Task T015).
- **Principle II (Verified Accuracy)**: Material constants (Si, CNT, Ag, Au) are hardcoded to NIST standard reference values. Citations in `research.md` are restricted to verified URLs.
- **Principle III (Data Hygiene)**: `data/processed/simulation_results.csv` is **not** pre-created. It is created/overwritten by the main execution script (Task T015) upon successful completion. Checksums are recorded post-run.
- **Principle IV (Single Source of Truth)**: All figures and statistics in the final report will be generated directly from `data/processed/simulation_results.csv` via scripts in `code/analysis/`.
- **Principle V (Versioning Discipline)**: Artifact hashes will be computed for the final CSV and the `requirements.txt` at the end of the run, and the `state/projects/...yaml` file will be updated with the new hashes and timestamp.
- **Principle VI (Numerical Stability)**: The solver uses `scipy.sparse.linalg` with double precision and a hard `1e-6` residual tolerance. Non-convergent runs are logged and excluded from regression.
- **Principle VII (Physical Units Consistency)**: All conductivity inputs converted to SI (W/m·K) before edge resistance calculation. Output reported in W/m·K.

## Project Structure

### Documentation (this feature)

```text
specs/001-network-topology-thermal/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── simulation_result.schema.yaml
│   └── network_config.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point: orchestrates grid sweep, watchdog
├── config.py            # Material defaults (NIST), hyperparameters
├── models/
│   ├── __init__.py
│   └── network.py       # Graph generation (NetworkX)
├── services/
│   ├── __init__.py
│   ├── resistor.py      # Edge resistance calculation (Fuchs-Sondheimer)
│   ├── solver.py        # Kirchhoff solver (SciPy)
│   └── metrics.py       # Graph metrics (degree, path, clustering)
├── analysis/
│   ├── __init__.py
│   ├── regression.py    # OLS, scaling law fitting, percolation detection
│   └── sensitivity.py   # Resistance scaling sweep
├── utils/
│   ├── __init__.py
│   └── logging.py       # CSV output, seed management, checksums
└── tests/
    ├── test_network.py
    ├── test_solver.py
    └── test_regression.py

data/
└── processed/
    # Runtime directory only. No files pre-staged.
```

**Structure Decision**: Single project structure (Option 1). The project is a self-contained scientific simulation suite. No frontend/backend split is required as the output is a CSV and a report. All logic is modularized into `models`, `services`, and `analysis` for testability.

## Complexity Tracking

No violations identified. The complexity is managed by:
1.  **Modular Solver**: Separating graph generation, resistance assignment, and linear solving ensures numerical stability and independent testing.
2.  **Runtime Data Generation**: Eliminating pre-staged CSV files ensures data hygiene and reproducibility.
3.  **Strict Schema**: The `contracts/` schemas enforce that `percolation_threshold` is handled as a derived scalar, avoiding schema mismatches during CSV writes.
4.  **Timeout Enforcement**: A dedicated watchdog task ensures the 6-hour limit is respected.

## Implementation Phases

### Phase 1: Foundation & Configuration
- **T001**: Initialize Python project structure (`code/`, `data/`, `tests/`).
- **T002**: Create `requirements.txt` with verified dependencies (`networkx`, `scipy`, `numpy`, `pandas`, `matplotlib`, `pytest`). **Removed invalid `pi==0.0.1`**.
- **T003**: Implement `config.py` with NIST defaults and CLI argument parsing.
- **T004**: Implement material validation logic (FR-010) with specific error message for non-standard materials.

### Phase 2: Core Simulation Engine
- **T005**: Implement `models/network.py` for Random Geometric Graph generation.
  - **Constraint**: Domain fixed to unit square [0,1]x[0,1].
  - **Constraint**: Source/Sink selection: Max Euclidean distance pair.
- **T006**: Implement `services/resistor.py` for edge resistance (Fuchs-Sondheimer).
  - **Note**: Homogeneous diameter assumption documented as a construct validity limitation.
- **T007**: Implement `services/solver.py` for Kirchhoff heat flow.
  - **Constraint**: Double precision, residual <= 1e-6.
  - **Constraint**: Handle disconnected graphs (k_eff=0).
- **T008**: Implement `main.py` watchdog mechanism (signal-based) to enforce 6-hour runtime limit (FR-008).

### Phase 3: Data Generation & Logging
- **T009**: Implement Graph Generation with Target Degree Validation.
  - Consolidated logic for generation and validation.
  - Validate measured degree within ±5% of target.
- **T010**: Implement `utils/logging.py` for CSV output.
  - **Runtime Initialization**: Logic to create `data/processed/simulation_results.csv` header only if file missing (no pre-staged file).
- **T011**: Implement CLI argument `--k-value` for non-standard materials (FR-010).
- **T012**: Implement main grid sweep loop (100 sims x 10 levels).

### Phase 4: Analysis & Reporting
- **T013**: Implement `analysis/regression.py`.
  - **Method**: Calculate percolation threshold (P(connected)>=0.80).
  - **Method**: Fit $k_{eff} \propto (\langle k \rangle - \langle k \rangle_c)^t$ only for connected graphs.
  - **Method**: Handle $k_{eff}=0$ by exclusion from log-fit.
- **T014**: Implement `analysis/sensitivity.py` for scaling factor sweep.
- **T015**: Implement runtime CSV writing (T010 extension) to append results.
- **T016**: Generate Validation Report (SC-001): % graphs within ±5% target.
- **T017**: Generate Convergence Report (SC-002): % solver convergence.
- **T018**: Generate Sensitivity Report (SC-004): Max deviation check.
- **T019**: Generate Runtime Report (SC-005): Total time check.
- **T020**: Compute checksums and update `state/projects/...yaml` (Principle V).
- **T027a**: Implement storage of `percolation_threshold` into `simulation_results.csv` (Schema updated to include this column).

### Phase 5: Verification
- **T021**: Run full test suite (`pytest`).
- **T022**: Verify all SCs (001-005) are met in generated reports.
- **T023**: Final artifact hash computation.