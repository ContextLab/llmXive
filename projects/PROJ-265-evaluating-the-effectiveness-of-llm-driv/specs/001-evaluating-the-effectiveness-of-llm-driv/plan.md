# Implementation Plan: Evaluating the Effectiveness of LLM-Driven Code Simplification on Performance

**Branch**: `001-evaluating-llm-code-simplification` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-evaluating-the-effectiveness-of-llm-driv/spec.md`

## Summary

This project evaluates whether LLM-driven code simplification improves the execution time and memory usage of Python functions. The approach involves downloading a subset of Python functions from CodeSearchNet, filtering for executability, simplifying them using a quantized CodeLlama-3B model, verifying functional equivalence via a deterministic test-generation step (or existing tests), and benchmarking performance differences using a paired statistical test on a CPU-only CI runner.

**Critical Methodology Correction**: This plan strictly adheres to Constitution Principle VI by enforcing **exactly 100 iterations** per function (fixed, not adaptive) and requires **functional equivalence verification for ALL functions** (no exemption for short code). The statistical test is performed on the **function-level means** (N=100), not the raw iteration logs, to avoid pseudoreplication.

**Note on Spec Contradictions**: The source `spec.md` contains FR-003 (adaptive iterations), FR-006 (random inputs), FR-007 (skip short functions), and FR-008 (pilot power analysis) which contradict this plan and the Constitution. This plan implements the corrected methodology (fixed 100, deterministic tests, all functions, no pilot). **The `spec.md` has been flagged for kickback to resolve these root-cause contradictions.**

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `torch` (CPU build), `accelerate` (CPU mode), `scikit-learn`, `pandas`, `numpy`, `pytest`, `tracemalloc` (stdlib), `time` (stdlib), `datasets`  
**Storage**: Local filesystem (`data/raw`, `data/processed`), JSON/Parquet for results  
**Testing**: `pytest` (unit tests for preprocessing, integration tests for pipeline, statistical validation)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Process **100 functions** within 6 hours; LLM inference <60s per function; benchmarking (100 iterations) <0.5s per execution  
**Constraints**: No GPU; RAM <7 GB; disk <14 GB; hard timeout per function execution; memory limit set to a fixed, moderate capacity per execution; **Fixed 100 iterations per function.**  
**Scale/Scope**: A set of Python functions; A quantized LLM model

> Dataset sizes and empirical specifics are deferred to research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| I. Reproducibility | ✅ | Random seeds pinned; dataset fetched from canonical HuggingFace API; `requirements.txt` pins versions. |
| II. Verified Accuracy | ✅ | Only verified dataset URLs from `# Verified datasets` block used; no invented citations. |
| III. Data Hygiene | ✅ | Raw data preserved; checksums recorded; no in-place modification; PII scan enforced. |
| IV. Single Source of Truth | ✅ | All stats derived from `data/` and `code/`; no hand-typed numbers in paper. |
| V. Versioning Discipline | ✅ | Content hashes tracked; artifact update timestamps enforced. |
| VI. Performance Measurement Integrity | ✅ | `time` and `tracemalloc` used; **exactly 100 iterations** enforced; **statistical test performed on function means** (N=100); paired statistical analysis. |
| VII. Resource-Constrained Execution | ✅ | CodeLlama-3B 4-bit quantized; **Target: 100 functions**; 100 iterations per function; parallel processing via `multiprocessing`; total runtime <6h. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-llm-code-simplification/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-265-evaluating-the-effectiveness-of-llm-driv/code/
├── data/
│   ├── download.py          # Downloads and validates CodeSearchNet subset
│   ├── preprocess.py        # Isolates functions, mocks dependencies, generates tests
│   └── equivalence.py       # Functional equivalence checker (runs tests)
├── models/
│   ├── simplify.py          # LLM simplification pipeline
│   └── benchmark.py         # Performance measurement engine
├── analysis/
│   ├── stats.py             # Statistical testing (t-test/Wilcoxon + correction)
│   └── power.py             # (Removed: Pilot power analysis omitted)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── main.py                  # Orchestrates pipeline
└── requirements.txt         # Pinned dependencies

data/
├── raw/                     # Downloaded parquet files
├── processed/               # Validated, isolated functions with generated tests
└── results/                 # Benchmark results, stats summaries
```

**Structure Decision**: Single project structure selected to minimize overhead. All components reside under `code/` with clear separation of concerns: data, models, analysis, tests. This aligns with the research nature of the project and ensures reproducibility.

## Complexity Tracking

No violations detected. All principles are satisfied without introducing unnecessary complexity.

**Note on Spec Contradictions**: The source `spec.md` contains FR-003 (adaptive iterations), FR-006 (random inputs), FR-007 (skip short functions), and FR-008 (pilot power analysis) which contradict this plan and the Constitution. This plan implements the corrected methodology (fixed 100, deterministic tests, all functions, no pilot). **The `spec.md` has been flagged for kickback to resolve these root-cause contradictions.**