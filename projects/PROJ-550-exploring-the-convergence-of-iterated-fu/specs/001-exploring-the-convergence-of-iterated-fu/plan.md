# Implementation Plan: Exploring the Convergence of Iterated Function Systems with Non-Contractive Maps

**Branch**: `001-gene-regulation` | **Date**: 2026-06-28 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a computational framework to generate synthetic Iterated Function Systems (IFS) with controlled Lipschitz constants ranging from contractive (<1.0) to non-contractive (≥1.0) regimes. The core objective is to empirically map the transition from stable invariant measures to divergence or chaotic filling using the Chaos Game algorithm. The implementation validates numerical Lipschitz constants, approximates invariant measures via Monte Carlo simulation with multi-stage convergence checks, computes topological descriptors (Minkowski-Bouligand dimension and Transient Dimension), and performs sensitivity analysis on the Lipschitz threshold using logistic regression. The target variable for regression is the *existence of an invariant measure*, validated against theoretical benchmarks, avoiding circular definitions.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `numpy`, `scipy`, `scikit-learn`, `pandas`, `pytest`, `matplotlib`
**Storage**: Local filesystem (`data/` for artifacts, `code/` for scripts)
**Testing**: `pytest` with contract validation against YAML schemas
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7GB RAM)
**Project Type**: Computational Research Library/CLI
**Performance Goals**: Full analysis of 500 IFS instances within 6 hours CPU time; memory usage < 6GB peak.
**Constraints**: No GPU; all operations must be vectorized or batch-processed to fit in RAM; strict adherence to 6-hour runtime limit.
**Scale/Scope**: synthetic IFS instances; benchmark IFS instances; ⁶ Chaos Game iterations (extended to a significantly larger scale for edge cases); A high-resolution grid for non-contractive Lipschitz estimation

The research question concerns the estimation of non-contractive Lipschitz constants. The method employs a high-resolution grid approach. References include standard works on Lipschitz estimation..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: The plan mandates pinned random seeds in `code/` via a `--seed` argument in all entry points and a central `config.py`. The specific 10⁶ iteration count (default) and 5000-point grid (for non-contractive) are defined as constants in `config.py` to ensure identical outputs on fresh runs.
2.  **II. Verified Accuracy**: Citations for benchmark IFS (Sierpinski, Barnsley Fern, da Cunha et al.) will be validated against primary literature before inclusion in `research.md`. The plan requires a "Benchmark Validation" phase before processing synthetic data.
3.  **III. Data Hygiene**: The implementation will generate a checksum manifest (`data/checksums.json`) for all raw and derived artifacts after *every* derivation step. No in-place modifications; all derivations write to new files.
4.  **IV. Single Source of Truth**: The logistic regression model results and topological dimensions will be stored in structured CSV/Parquet files in `data/`. The paper will reference these files, not hand-calculated numbers.
5.  **V. Versioning Discipline**: The `state/` file will be updated with artifact hashes upon completion of each phase.
6.  **VI. Numerical Precision**: The plan explicitly documents a dense grid for gradient estimation on non-contractive maps (A point for contractive), A high number of iterations for Chaos Game (extended further for edge cases), and scale levels for box-counting. Runtime constraints are enforced by processing instances in batches.
7.  **VII. Benchmark Validation**: The pipeline is ordered to run benchmarks first. The logistic regression model will only be trained on synthetic data after benchmark accuracy is confirmed. Specifically, the trained model will be applied to benchmark instances, and its accuracy against known theoretical outcomes will be reported before generalizing to synthetic data.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-550-exploring-the-convergence-of-iterated-fu/
├── code/
│   ├── __init__.py
│   ├── config.py                # Paths, seeds, hyperparameters (grid size, iterations)
│   ├── generators.py            # Synthetic IFS generation (FR-001, FR-002)
│   ├── chaos_game.py            # Monte Carlo simulation (FR-003, FR-004)
│   ├── topology.py              # Box-counting dimension (FR-005)
│   ├── analysis.py              # Sensitivity analysis & Logistic Regression (FR-006, FR-007)
│   └── benchmarks.py            # Benchmark validation (FR-008)
├── data/
│   ├── raw/                     # Downloaded/generated raw data
│   ├── derived/                 # Processed results (histograms, metrics)
│   └── checksums.json           # Integrity manifest (updated after each step)
├── tests/
│   ├── unit/                    # Unit tests for generators and metrics
│   └── contract/                # Contract validation tests
└── requirements.txt             # Pinned dependencies
```

**Structure Decision**: A modular monolithic structure within `code/` is selected to minimize overhead and simplify dependency management on the free-tier runner. This aligns with the computational research nature of the project, where data flows sequentially from generation to analysis.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is contained within a single computational pipeline. | A microservices or multi-repo approach would add unnecessary overhead for a 6-hour batch job. |

## Pipeline Execution Order

1.  **Generation**: `generators.py` creates `raw/ifs_instances.parquet`.
2.  **Benchmark Validation**: `benchmarks.py` runs on hardcoded benchmarks. Results stored in `derived/benchmark_results.parquet`.
3.  **Simulation**: `chaos_game.py` reads instances, runs Chaos Game (with multi-stage checks), writes `derived/chaos_results.parquet`.
4.  **Topology**: `topology.py` computes dimensions (including Transient Dimension), writes `derived/topology_results.parquet`.
5.  **Analysis**: `analysis.py` fits logistic regression (validated on benchmarks first), writes `derived/analysis_summary.csv`.
6.  **Checksum**: A final step generates `data/checksums.json` covering all derived artifacts.