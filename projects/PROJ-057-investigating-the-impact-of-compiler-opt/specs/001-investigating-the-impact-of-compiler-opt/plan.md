# Implementation Plan: Investigating the Impact of Compiler Optimizations on LLM Inference Latency

**Branch**: `001-investigate-compiler-optimizations` | **Date**: 2024-05-22 | **Spec**: `specs/001-investigating-the-impact-of-compiler-opt/spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-impact-of-compiler-opt/spec.md`

## Summary

This project investigates the trade-off between latency reduction and numerical stability in LLM inference kernels (Matrix Multiplication, Softmax, LayerNorm) when compiled with varying GCC/Clang optimization flags. The technical approach involves a C++ benchmarking harness that generates synthetic tensors (using multiple distinct random seeds with varied distributions to ensure construct validity), compiles kernels with specific flags (e.g., `-O3`, `-ffast-math`), measures execution time over a **fixed [deferred] iterations** per configuration (as mandated by Constitution Principle VII), and compares outputs against a Python `decimal` (512-bit) reference and an `-O0` baseline. Statistical significance is determined via **Welch's Independent Samples t-test** on A set of block-averaged means (block size in the range of one hundred), and results are visualized on a Pareto frontier that includes **all** configurations (stable and unstable) to empirically map the full trade-off landscape.

## Technical Context

**Language/Version**: C++17 (kernels), Python 3.11 (orchestration, stats, visualization)  
**Primary Dependencies**: `numpy`, `scipy`, `matplotlib`, `pyyaml`, `pytest`, `pandas`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`) mapped to **GitHub Actions ephemeral storage**. All artifacts are uploaded as CI artifacts at job completion to ensure reproducibility on fresh runners via deterministic regeneration.  
**Testing**: `pytest` (unit tests for error calculation, integration tests for compilation flow)  
**Target Platform**: Linux (GitHub Actions x86_64 runner)  
**Project Type**: Research Benchmark Suite  
**Performance Goals**: Complete full matrix (optimization levels × 3 kernels × compilers × [deferred] iterations) within 6 hours on 2 CPU cores.
**Constraints**: Must run on CPU-only, ≤7 GB RAM. No GPU. Synthetic tensor size capped at 768x768 (float32).  
**Scale/Scope**: kernel types, 2 compilers, ~flag combinations, **[deferred] total iterations** per configuration (A set of configurations. × [deferred] iterations = measurements).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file:*

1.  **Reproducibility (Principle I)**: **PASS**. Plan mandates fixed random seeds and varied distributions for synthetic data generation. The benchmark script is version-controlled and deterministic; results can be regenerated on a fresh runner by re-executing the script. Storage is mapped to GitHub Actions ephemeral storage, and artifacts are uploaded as CI artifacts to satisfy the "fresh runner" constraint.
2.  **Verified Accuracy (Principle II)**: **PASS**. The Python `decimal` module (-bit precision) serves as the verified "ground truth" reference. No external citations requiring web validation are introduced in the methodology.
3.  **Data Hygiene (Principle III)**: **PASS**. Raw synthetic tensors are generated on-the-fly (no external data). Derived results (CSVs) are written to new filenames. No PII exists in synthetic tensor data.
4.  **Single Source of Truth (Principle IV)**: **PASS**. All figures in the final paper will be generated directly from the CSVs in `data/results` via the plotting script, preventing manual transcription errors.
5.  **Versioning Discipline (Principle V)**: **PASS**. The plan mandates SHA-256 hashing for **compiled binaries**, **final immutable snapshots of raw logs**, **aggregated CSVs**, and **final plots**. These hashes are recorded in a `manifest.json` file within `data/` **after the experiment completes**.
6.  **Numerical Stability (Principle VI)**: **PASS**. The plan explicitly includes a "Stability Check" phase that flags configurations with L2 error > 1e-5. Crucially, the comparative drift analysis is anchored to the **-O0 baseline** as required by the Constitution, while the Python decimal reference serves as the absolute correctness check.
7. **Benchmark Transparency (Principle VII)**: **PASS**. The plan defines exact tensor dimensions (512x512, 768x768) and a **fixed iteration count of [deferred]** per configuration, strictly adhering to the Constitution's hard requirement. The specific compiler versions (GCC recent, Clang recent) are mandated.

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-impact-of-compiler-opt/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-057-investigating-the-impact-of-compiler-opt/
├── code/
│   ├── requirements.txt
│   ├── kernels/                 # C++ source files
│   │   ├── matmul.cpp
│   │   ├── softmax.cpp
│   │   └── layernorm.cpp
│   ├── benchmarks/
│   │   ├── compile_runner.py    # Orchestrates g++/clang++ compilation
│   │   ├── executor.py          # Runs binaries, measures latency
│   │   └── reference.py         # Python decimal reference implementation
│   ├── analysis/
│   │   ├── stability_check.py   # Compares outputs, calculates L2/MaxDiff
│   │   ├── stats.py             # Welch's t-tests, significance
│   │   └── viz.py               # Pareto frontier plotting
│   └── main.py                  # Entry point for full experiment
├── data/
│   ├── raw/                     # Synthetic tensors (generated on fly)
│   ├── intermediates/           # Binary executables, raw timing logs
│   └── results/                 # Final CSVs, plots, summary tables, manifest.json
└── tests/
    ├── unit/
    │   ├── test_stability.py
    │   └── test_stats.py
    └── integration/
        └── test_compile_run.py
```

**Structure Decision**: Selected a modular Python-based orchestration with C++ kernels. This allows rapid iteration on statistical analysis (Python) while leveraging native speed for kernel execution (C++). The separation of `kernels/`, `benchmarks/`, and `analysis/` ensures that the compilation logic is distinct from the statistical evaluation, satisfying the "Single Source of Truth" requirement by keeping raw results separate from derived analysis.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual Compiler Support (GCC & Clang) | Compiler-specific optimizations (e.g., vectorization strategies) differ significantly between GCC and Clang. | Using only one compiler would miss critical variance in the "compiler impact" variable. |
| -bit Decimal Reference | Standard `float64` (double) is insufficient to detect drift caused by `-ffast-math` which may drop precision to `float32` or lower. | Using `float64` as reference would result in false negatives for stability failures. |
| **Welch's Independent Samples t-test** | Each configuration uses a distinct binary; samples are independent, not paired. | Paired t-tests require the same subject under two conditions, which is impossible here. |
| **Multi-Seed Data (Multiple sets)** | Single random seed may not capture instability in specific activation patterns. | A single seed risks false negatives for stability failures on unseen data distributions. |
| **Fixed [deferred] Iterations** | Adaptive stopping based on CV introduces selection bias and invalidates t-test assumptions. | Adaptive stopping creates a non-independent sample distribution. A fixed number of iterations allows for multiple blocks, providing sufficient degrees of freedom for statistical testing. |

## Versioning Manifest

To satisfy Constitution Principle V, the following artifacts will be hashed (SHA-256) and recorded in `data/manifest.json` **after the experiment completes**:
1.  **Compiled Binaries**: Each unique executable in `data/intermediates/binaries/`.
2.  **Raw Logs**: `data/intermediates/raw_logs/*.jsonl` (final immutable snapshots).
3.  **Aggregated Results**: `data/results/aggregated.csv`.
4.  **Final Plots**: `data/results/pareto_plot.png`.