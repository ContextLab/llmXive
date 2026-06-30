# Implementation Plan: Evaluating the Sensitivity of Common Statistical Tests to Dataset Size

**Branch**: `001-evaluating-sensitivity-statistical-tests` | **Date**: 2026-06-24 | **Spec**: `specs/001-evaluating-the-sensitivity-of-common-sta/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-sensitivity-of-common-sta/spec.md`

## Summary

This project implements a simulation engine to empirically evaluate the sensitivity of parametric statistical tests (t-test, ANOVA, chi-squared) to sample size reductions. The system generates synthetic data with known ground truth (null and alternative hypotheses) across sample sizes $n=5$ to $n=500$, performing [deferred]+ iterations per condition to calculate Type I and Type II error rates. It identifies reliability thresholds where error rates deviate from nominal levels or power drops below 0.80, visualizes these trends with confidence intervals, and validates findings against public small-sample datasets. The implementation adheres to strict reproducibility and compute feasibility constraints (CPU-only, bounded runtime).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `statsmodels`, `scikit-learn`, `requests`, `ucimlrepo`  
**Storage**: Local file system (`data/` for synthetic results, `data/raw/` for public datasets)  
**Testing**: `pytest` with `pytest-randomly` (seed pinning)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Research / Simulation Engine  
**Performance Goals**: Complete [deferred] iterations for all conditions (n=5..500, 3 tests, 3 effect sizes) within 6 hours on 2 CPU cores.
**Constraints**: No GPU usage; memory < 7 GB; disk < 14 GB; all random seeds pinned; no external API calls during core simulation (only dataset download once).  
**Scale/Scope**: A large-scale set of simulation iterations total (multiple sample sizes * tests * 3 effects * 2 hypotheses * 10k iterations, optimized via vectorization and batch processing).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan enforces pinned seeds in `data/simulation_metadata.json` and deterministic synthetic generation. |
| **II. Verified Accuracy** | PASS | Citations for public datasets (UCI HAR, Shopper) use verified URLs from the context. No fabricated URLs. |
| **III. Data Hygiene** | PASS | Plan mandates checksumming of raw public datasets and immutable synthetic data generation. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/` CSVs and `code/` scripts. No hand-typed numbers in paper. |
| **V. Versioning Discipline** | PASS | Artifact hashes will be recorded in project state; content hashes for code/data. |
| **VI. Simulation Fidelity** | PASS | Plan explicitly defines normal/multinomial distributions, effect sizes (d=0.2, 0.5, 0.8), and n=5..500 grid. |
| **VII. Benchmark Validation** | PASS | Plan includes validation against UCI HAR and Shopper (verified sources) to check consistency of p-value distributions, acknowledging that real-world ground truth is unknown. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-sensitivity-of-common-sta/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── simulation/
│   ├── __init__.py
│   ├── data_generator.py      # Synthetic data generation (FR-001)
│   ├── test_runner.py         # Statistical tests & error calculation (FR-002)
│   └── chi_squared_utils.py   # Fallback logic (FR-007)
├── analysis/
│   ├── __init__.py
│   ├── threshold_finder.py    # Threshold identification (FR-004)
│   └── validator.py           # Real-world dataset validation (FR-006)
├── visualization/
│   ├── __init__.py
│   └── plotter.py             # Error rate curves & CI (FR-005)
├── main.py                    # Orchestration script
├── requirements.txt           # Pinned dependencies
└── run_simulation.sh          # Entry point for CI

data/
├── raw/                       # Downloaded public datasets (checksummed)
├── simulation/                # Generated CSVs (p-values, error rates)
└── simulation_metadata.json   # Seeds, config, timestamps

tests/
├── unit/
│   ├── test_data_generator.py
│   └── test_chi_squared_fallback.py
├── integration/
│   └── test_full_pipeline.py
└── contract/
    └── test_schema_validation.py
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`simulation`, `analysis`, `visualization`) to ensure clear separation of concerns and ease of testing. This structure supports the computational nature of the project and aligns with the "Single Source of Truth" principle.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **N/A** | Constitution Check passed. No violations detected. | N/A |