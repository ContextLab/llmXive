# Implementation Plan: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

**Branch**: `001-evaluating-the-impact-of-variable-select` | **Date**: 2026-06-26 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary

This project implements a simulation-based power analysis to evaluate how three variable selection methods (Forward Stepwise, Backward Elimination, LASSO) affect **Inference Power** (the proportion of true non-zero coefficients correctly identified as statistically significant with p < alpha after selection and OLS refitting) and **Selection Recovery** (the proportion of true non-zero coefficients correctly selected). The system will download a representative set of real-world regression datasets from OpenML (specifically IDs), extract their predictor covariance structures via bootstrapping, and simulate synthetic outcome vectors across a grid of Signal-to-Noise Ratios (SNR) and Sparsity levels. To ensure feasibility on the 2 vCPU, 7 GB RAM CI runner within 6 hours, the simulation count is set to 200 per condition (total 24,000 simulations), with algorithmic optimizations (early stopping for stepwise, predictor pruning) and a mandatory Pilot Run (T004) to verify runtime. The implementation adheres to strict reproducibility and data hygiene principles defined in the project constitution.

**Note on Metric Definition**: The study distinguishes between **Selection Recovery** (did the method pick the variable?) and **Inference Power** (is the coefficient significantly different from zero?). The primary metric for the research question is **Inference Power** (FR-004), despite the known bias in post-selection p-values. The study compares methods under this shared bias, not absolute validity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `openml` (dataset fetch), `scikit-learn` (selection methods, LASSO), `statsmodels` (OLS refitting, p-values), `scipy` (Kruskal-Wallis, Dunn's test), `pandas`/`numpy` (data manipulation), `matplotlib`/`seaborn` (visualization), `pytest` (testing), `tracemalloc` (memory monitoring).  
**Storage**: Local `data/` directory for raw OpenML dumps (checksummed) and `data/processed/` for simulation results (CSV/Parquet). No external database.  
**Testing**: `pytest` with `pytest-cov`. Tests verify data generation, selection logic, and statistical aggregation.  
**Target Platform**: GitHub Actions free-tier runner (Linux, multiple vCPUs, ~7 GB RAM, no GPU).  
**Project Type**: Computational research simulation / CLI tool.  
**Performance Goals**: Complete 24,000 simulations (datasets × 4 SNR × Sparsity × 200 sims) within 6 hours; peak RAM ≤ 7 GB.  
**Constraints**: No GPU usage; no heavy model training; strict adherence to simulation count and parameter grid; CPU-only execution; early stopping for stepwise selection; predictor count capped at a reasonable limit for stepwise methods.  
**Scale/Scope**: ~24,000 simulation runs; Multiple source datasets; selection methods × 4 SNR × 3 Sparsity × Alpha thresholds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase, except where fixed for feasibility (200 sims).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All random seeds pinned in `code/config.py`. OpenML datasets fetched by specific IDs with fallback logic. `requirements.txt` pins versions. T039 enforces 6-hour runtime limit. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` limited to verified dataset URLs. **Known Limitation**: Post-selection p-values are biased; study compares methods under shared bias, not absolute validity. |
| **III. Data Hygiene** | PASS | Raw OpenML data stored in `data/raw/` with SHA-256 checksums recorded in `state/`. Derived simulation results written to `data/processed/` as new files. T006 enforces 7 GB RAM limit. |
| **IV. Single Source of Truth** | PASS | All power metrics and plots generated strictly from `data/processed/` files. No manual entry in paper. |
| **V. Versioning Discipline** | PASS | Artifact hashes updated in `state/` upon any data/code change. `updated_at` timestamps managed by state agent. |
| **VI. Simulation Fidelity** | PASS | `code/simulation.py` explicitly logs: (a) exact count (200), (b) seed, (c) covariance source (dataset ID and name), (d) SNR/Sparsity params for every run. Per-simulation IDs included for aggregation. **Known Limitation**: Post-selection inference bias acknowledged. T015 verifies `dataset_name` logging. |
| **VII. Selection Method Transparency** | PASS | `code/metrics.py` records selected variable indices and decision thresholds (alpha) for every simulation run in the results dataframe, conforming to `simulation_result.schema.yaml`. T026 ensures schema compliance. |

**Gates Determined**: All principles are satisfied by the proposed architecture. No violations found.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-impact-of-variable-select/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-504-evaluating-the-impact-of-variable-select/
├── code/
│   ├── __init__.py
│   ├── config.py              # Seeds, paths, constants (SNR, Sparsity, Alpha)
│   ├── downloader.py          # OpenML fetch logic with retry/backoff
│   ├── simulation.py          # Synthetic Y generation using real X (bootstrapped)
│   ├── selection.py           # Forward, Backward, LASSO implementations
│   ├── metrics.py             # Power calculation, VIF, p-value refitting
│   ├── analysis.py            # Kruskal-Wallis, Dunn's post-hoc, plotting
│   ├── main.py                # Orchestration script with watchdog timer
│   └── verify.py              # Memory and runtime verification scripts
├── data/
│   ├── raw/                   # OpenML dumps (checksummed)
│   └── processed/             # Simulation results (CSV/Parquet)
├── tests/
│   ├── unit/                  # Logic tests (selection, metrics)
│   ├── integration/           # End-to-end simulation flow
│   └── contract/              # Schema validation tests
├── docs/
│   └── paper/                 # Draft paper text (generated from data)
├── requirements.txt
└── pyproject.toml             # Linting/formatting config (black, flake8)
```

**Structure Decision**: Single-project structure selected to minimize overhead. All logic resides in `code/` with clear separation of concerns (download, simulate, select, analyze). This aligns with the computational nature of the project and ensures easy reproducibility on CI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

*Note: No violations identified. The plan strictly adheres to the spec's constraints and the constitution's rigor.*

## Implementation Tasks (Summary)

- **T001**: Download and validate multiple datasets from a specified range of identifiers. with fallback logic for dimensionality.
- **T002**: Configure linting (flake8/black) via `pyproject.toml` with explicit `[tool.black]` and `[tool.flake8]` sections.
- **T003**: Implement memory-efficient chunking with a scalable batch size (variable sims/batch) and `tracemalloc` monitoring.
- **T004**: Implement pilot profiling (T024) to verify 200 sims are sufficient for CI width < 0.1 and runtime < 5.5 hours. **Gate**: Abort if pilot fails.
- **T005**: Implement runtime watchdog (T039) to fail if > 5.5 hours.
- **T006**: Implement memory limit verification (T040) to fail if > 6.5 GB.
- **T007**: Implement Forward Stepwise with **AIC** criterion and early stopping.
- **T008**: Implement LASSO with fixed seed for CV.
- **T009**: Implement OLS refitting for p-values (FR-009).
- **T010**: Implement diagnostics recording (VIF, condition number) to `data/processed/diagnostics.csv` (T022).
- **T011**: Implement sensitivity analysis plots for Alpha across a range of small values (T023).
- **T012**: Implement integration test to verify dataset download count and fallback logic.
- **T013**: Implement Kruskal-Wallis on individual simulation-level power estimates (n=24,000).
- **T014**: Implement Dunn's post-hoc with Holm correction.
- **T015**: Implement schema validation against `simulation_result.schema.yaml` (T026).
- **T016**: Log `dataset_name` and `dataset_id` for every simulation (T026).
- **T017**: Implement aggregation task (T036) to compute simulation-level mean power per condition for statistical tests.
- **T018**: Implement logic to handle zero true coefficients as true negatives (T030).
- **T019**: Implement contract schema for `diagnostics.schema.yaml`.

## Research & Methodology Alignment

- **FR-001**: Addressed by T001 (download 10 datasets).
- **FR-002**: Addressed by T004 (pilot run to verify sufficiency).
- **FR-003**: Addressed by T007, T008, T009 (selection methods).
- **FR-004**: Addressed by T009 (OLS refitting for p-values).
- **FR-005**: Addressed by T013, T014 (Kruskal-Wallis on simulation-level data).
- **FR-006**: Addressed by T011 (sensitivity analysis).
- **FR-007**: Addressed by T010 (diagnostics recording).
- **FR-008**: Addressed by T005, T039 (runtime watchdog).
- **FR-009**: Addressed by T009 (OLS refitting).
- **SC-001**: Addressed by T009 (power calculation against ground truth).
- **SC-002**: Addressed by T014 (Dunn's post-hoc).
- **SC-003**: Addressed by T005, T039 (runtime limit).
- **SC-004**: Addressed by T006 (memory limit).

## Computational Feasibility

- **Hardware**: GitHub Actions free-tier (2 vCPU, ~7 GB RAM, no GPU).
- **Strategy**:
  - **Chunking**: Process simulations in batches of to manage memory.
  - **Optimization**: Early stopping for stepwise; cap predictors at a reasonable limit for stepwise methods; fixed seed for LASSO CV.
  - **Pilot Run**: T004 validates that 200 sims provide sufficient CI width (< 0.1) and runtime < 5.5 hours before full run.
  - **Timeout**: Watchdog timer (T005) fails job if > 5.5 hours.
  - **Memory**: `tracemalloc` (T006) fails job if > 6.5 GB.
 - **Calculation**: A large-scale set of simulations, each optimized to run in [deferred], is projected to require [deferred] of total compute time.. Pilot run will confirm actual timing; if > 5.5 hours, job aborts.

## Decision Rationale

- **Why OpenML?** Provides diverse, real-world covariance structures.
- **Why Bootstrapping?** Preserves empirical distribution of X, addressing non-normality.
- **Why 200 Sims?** Balances statistical stability (CI width) with 6-hour runtime constraint on 2 vCPU.
- **Why AIC?** Fixed criterion for Forward Stepwise to ensure construct validity.
- **Why Individual Unit of Analysis?** Preserves variance structure for Kruskal-Wallis, meeting FR-005.
- **Why OLS Refitting?** Required by FR-009 to calculate p-values for Inference Power.
- **Why Pilot Run?** Ensures feasibility before committing to full runtime.

## Limitations

- **Dataset Size**: Limited to datasets with ≤50,000 rows to fit in RAM.
- **SNR Range**: Fixed to low-moderate levels.
- **Selection Methods**: Only three methods tested.
- **Post-Selection Inference**: Standard OLS p-values are biased; study compares relative performance under this bias, not absolute validity.
- **Collinearity**: Perfect multicollinearity (Condition Number > 10^10) causes dataset skip.
