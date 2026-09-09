# Implementation Plan: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

**Branch**: `001-evaluating-robustness-tests` | **Date**: 2026-06-25 | **Spec**: `specs/001-evaluating-the-robustness-of-common-stat/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-robustness-of-common-stat/spec.md`

## Summary

This project implements a Monte Carlo simulation framework to quantify how non-independence (temporal, hierarchical) in public datasets inflates Type I error rates and alters statistical power for standard tests (t-test, ANOVA, Chi-squared). The system downloads verified UCI datasets, injects controlled dependency structures (AR(1) for temporal, Cluster-Effect Injection for hierarchical) into the error terms of real data, and executes 10,000+ replications per configuration on a CPU-only runner. The output includes error rate curves, power loss quantification, and comparative visualizations against nominal alpha levels.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local file system (`data/`, `results/`) with checksummed CSV/Parquet files.  
**Testing**: `pytest` with `conftest` for seed pinning and edge-case coverage.  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM, 14GB Disk).  
**Project Type**: Computational Research / Simulation Pipeline.  
**Performance Goals**: Complete 10,000 replications per config within 6 hours; memory usage < 6GB (leaving 1GB buffer).  
**Constraints**: No GPU; no external API calls during simulation; strict seed reproducibility; no synthetic data generation for the *base* dataset (must use real UCI data with injected dependency).  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Implementation Strategy | Status |
| :--- | :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned; canonical data fetch. | `code/utils/seeding.py` sets global `np.random.seed` and `random.seed`. Data fetched via `datasets.load_dataset` with specific revision hashes. | ✅ |
| **II. Verified Accuracy** | Citations verified against primary source. | All dataset references in `research.md` use ONLY the verified URLs from the `# Verified datasets` block. No external URLs invented. | ✅ |
| **III. Data Hygiene** | Checksummed data; no in-place modification. | `data/raw/` files are checksummed in `state.yaml`. Derived files (injected dependency) written to `data/processed/` with new names. | ✅ |
| **IV. Single Source of Truth** | Figures trace to `data/` and `code/`. | `results/` contains raw CSVs of simulation outcomes. `code/analysis/plotting.py` reads these exclusively. No manual numbers in reports. | ✅ |
| **V. Versioning Discipline** | Content hashes for artifacts. | `state.yaml` tracks `artifact_hashes` for `data/`, `code/`, and `results/`. | ✅ |
| **VI. Dependency Modeling Transparency** | Injection parameters (r, block size) manifest. | `data/dependency_manifest.yaml` records exact `r` values (0, 0.1, 0.2, 0.3, 0.5) and method (AR1, Cluster-Effect) for every run. | ✅ |
| **VII. Empirical Error Rate Reporting** | 95% CIs; ≥1,000 replications (target 10k). | `code/analysis/metrics.py` calculates Clopper-Pearson intervals. `config.yaml` enforces `n_replications=10000`. **Logistic regression models** are output to `results/logistic_models.pkl` as required. | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-robustness-of-common-stat/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── simulation_output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-483-evaluating-the-robustness-of-common-stat/
├── data/
│   ├── raw/                 # Downloaded UCI datasets (checksummed)
│   ├── processed/           # Dependency-injected datasets
│   └── dependency_manifest.yaml
├── code/
│   ├── __init__.py
│   ├── main.py              # Entry point for CLI
│   ├── data_loader.py       # FR-001: Download and parse UCI/OpenML
│   ├── dependency_injector.py # FR-003: AR(1), Cluster-Effect Injection (Addresses FR-003)
│   ├── null_constructor.py  # FR-002: Permutation logic on injected data (Addresses FR-002)
│   ├── simulator.py         # FR-004: Monte Carlo loop (10k reps)
│   ├── analysis/
│   │   ├── metrics.py       # FR-005: Error rates, Power, CIs
│   │   ├── logistic_models.py # VII: Logistic regression for trend analysis
│   │   └── plotting.py      # FR-006: Comparative visualizations
│   ├── utils/
│   │   ├── seeding.py       # Constitution I: Seed management
│   │   └── logging.py       # Constitution VII: Perf logging
│   └── requirements.txt
├── tests/
│   ├── unit/
│   │   ├── test_null_construction.py # T033: Edge cases (small N, no effect)
│   │   └── test_dependency_injection.py
│   └── integration/
│       └── test_full_pipeline.py
├── results/
│   ├── perf_log.json        # T032b: Execution metrics
│   ├── type1_error_rates.csv
│   ├── power_analysis.csv
│   └── logistic_models.pkl
└── state.yaml               # Versioning & Checksums
```

**Structure Decision**: Single project structure (Option 1) selected. The project is a research pipeline, not a web service or mobile app. Separation of `data/`, `code/`, and `results/` aligns with Constitution III (Data Hygiene) and IV (Single Source of Truth).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dependency Injection Before Permutation** | FR-002 explicitly requires injecting dependency *before* constructing the null via permutation to preserve the structure while removing the effect. | Doing permutation first would destroy the injected dependency structure, violating the core research question of "robustness to non-independence". |
| **Cluster-Effect Injection (vs Block Bootstrap)** | Block Bootstrap resamples data, altering N and distribution, violating FR-002. Cluster-Effect Injection adds correlated noise to residuals, preserving N and distribution while inducing dependency. | Block Bootstrap creates a synthetic dataset, not a modified real one. |
| **Vectorized Simulation Loop** | FR-008 requires 10k reps in 6 hours on 2 cores. Python loops are too slow. | Pure Python loops would exceed the time budget. Vectorized `numpy` operations are required to meet the 6-hour constraint. |
| **Clopper-Pearson CIs** | SC-003 requires high precision ($\pm [deferred]$) and rigorous error reporting. | Standard Wald intervals are inaccurate for proportions near 0 or 1 (rare false positives) or small sample sizes. Clopper-Pearson is the conservative standard. |
| **Sensitivity Sweep Task** | FR-007 requires sweeping r ∈ {0, 0.1, 0.2, 0.3, 0.5}. | A single configuration would miss the trend analysis required by the spec. |
| **Precision Verification Task** | SC-003 requires checking the CI width against the 0.5% target. | Assuming 10k reps is sufficient without verification risks failing the precision target. |

## Tasks

### Phase 0: Research & Design
- [ ] T001: Review verified datasets and select suitable ones (UCI Wine, HAR).
- [ ] T002: Define dependency injection methods (AR1, Cluster-Effect) and null construction logic.
- [ ] T003: Design the sensitivity sweep loop for r ∈ {0, 0.1, 0.2, 0.3, 0.5}.

### Phase 1: Implementation
- [ ] T010: Implement `data_loader.py` to download and checksum datasets.
- [ ] T011: Implement `dependency_injector.py` with AR1 and Cluster-Effect Injection.
- [ ] T012: Implement `null_constructor.py` to permute labels on injected data (Addresses FR-002).
- [ ] T013: Implement `simulator.py` for 10k replications with vectorized loops.
- [ ] T014: Implement `metrics.py` for Clopper-Pearson CIs and precision verification.
- [ ] T015: Implement `logistic_models.py` for trend analysis (Constitution VII).
- [ ] T016: Implement `plotting.py` for comparative visualizations.

### Phase 2: Testing & Validation
- [ ] T030: Update `docs/` and `README.md` with new methodology.
- [ ] T032b: Generate `results/perf_log.json` and verify execution time < 6h.
- [ ] T033: Add unit tests for `null_constructor.py` and edge cases (small N).
- [ ] T034: Verify reproducibility by running the pipeline twice and comparing results.
