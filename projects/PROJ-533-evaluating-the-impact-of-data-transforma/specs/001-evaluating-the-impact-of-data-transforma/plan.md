# Implementation Plan: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Branch**: `001-data-transformation-sensitivity` | **Date**: 2024-01-15 | **Spec**: `specs/001-data-transformation-sensitivity/spec.md`
**Input**: Feature specification from `/specs/001-data-transformation-sensitivity/spec.md`

## Summary

This project implements a statistical simulation pipeline to evaluate how three data transformation techniques (Box-Cox, Yeo-Johnson, rank-based inverse normal) affect the Type I error rate and statistical power of parametric tests (t-test, ANOVA) when applied to non-normal data. The system ingests real-world datasets from UCI/OpenML (filtered for non-normality via skewness/kurtosis and Shapiro-Wilk), applies transformations, performs null simulations via label shuffling to estimate Type I error (measuring raw rejection rates), and generates synthetic data with known effect sizes from non-normal distributions to estimate power. Results are aggregated using Generalized Linear Mixed Models (GLMM) with binomial link functions to account for the proportion nature of error rates, followed by post-hoc corrections.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `scipy`, `pandas`, `numpy`, `seaborn`, `matplotlib`, `requests`, `pyyaml`, `statsmodels`  
**Storage**: Local filesystem (`data/`, `results/`), CSV/JSON/Parquet formats  
**Testing**: `pytest` (unit tests for transformation logic, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, ~7 GB RAM)  
**Project Type**: Data analysis / Simulation pipeline  
**Performance Goals**: Complete full pipeline (50+ datasets + 1000 simulations) within 6 hours on CPU-only runner; memory usage < 6 GB peak  
**Constraints**: No GPU usage; no large model training; strict random seed pinning; checkpointing for resumption; all data checksummed  
**Scale/Scope**: Multiple real-world datasets; A sufficient number of iterations per dataset for Type I error; A large number of simulated datasets per effect size; transformations × 2 tests × 3 effect sizes  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Random seeds pinned (); all datasets fetched from canonical sources; `requirements.txt` pins versions; CI runs end-to-end |
| II. Verified Accuracy | PASS | Citations limited to verified URLs in `# Verified datasets` block; Reference-Validator Agent checks title overlap (≥0.7) before review points are awarded; no fabricated sources |
| III. Data Hygiene | PASS | SHA-256 checksums computed and stored (`data/checksums.csv`); raw data preserved; derivations written to new files |
| IV. Single Source of Truth | PASS | All figures/statistics trace to `data/` and `code/`; no hand-typed numbers in paper |
| V. Versioning Discipline | PASS | Artifact hashes tracked in state YAML; `updated_at` timestamps managed by Advancement-Evaluator; checkpoint files stored in `results/checkpoints/` |
| VI. Benchmark Transparency | PASS | All datasets from UCI/OpenML via explicit URLs recorded in `data/datasets.csv` |
| VII. Simulation Determinism | PASS | Random seed used for all shuffling/simulation.; seed value stored in `results/simulation_seeds.txt` |

## Project Structure

### Documentation (this feature)

```text
specs/001-data-transformation-sensitivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-533-evaluating-the-impact-of-data-transforma/
├── code/
│   ├── __init__.py
│   ├── download_datasets.py       # FR-001, FR-010
│   ├── filter_datasets.py         # FR-002
│   ├── apply_transformations.py   # FR-003
│   ├── simulate_null.py           # FR-004
│   ├── simulate_power.py          # FR-005, FR-006
│   ├── aggregate_results.py       # FR-007, FR-008, FR-009
│   ├── utils/
│   │   ├── transformations.py
│   │   ├── statistical_tests.py
│   │   └── checkpointing.py
│   └── main_pipeline.py           # Orchestrates all steps
├── data/
│   ├── raw/                       # Downloaded datasets
│   ├── processed/                 # Filtered & transformed data
│   ├── datasets.csv               # FR-001 metadata
│   └── checksums.csv              # FR-010 checksums
├── results/
│   ├── type1_error/               # Per-dataset Type I error estimates
│   ├── power/                     # Per-simulation power estimates
│   ├── aggregated/                # Summary tables & plots
│   ├── checkpoints/               # Checkpoint files for resumption (Constitution V)
│   └── simulation_seeds.txt       # FR-004, FR-006 seed log (Constitution VII)
├── tests/
│   ├── unit/
│   │   ├── test_transformations.py
│   │   └── test_statistical_tests.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure chosen to align with the statistical analysis workflow. All code resides in `code/` with clear separation between download, filtering, transformation, simulation, and aggregation modules. Data is organized into `raw/` and `processed/` to preserve integrity per Constitution Principle III. Checkpoints are explicitly stored in `results/checkpoints/` to satisfy Constitution Principle V.

## Complexity Tracking

No violations detected. The single-project structure is sufficient for the scope (50+ datasets, 3 transformations, 2 tests, 3 effect sizes). Checkpointing and modular design ensure maintainability without over-engineering.