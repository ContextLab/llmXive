# Implementation Plan: Impact of Cache Line Padding on False Sharing in Concurrent Counters

**Branch**: `001-cache-line-padding-false-sharing` | **Date**: 2026-06-08 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-cache-line-padding-false-sharing/spec.md`

## Summary

This project implements a high-performance C++ benchmark to quantify the causal impact of cache-line padding on false sharing in concurrent counters. The system compiles two counter variants (packed vs. 64-byte aligned), executes them across a range of thread counts with a substantial number of atomic increments per thread, and records wall-clock time. A Python analysis pipeline performs statistical testing (Two-Way ANOVA, post-hoc t-tests with FDR) and generates visualizations. The entire workflow is designed to run on GitHub Actions free-tier runners (CPU-only, ~7GB RAM) within 6 hours, with explicit hardware controls to mitigate noise.

## Technical Context

**Language/Version**: C++17 (for `std::atomic`, `alignas`), Python 3.11 (analysis)  
**Primary Dependencies**: `g++` (system), `pandas`, `scipy`, `matplotlib`, `pyyaml`, `pydantic`  
**Storage**: Local CSV files (`data/raw/`), no external database  
**Testing**: C++ unit test (single-threaded validation), `verify_layout.cpp` (memory layout check), Python `pytest` (schema validation)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Computational Benchmark / Performance Analysis  
**Performance Goals**: Complete 4 thread counts × 2 configs × 5 runs ≤ 6 hours total runtime  
**Constraints**: No GPU; CPU-only compilation and execution; memory usage < 7GB; strict adherence to spec-defined iteration counts  
**Scale/Scope**: A series of benchmark runs; A moderate amount of C++ code (including verification); A moderate amount of Python analysis code.

> Domain-specific empirical specifics are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All C++ code, Python scripts, and `requirements.txt` are version-controlled. **No random seeds are required; the experiment is deterministic** (fixed atomic increments, no stochastic sampling). GitHub Actions workflow ensures identical environment. |
| **II. Verified Accuracy** | PASS | Citations (e.g., Benjamini & Hochberg) will be verified by the Reference-Validator Agent against primary sources before inclusion in `research.md` or `paper.md`. |
| **III. Data Hygiene** | PASS | Raw CSV outputs stored in `data/raw/` with checksums recorded in `state/`. No in-place modification; analysis scripts read raw data and write derived `data/processed/`. |
| **IV. Single Source of Truth** | PASS | **`data/processed/statistical_comparison.csv` is explicitly designated as the Single Source of Truth (SSoT) for all statistical results.** All figures and statistics in the final report must trace directly to this file. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | **Content hashes are stored in `state/artifacts/checksums.json`.** The `run_analysis.py` script automatically updates the `updated_at` timestamp in the project state file upon successful artifact generation. |
| **VI. Empirical Benchmarking Rigor** | PASS | Plan mandates ≥5 runs per config (with escalation to 10 if variance is high). Two-Way ANOVA and t-tests (α=0.05) with FDR correction. Confidence interval calculated via t-distribution. |
| **VII. Hardware Configuration Transparency** | PASS | A `hardware_spec.yaml` will be generated. **Additionally, the benchmark harness will set the CPU governor to 'performance' and use `taskset` to pin threads to specific cores** to mitigate noisy neighbor effects and frequency scaling variance. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cache-line-padding-false-sharing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/
├── code/
│   ├── benchmark/
│   │   ├── main.cpp           # C++ benchmark harness
│   │   ├── verify_layout.cpp  # Memory layout verification utility
│   │   ├── counter_packed.hpp # Packed struct definition
│   │   └── counter_padded.hpp # Padded struct definition
│   ├── analysis/
│   │   ├── requirements.txt   # Python dependencies (includes pydantic)
│   │   ├── run_analysis.py    # Statistical analysis, plotting, and schema validation
│   │   └── hardware_detect.py # Hardware spec detection
│   └── scripts/
│       ├── build.sh           # Compilation script (includes verify_layout)
│       └── run_benchmarks.sh  # Experiment orchestration (includes hardware control)
├── data/
│   ├── raw/                   # Raw CSV outputs from benchmarks
│   └── processed/             # Aggregated results & plots
├── state/
│   └── artifacts/             # Checksums and hashes (checksums.json)
└── .github/
    └── workflows/
        └── benchmark.yml      # CI/CD pipeline
```

**Structure Decision**: Single project structure with distinct `benchmark` (C++) and `analysis` (Python) directories to separate performance-critical code from statistical analysis, ensuring modularity and clear separation of concerns. **The `verify_layout.cpp` utility is critical for scientific validity to confirm the memory layout assumptions.**

**Validation Strategy**: The `run_analysis.py` script will use **`pydantic`** to validate all generated CSV outputs against the schemas in `contracts/` before proceeding to aggregation or plotting. This ensures data hygiene and SSoT compliance.

## Complexity Tracking

No violations found. The single-project structure with clear separation of C++ and Python components, plus the explicit memory layout verification step, is sufficient for the scope.