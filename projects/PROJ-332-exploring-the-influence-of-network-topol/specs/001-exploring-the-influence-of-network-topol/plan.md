# Implementation Plan: Influence of Network Topology on Thermal Conductivity in Nanomaterials

**Branch**: `001-network-topology-thermal` | **Date**: 2026-06-25 | **Spec**: `spec.md`

## Summary

This feature implements a computational physics pipeline to investigate the relationship between the connectivity distribution of randomly assembled nanowire networks and their effective thermal conductivity. The system generates random geometric graphs (NetworkX), assigns thermal resistances based on bulk material properties and size-correction factors (Fuchs-Sondheimer), solves the Kirchhoff heat-flow equations via sparse linear algebra (SciPy), and performs statistical regression to identify scaling laws and percolation thresholds. The implementation strictly adheres to the -CPU/7GB-RAM constraints of the CI environment, ensuring all simulations, sensitivity analyses, and regression outputs are reproducible and numerically stable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (graph generation), `scipy` (sparse linear solvers, statsmodels), `numpy` (numerical ops), `pandas` (data handling), `pyyaml` (schema), `pytest` (testing).  
**Storage**: Local file system (`data/` for CSV logs, `data/raw/` for synthetic artifacts); no external database.  
**Testing**: `pytest` with contract tests against YAML schemas and unit tests for graph metrics/solver convergence.  
**Target Platform**: Linux (GitHub Actions Free Tier: Limited vCPU capacity, 7GB RAM, no GPU).  
**Project Type**: Computational research library / CLI pipeline.  
**Performance Goals**: Complete 100 simulations × 10 connectivity levels (1000 total) within 6 hours; solver convergence <1e-6 residual.  
**Constraints**: No GPU usage; memory footprint <7GB; strict adherence to NIST default values for missing standard materials; double-precision arithmetic only.  
**Scale/Scope**: Extensive synthetic network simulations; output includes regression tables, sensitivity reports, and percolation threshold identification.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence in Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds logged in CSV (FR-009); `requirements.txt` pins versions; no external data fetching (synthetic generation); deterministic solver. |
| **II. Verified Accuracy** | **PASS** | Material constants derived from NIST standards (FR-010); citations in `research.md` restricted to verified sources only. |
| **III. Data Hygiene** | **PASS** | Synthetic data generated in-place; `simulation_results.csv` checksummed *after* all aggregation steps (regression/sensitivity) via `update_state.py`; no modification of raw inputs (NIST defaults are read-only). |
| **IV. Single Source of Truth** | **PASS** | All statistics (scaling exponents, p-values) derived from `data/simulation_results.csv`; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | A dedicated `update_state.py` script calculates SHA-256 of `simulation_results.csv` and updates `state/projects/...yaml` after every run. |
| **VI. Numerical Stability** | **PASS** | Solver uses double-precision (`float64`); convergence tolerance enforced (FR-003); zero-resistance clamping (negligible thermal resistance) implemented. |
| **VII. Physical Units Consistency** | **PASS** | All conductivities converted to SI (W/(m·K)) before calculation; outputs reported in SI units. |

## Project Structure

### Documentation (this feature)

```text
specs/001-network-topology-thermal/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── simulation_result.schema.yaml
│   └── material_property.schema.yaml
└── tasks.md             # Phase 2 output (generated after plan approval)
```

**Note**: `tasks.md` is a Phase 2 artifact generated *after* this plan is approved and *before* implementation begins. It is not part of the current plan deliverables.

### Source Code (repository root)

```text
projects/PROJ-332-exploring-the-influence-of-network-topol/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── generate_networks.py      # FR-001, FR-004
│   ├── thermal_solver.py         # FR-002, FR-003, FR-011
│   ├── regression_analysis.py    # FR-005, FR-006
│   ├── sensitivity_analysis.py   # FR-007
│   ├── material_db.py            # FR-010
│   ├── update_state.py           # Constitution Principle V, III
│   └── main.py                   # Orchestration (FR-008, FR-009)
├── data/
│   ├── raw/                      # Synthetic network snapshots (if needed)
│   └── processed/
│       └── simulation_results.csv
├── tests/
│   ├── unit/
│   │   ├── test_network_gen.py
│   │   ├── test_solver.py
│   │   └── test_materials.py
│   ├── contract/
│   │   └── test_schemas.py
│   └── integration/
│       └── test_full_pipeline.py
└── specs/001-network-topology-thermal/
    └── ... (documentation files)
```

**Structure Decision**: Single project structure selected. The workflow is linear (Generate → Solve → Analyze → Report), making a monolithic `code/` directory with modular scripts the most efficient approach for a 2-CPU CI runner. No separate frontend/backend is required as the output is a CSV and a static report.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The plan adheres strictly to the spec's complexity. The 6-hour limit and 7GB RAM constraint necessitate a lightweight, CPU-only approach, which this structure supports. | N/A |
