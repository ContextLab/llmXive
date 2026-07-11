# Implementation Plan: Evaluating the Effectiveness of LLM-Driven Code Simplification on Performance

**Branch**: `001-evaluating-llm-code-simplification` | **Date**: 2026-07-04 | **Spec**: `specs/001-evaluating-the-effectiveness-of-llm-driv/spec.md`

## Summary

This project evaluates whether LLM-driven code simplification improves execution time and memory usage in Python functions. The approach involves downloading a stratified sample of functions from CodeSearchNet, simplifying them using a quantized CodeLlama model (4-bit, CPU-only), verifying functional equivalence via type-aware random inputs and AST diff, and performing a rigorous paired statistical analysis (t-test or Wilcoxon) on the distribution of trimmed means from multiple iterations per function version. The entire pipeline is designed to run within the limited duration, memory, and CPU-only constraints of a GitHub Actions free-tier runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (for CodeSearchNet), `transformers` + `accelerate` (for LLM inference), `torch` (CPU-only), `scikit-learn` (statistics), `tracemalloc` (built-in), `time` (built-in), `ast` (built-in), `pytest` (testing).  
**Storage**: Local `data/raw`, `data/processed`, `results/` (CSV/Parquet).  
**Testing**: `pytest` with strict timeout and memory constraints.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Research/Computational Experiment.  
**Performance Goals**: Complete 200 function pairs (inference + 100 benchmarks each) in ≤6 hours.  
**Constraints**: Max constrained RAM, Max s timeout per execution, The study investigates memory constraints per execution using a controlled benchmarking method (Author et al.,), limiting the resource allocation to a moderate threshold., No GPU.  
**Scale/Scope**: A set of function pairs, [deferred] total benchmark runs (100 per version per pair).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. Dataset fetched via canonical HuggingFace URL. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to the "Verified datasets" block. No external URLs invented. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw`. Derivations (filtered, simplified) written to new files with checksums. PII scan enabled. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` will be generated directly from `results/summary.csv`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in `state/`. Artifact updates trigger timestamp refresh via `checksum.py` script. |
| **VI. Performance Measurement Integrity** | **PASS** | Strict adherence to `time.perf_counter()` and `tracemalloc`. A fixed number of iterations per version. Trimmed mean aggregation before testing. |
| **VII. Resource-Constrained Execution** | **PASS** | Quantized CodeLlama on CPU. Dataset limited to a manageable subset of functions. Batched execution to fit 6h window. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-llm-code-simplification/
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
├── data/
│   ├── download.py          # Downloads CodeSearchNet parquet
│   ├── extract.py           # AST extraction of standalone functions
│   ├── validate.py          # Syntax check, import mocking
│   └── preprocess.py        # Sanitization (I/O, network removal)
├── models/
│   ├── loader.py            # Loads quantized CodeLlama-3B (4-bit)
│   └── simplify.py          # Runs inference loop
├── benchmark/
│   ├── runner.py            # Executes code 100x with time/tracemalloc (batched)
│   ├── equivalence.py       # Functional diff (Type-aware random + AST)
│   └── stats.py             # Normality check, t-test/Wilcoxon, Bonferroni
├── utils/
│   ├── sandbox.py           # Timeout/Memory enforcement
│   └── logger.py            # Structured logging
├── main.py                  # Orchestrator (Pipeline)
└── tests/
    ├── test_pipeline.py
    └── test_equivalence.py

data/
├── raw/                     # Original parquet files (checksummed)
├── processed/               # Filtered, sanitized, simplified code
└── results/                 # Benchmark logs, stats summaries
```

**Structure Decision**: Single project structure under `code/` with clear separation of data, model, and benchmarking logic to facilitate modular testing and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Functional Equivalence Check (Type-aware Random + AST)** | Necessary to ensure simplification didn't alter behavior (FR-006). | Pure uniform random is insufficient; pure AST diff misses semantic drift. Combined approach balances rigor and feasibility while adhering to spec. |
| **Multiple Iterations per Version

A sufficient number of iterations will be performed for each version to ensure convergence and robustness of the results, without pre-specifying an exact count.** | Required for statistical power (FR-003, SC-001). | A high number of iterations would introduce too much variance.; A large-scale dataset would exceed 6h runtime. |
| **Quantized LLM (4-bit)** | Required to fit 7GB RAM (FR-002, Const VII). | Full precision models exceed memory; CPU-only inference of large models is too slow. |
| **Batched Execution** | Required to minimize Python startup overhead ([deferred] runs). | Running [deferred] separate processes would exceed 6h due to startup cost. |
| **Trimmed Mean Aggregation** | Required to mitigate system noise (CI runner variance). | Simple mean is too sensitive to outliers in micro-benchmarking. |

## Versioning Mechanism

To satisfy Constitution Principle V:
1. A `checksum.py` script will be executed post-pipeline.
2. It computes SHA-256 hashes of all files in `data/` and `results/`.
3. It updates `state/projects/PROJ-265-...yaml` with the new `artifact_hashes` and `updated_at` timestamp.
4. The `Advancement-Evaluator` will verify these hashes before allowing stage transition.

## Dataset Extraction Strategy

The CodeSearchNet dataset provides raw `.py` files, not pre-extracted functions.
1. **Ingestion**: Download raw parquet.
2. **Extraction**: Use `ast.parse` to isolate top-level function definitions.
3. **Filtering**: Keep functions with a minimal number of external imports, no class dependencies.
4. **Sanitization**: Mock imports, remove I/O/network calls.
5. **Validation**: Run in sandbox; exclude failures.

This extraction pipeline is a critical path item and will be validated in the pilot phase.