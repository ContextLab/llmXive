# Implementation Plan: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

**Branch**: `001-evaluating-the-impact-of-variable-select` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-variable-select/spec.md`

## Summary

This project implements a simulation-based analysis to evaluate how three variable selection methods (Forward Stepwise, Backward Elimination, LASSO) affect **Selection Recovery Rate** (the proportion of true non-zero coefficients correctly identified) in linear regression. The system downloads a set of real-world regression datasets from OpenML., extracts their covariance structures, and simulates synthetic outcome vectors across varying Signal-to-Noise Ratios (SNR) and Sparsity levels. 

**Critical Methodological Update**: To address the "double-dipping" fallacy and pseudoreplication concerns, the primary metric is **Selection Recovery Rate** (ground-truth based), not post-selection p-values. Statistical comparisons will be performed on **dataset-level aggregates** (n=10) using Mixed-Effects Models or Friedman tests, rather than on individual simulations, to ensure valid inference.

For each simulation, the system applies selection methods, records selected variables and decision thresholds, and calculates the recovery rate. Finally, it performs rigorous statistical comparisons and generates recovery curves.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `statsmodels`, `openml`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `lme4` (via `statsmodels` mixedlm)  
**Storage**: Local files under `data/` (CSV/Parquet) and `results/` (JSON/CSV); no external database.  
**Testing**: `pytest` with unit tests for simulation logic and integration tests for pipeline execution.
- **FR-001 Coverage**: `test_downloader.py` validates 10 datasets with ≥100 rows.
- **FR-002 Coverage**: `test_simulators.py` validates 1,000 simulations per tuple.
- **FR-003/004 Coverage**: `test_selectors.py` validates selection methods and recovery calculation.
- **FR-005/006 Coverage**: `test_comparators.py` validates statistical tests and sensitivity analysis.
- **FR-007/008/009 Coverage**: `test_metrics.py` validates diagnostics, runtime checks, and OLS refitting logic.

**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, 7 GB RAM, no GPU).  
**Performance Goals**: Complete 120,000+ simulations within 6 hours on 2 vCPUs; peak RAM < 7 GB.  
**Constraints**: CPU-only execution; no GPU/CUDA; memory-efficient data handling (chunking if needed); strict reproducibility via pinned seeds.  
**Scale/Scope**: 10 datasets × [deferred] sims × 4 SNR × 3 Sparsity = 120,000 simulation runs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**: Plan mandates pinned random seeds in `code/` scripts. The `--seed` CLI argument is passed to the `simulators.py` module via the `run_simulation(seed)` function, which explicitly sets `np.random.seed(seed)` and `random_state=seed` in all sklearn estimators. All results trace to `data/` files.
2.  **Verified Accuracy**: Citations in `research.md` will be restricted to the verified OpenML datasets listed in the spec. No fabricated URLs.
3.  **Data Hygiene**: Raw OpenML data will be checksummed upon download. Simulated data will be derived with documented parameters (SNR, Sparsity, Seed) and stored as new files. No in-place modification.
4.  **Single Source of Truth**: All recovery metrics and plots will be generated directly from the `results/` CSVs. No hand-typed numbers in the final report.
5.  **Versioning Discipline**: All artifacts (code, data, results) will carry content hashes. The `state/` YAML will track updates.
6. **Simulation Fidelity**: The plan explicitly documents the **exact number of synthetic outcome vectors generated per tuple ([deferred])**. This count is recorded in the `SimulatedDataset` metadata and the final `PowerMetric` aggregation for every dataset/SNR/Sparsity combination.
7.  **Selection Method Transparency**: The implementation will record selected predictors and **decision thresholds** (p-value cutoffs for Forward/Backward, lambda for LASSO) for every run in the output artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-impact-of-variable-select/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-504-evaluating-the-impact-of-variable-select/
├── code/
│   ├── __init__.py
│   ├── main.py                  # Entry point for pipeline execution
│   ├── data/
│   │   ├── downloader.py        # OpenML dataset fetching & validation
│   │   └── simulators.py        # Synthetic outcome generation (seeded)
│   ├── analysis/
│   │   ├── selectors.py         # Forward, Backward, LASSO implementations
│   │   ├── metrics.py           # Recovery rate calculation & diagnostics
│   │   └── comparators.py       # Mixed-Effects / Friedman tests
│   └── viz/
│       └── plots.py             # Recovery curve generation
├── data/
│   ├── raw/                     # Downloaded OpenML datasets (checksummed)
│   └── simulated/               # Generated outcome vectors & metadata
├── results/
│   ├── simulation_results.csv   # Aggregated recovery metrics
│   └── plots/                   # Generated figures
├── tests/
│   ├── unit/
│   │   ├── test_simulators.py
│   │   └── test_selectors.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure focused on `code/` modules for data, analysis, and viz. This aligns with the computational research nature, keeping logic modular for testing and reproducibility.

## Complexity Tracking

*No violations detected. The scope is constrained to CPU-tractable methods and a fixed number of simulations to fit CI limits. Methodological rigor has been updated to address pseudoreplication and selection bias.*