# Implementation Plan: Assessing the Validity of p-Values in High-Dimensional Data

**Branch**: `[001-assess-p-value-validity]` | **Date**: 2026-06-28 | **Spec**: `specs/001-assess-p-value-validity/spec.md`

## Summary

This feature implements a computational study to empirically assess how standard p-values (from t-tests and F-tests) deviate from their theoretical uniform distribution when applied to high-dimensional data where independence and normality assumptions are violated. The approach relies on generating synthetic datasets with controlled correlation structures ($\rho \in \{0, \dots, 0.9\}$), sample sizes ($n \in \{50, \dots, 500\}$), and feature counts ($p \in \{500, \dots, 5000\}$), applying standard hypothesis tests under a known null, and comparing the resulting p-value distributions against a permutation-based "Gold Standard" using Kolmogorov-Smirnov (KS) statistics and QQ-plots. All computations are strictly CPU-bound to ensure compatibility with free-tier CI.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`  
**Storage**: Local filesystem (`data/` for synthetic artifacts, `code/` for scripts). No external database.  
**Testing**: `pytest` (unit tests for data generation logic, integration tests for simulation pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, ~7 GB RAM).  
**Project Type**: Computational research / Simulation library.  
**Performance Goals**: Complete full simulation sweep (1000 iterations per setting) within 6 hours on CPU. Memory usage < 6 GB.  
**Constraints**: No GPU/CUDA; no large-LLM inference; strict adherence to `scipy`/`numpy` CPU-only methods; regularization required for singular covariance matrices.  
**Scale/Scope**: A large number of hypothesis tests will be conducted across all simulation settings.; output includes a representative set of KS statistics and corresponding plots.

> **Design Parameters**: The simulation uses **1000 iterations** as a fixed design parameter (required by SC-005 for power) and **A sufficient number of permutations per iteration** (with a fallback to a reduced sample size if runtime exceeds a practical threshold) to ensure statistical robustness. Empirical results (measured KS deviations) are deferred to the research phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned `random_seed` in `data/` metadata; `requirements.txt` pins versions; CI runs from scratch. |
| **II. Verified Accuracy** | **PASS** | No external citations for datasets used in the core simulation (synthetic generation). If public data is used for validation, URLs will be restricted to the "Verified datasets" block. |
| **III. Data Hygiene** | **PASS** | Synthetic data will be checksummed upon generation; no in-place modification; raw seeds stored. |
| **IV. Single Source of Truth** | **PASS** | All KS statistics and plots generated programmatically; no hand-typed values in paper. |
| **V. Versioning Discipline** | **PASS** | Artifacts (synthetic datasets, results) will carry content hashes; state file updated on change. |
| **VI. Simulation Fidelity** | **PASS** | Plan explicitly enforces $\rho \in \{0, \dots, 0.9\}$, $n \in \{50, \dots, 500\}$, $p \in \{500, \dots, 5000\}$ as per spec and constitution. |
| **VII. Statistical Validity Reporting** | **PASS** | Plan mandates reporting KS statistic + bootstrap CI (computed by `analyze_pvalues.py`); QQ-plots generated automatically. The `analyze_pvalues.py` script is explicitly required to compute and store bootstrap confidence intervals for every KS statistic reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-p-value-validity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-054-assessing-the-validity-of-p-values-in-hi/
├── code/
│   ├── requirements.txt
│   ├── generate_data.py       # Synthetic data generation (FR-001)
│   ├── run_tests.py           # Hypothesis testing (FR-002, FR-003)
│   ├── analyze_pvalues.py     # KS stats, QQ-plots, sensitivity, bootstrap CIs (FR-004, FR-005, FR-007)
│   ├── utils/
│   │   ├── regularization.py  # Covariance regularization (FR-009)
│   │   └── simulation.py      # Simulation orchestration
│   └── main.py                # Entry point for full sweep
├── data/
│   ├── raw/                   # Downloaded public datasets (if any)
│   ├── synthetic/             # Generated datasets with checksums
│   └── results/               # KS statistics, plots, metadata
├── tests/
│   ├── unit/
│   │   ├── test_data_gen.py
│   │   └── test_stats.py
│   └── integration/
│       └── test_full_sweep.py
└── docs/                      # Paper drafts, methodology notes
```

**Structure Decision**: Single project structure under `code/` with modular scripts for generation, testing, and analysis. This minimizes overhead and aligns with the computational research nature of the feature.

**Contract Consistency**: The `contracts/*.yaml` files are the source of truth for data validation logic in `generate_data.py`, `run_tests.py`, and `analyze_pvalues.py`. Specifically, `analyze_pvalues.py` adheres to the `SimulationResult` schema (defined in `contracts/` or `data-model.md`) to ensure bootstrap CIs are computed and stored in the required format.

## Complexity Tracking

No violations identified. The complexity is inherent to the simulation scope (high-dimensional matrix operations) but is managed by:
1.  Strict parameter bounds ($p \le 5000$).
2.  CPU-optimized libraries (`numpy`/`scipy`).
3.  Regularization for numerical stability.