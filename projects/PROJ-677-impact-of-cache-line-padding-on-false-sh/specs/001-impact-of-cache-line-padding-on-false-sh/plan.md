# Implementation Plan: Impact of Cache Line Padding on False Sharing in Concurrent Counters

**Branch**: `001-cache-line-padding-false-sharing` | **Date**: 2026-06-08 | **Spec**: `specs/001-cache-line-padding-false-sharing/spec.md`
**Input**: Feature specification from `/specs/001-cache-line-padding-false-sharing/spec.md`

## Summary

This project implements a C++ benchmark harness to measure the impact of cache-line padding on false sharing in concurrent counters. The technical approach involves compiling two counter variants (packed vs. padded) with `-O3 -march=native` flags, executing multi-threaded atomic increment workloads across varying thread counts, and performing statistical analysis (t-tests, Cohen's d, FDR correction) on the resulting throughput data. The study is observational, framing findings as associational between padding and throughput, but controls for OS scheduler noise via CPU pinning.

## Technical Context

**Language/Version**: C++17 (GCC 11+), Python 3.11  
**Primary Dependencies**: `std::atomic`, `std::thread`, `matplotlib`, `scipy`, `pandas`, `pydantic`, `statsmodels`  
**Storage**: Local CSV files (`data/raw/*.csv`), YAML hardware specs (`data/hardware_spec.yaml`)  
**Testing**: `pytest` for analysis scripts; manual compilation checks for C++  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 CPU, ~7 GB RAM)  
**Project Type**: Performance benchmarking / Systems research  
**Performance Goals**: Complete full benchmark suite (5+ runs × 4 threads × 2 configs) within 6 hours  
**Constraints**: Must run on CPU-only free tier; no GPU required; strict reproducibility (pinned seeds, checksums)  
**Scale/Scope**: + benchmark runs total; ~10⁷ iterations per run; output ~40 KB CSV data

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| **I. Reproducibility** | ✅ Compliant | Plan mandates pinned seeds, CI-based re-runs, and `requirements.txt`/`CMakeLists.txt` versioning. |
| **II. Verified Accuracy** | ✅ Compliant | Citations (Benjamini-Hochberg) will be verified by the **Reference-Validator Agent** against the primary source with a title-token overlap threshold ≥ 0.7 before inclusion. |
| **III. Data Hygiene** | ✅ Compliant | Raw CSVs will be checksummed; no in-place modifications; `hardware_spec.yaml` recorded. |
| **IV. Single Source of Truth** | ✅ Compliant | All figures/stats trace to `data/raw/*.csv`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | ✅ Compliant | Artifacts will carry content hashes; `state/` updated on changes. |
| **VI. Empirical Benchmarking Rigor** | ✅ Compliant | Plan explicitly requires ≥5 runs (or power-calculated n), t-tests, Cohen's d, and 95% CI. |
| **VII. Hardware Configuration Transparency** | ✅ Compliant | `hardware_detect.py` will generate `hardware_spec.yaml` with CPU model, cores, cache line size, and compiler flags. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cache-line-padding-false-sharing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/
├── code/
│   ├── benchmark/
│   │   ├── CMakeLists.txt
│   │   ├── main.cpp
│   │   ├── verify_layout.cpp
│   │   ├── counter_packed.hpp
│   │   ├── counter_padded.hpp
│   │   └── hardware_detect.py
│   ├── scripts/
│   │   ├── build.sh
│   │   ├── run_benchmarks.sh
│   │   └── validate_raw_data.py
│   └── analysis/
│       ├── requirements.txt
│       ├── contracts/
│       │   ├── benchmark_run.py
│       │   ├── aggregated_result.py
│       │   └── statistical_comparison.py
│       └── analysis.py
├── data/
│   ├── raw/
│   └── processed/
├── state/
│   └── projects/PROJ-677-impact-of-cache-line-padding-on-false-sh.yaml
└── .github/
    └── workflows/
        └── benchmark.yml
```

**Structure Decision**: Single-project structure with clear separation between C++ benchmark code (`code/benchmark/`), Python analysis (`code/analysis/`), and CI/CD (`.github/`). This aligns with the requirement for reproducible, isolated execution on GitHub Actions.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | No violations detected; all requirements are met with standard benchmarking patterns. |

## Phase Breakdown

### Phase 0: Research & Data Strategy
- **Goal**: Confirm dataset (synthetic workload) fit, statistical methodology, and power analysis.
- **FR-001 to FR-010**: Map to C++ implementation and Python analysis steps.
- **SC-001 to SC-005**: Define measurement targets and statistical thresholds.
- **Task T000**: **Power Analysis**. Use `statsmodels` to calculate required sample size (n) based on pilot variance estimates to achieve power ≥ 0.8 for detecting Cohen's d ≥ 0.5. If n > 5, update plan to run n iterations.
- **Output**: `research.md` detailing dataset strategy (synthetic), statistical plan, power analysis results, and hardware detection.

### Phase 1: Design & Contracts
- **Goal**: Define data schemas and project scaffolding.
- **FR-006**: Define CSV schema (`BenchmarkRun`).
- **FR-007, FR-008, FR-009**: Define statistical output schema (`AggregatedResult`, `StatisticalComparison`).
- **Task T006**: **Create Pydantic Schemas**. Implement `code/analysis/contracts/benchmark_run.py`, `aggregated_result.py`, `statistical_comparison.py`. **Verification**: Run `pytest` on sample data to ensure `pydantic` validation passes.
- **Output**: `data-model.md`, `contracts/*.schema.yaml`, `quickstart.md`.

### Phase 2: Implementation (Tasks)
- **Goal**: Execute C++ build, benchmark runs, and analysis.
- **T001**: **Directory Hierarchy**. Create `projects/PROJ-677-.../code/`, `data/`, `state/`, `.github/`. **Verification**: `ls` output confirms structure.
- **T002**: **C++ Build System**. Create `code/benchmark/CMakeLists.txt` with C++17 and `-O3 -march=native`. **Verification**: `cmake` succeeds.
- **T003**: **Linting/Formatting**. Create `.gitignore`, configure `clang-format` (C++), `black`/`flake8` (Python). **Verification**: `black --check` passes.
- **T004**: **Hardware Detection**. Create `hardware_detect.py`. **Verification**: Output `data/hardware_spec.yaml` contains keys: `cpu_model`, `core_count`, `cache_line_size`, `compiler_flags`, `timestamp` and validates against `contracts/hardware_spec.schema.yaml`.
- **T005**: **Layout Verification**. Create `verify_layout.cpp`. **Verification**: Binary outputs struct sizes (packed small, padded large).
- **T007**: **Counter Implementation**. Create `counter_packed.hpp` (`#pragma pack(1)`) and `counter_padded.hpp` (`alignas(64)`). **FR-002, FR-010 Addressed**.
- **T008**: **GitHub Actions Workflow**. Create `.github/workflows/benchmark.yml`. **Structure**: `on: [push]`, `jobs: benchmark`, `runs-on: ubuntu-latest`, `timeout-minutes: 360`. **Steps**: Checkout, Build, Run, Analyze. **Verification**: YAML parses valid; timeout logic handles >6h job termination.
- **T014**: **Benchmark Harness**. Create `main.cpp` with argument parsing (`--threads`, `--config`). **FR-003, FR-004 Addressed**.
- **T015**: **Build Script**. Create `code/scripts/build.sh` compiling `main.cpp`, `verify_layout.cpp` with `-O3 -march=native`. **FR-001 Addressed**.
- **T016**: **Single-Threaded Validation**. Modify `main.cpp` to run single-threaded sanity check. **Verification**: Runs without error.
- **T017**: **Compilation Logging**. Modify `build.sh` to redirect stdout/stderr to `build.log`. **Verification**: `build.log` contains warnings if any; exit code 1 on error.
- **T025**: **CPU Pinning & Governor**. Modify `run_benchmarks.sh` to: 1. Set governor: `cpupower frequency-set -g performance`. 2. Pin threads: `taskset -c 0-7 ./benchmark ...`. **Verification**: `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor` returns "performance". **Addressed: Methodology Concerns (noise control)**.
- **T026**: **Benchmark Execution**. Modify `run_benchmarks.sh` to repeat each config ≥5 times (or n from T000). **FR-005, FR-006 Addressed**. **Verification**: CSV has ≥5 rows per config.
- **T047**: **Data Validation**. Create `validate_raw_data.py` to check NaNs, missing values, schema. **Verification**: Script exits 0 on valid data.
- **T048**: **Statistical Analysis**. Create `analysis.py` to run t-tests, Cohen's d, FDR. **FR-007, FR-008, FR-009 Addressed**. **SC-005 Addressed**.

### Phase 3: Analysis & Reporting
- **Goal**: Statistical analysis and visualization.
- **FR-007, FR-008, FR-009**: T-tests, effect sizes, plots.
- **SC-002, SC-003**: Significance and effect size reporting.
- **Output**: `data/processed/`, figures, paper draft.

## Compute Feasibility
- **CPU-First**: C++ benchmarking and statistical analysis are lightweight and fully tractable on GitHub Actions free tier (2 CPU, 7 GB RAM).
- **No GPU Required**: No transformer or diffusion models; standard `std::atomic` and `scipy` suffice.
- **Time Budget**: 40+ runs × ~10⁷ iterations estimated at <1 hour total; well within 6-hour limit.

## Data Availability
- **Synthetic Workload**: Data is generated programmatically via `main.cpp`; no external dataset required.
- **Hardware Detection**: `hardware_detect.py` fetches local system info; no external API.
- **Reproducibility**: All data generated on CI; checksums recorded in `state/`.