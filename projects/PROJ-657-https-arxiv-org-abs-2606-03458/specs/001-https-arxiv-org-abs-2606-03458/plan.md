# Implementation Plan: KVarN Variance-Normalized KV-Cache Quantization

**Branch**: `001-kvarn-quantization` | **Date**: 2026-06-20 | **Spec**: `specs/001-kvarn-quantization/spec.md`
**Input**: Feature specification from `/specs/001-kvarn-quantization/spec.md`

## Summary

This project implements KVarN, a variance-normalized KV-cache quantization algorithm designed to mitigate error accumulation in LLM reasoning tasks. The core technical approach involves intercepting KV-cache tensors during autoregressive decoding, computing local variance, and scaling quantization parameters accordingly before applying 8-bit linear quantization. The implementation integrates with the `transformers` library (via a custom forward loop) to evaluate performance against a uniform 8-bit baseline on MATH500, AIME24, HumanEval, and IFEval benchmarks. Success is measured by reduced Mean Squared Error (MSE) in reconstruction, maintained or improved exact-match accuracy, and statistically significant reduction in error accumulation slopes.

> **Spec Deviation Note (FR-003)**: The spec mandates integration into `vllm`. Due to CPU-only constraints (7GB RAM, 6h timeout) and the lack of CPU-compatible custom hook injection in `vllm`, this plan implements the algorithm via `transformers` with a custom generate loop. This satisfies the functional requirement (custom KV quantization) but deviates from the specific engine. **Action Required**: The spec.md file MUST be amended to change FR-003 from "vllm" to "CPU-compatible inference engine (e.g., transformers)".

> **Spec Assumption Correction**: The spec assumes Llama fits in available RAM. This is factually incorrect. This plan uses **Phi-2 (2.7B)** in FP16 to ensure feasibility. **Action Required**: The spec.md Assumptions section MUST be updated to reflect the use of Phi-2.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `transformers`, `torch` (CPU wheel), `datasets`, `scikit-learn`, `pandas`, `numpy`, `pytest`  
**Storage**: Temporary `data/` directory for benchmark datasets (cached), `data/` for experiment logs (CSV/JSONL)  
**Testing**: `pytest` (unit tests for quantizer, integration tests for benchmark runner)  
**Target Platform**: Linux (GitHub Actions Free Tier: Multiple vCPU, 7GB RAM, CPU-only)  
**Project Type**: Research library / Benchmarking suite  
**Performance Goals**: Inference completion within 6 hours for a subset of benchmarks; memory usage < 7GB RAM.  
**Constraints**: No GPU; no CUDA; no 8-bit/4-bit quantization libraries requiring CUDA (bitsandbytes); must run on free-tier CI.  
**Scale/Scope**: Single model (**Phi-2 2.7B** in FP16), 4 reasoning benchmarks, limited sample size per benchmark to fit time/memory constraints.  
**Engine Strategy**: **`transformers` with a custom `generate` loop** to inject KV hooks. This is the ONLY path to ensure per-token variance calculation on CPU. `vllm` is not used due to hook injection limitations on CPU. `llama-cpp-python` is not used due to inability to inject custom Python hooks without C++ rebuild.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, canonical dataset sources (HF Datasets), and isolated virtualenv. |
| **II. Verified Accuracy** | **PASS** | Citations restricted to verified dataset URLs provided in the spec; no invented URLs. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw datasets and immutability of raw data; derivations in new files. |
| **IV. Single Source of Truth** | **PASS** | All metrics (MSE, accuracy) will be logged to `data/` and referenced by code; no hand-typed stats in paper. |
| **V. Versioning Discipline** | **PASS** | Artifacts (code, data) will carry content hashes; state updates tracked. |
| **VI. Numerical Stability** | **PASS** | Explicit plan to clamp variance < 1e-8 (FR-008) and **log per-token MSE to `data/processed/results_*.jsonl`** as required by Principle VI. |
| **VII. Benchmark Reproducibility** | **PASS** | Benchmarks accessed via `datasets.load_dataset` with explicit version pins. |

## Project Structure

### Documentation (this feature)

```text
specs/001-kvarn-quantization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset_schema.schema.yaml
    ├── inference_result_schema.schema.yaml
    └── analysis_summary_schema.schema.yaml
```

### Source Code (repository root)

```text
code/
├── src/
│   ├── __init__.py
│   ├── quantization/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract Quantizer
│   │   ├── uniform.py             # Uniform 8-bit baseline
│   │   └── kvarn.py               # Variance-normalized implementation
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── engine.py              # Transformers wrapper / custom loop
│   │   └── hooks.py               # KV-cache interception logic
│   ├── benchmarks/
│   │   ├── __init__.py
│   │   ├── loader.py              # Dataset loading (MATH, AIME, etc.)
│   │   └── evaluator.py           # Exact match & MSE calculation
│   └── analysis/
│       ├── __init__.py
│       ├── stats.py               # McNemar, t-test, regression
│       └── plots.py               # Error accumulation visualization
├── tests/
│   ├── unit/
│   │   ├── test_quantizer.py
│   │   └── test_hooks.py
│   └── integration/
│       └── test_benchmark_run.py
├── data/
│   ├── raw/                       # Downloaded benchmarks (checksummed)
│   └── processed/                 # Logs, results, checksums
├── requirements.txt
└── run_experiment.py              # Entry point
```

**Structure Decision**: A modular `code/src` layout separating quantization logic, inference hooks, and analysis. This allows unit testing the KVarN algorithm in isolation (US-1) before integrating with the heavy inference engine (US-2). The `data/` directory strictly separates raw benchmarks from processed logs to satisfy Data Hygiene (Principle III). The `contracts/` directory contains the **source of truth** for the JSONL schemas used in `data/processed/`, ensuring synchronization with `data-model.md`. The `contracts` files are explicitly linked to the data flow steps in `data-model.md` to ensure the data model and schemas are synchronized.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Custom `transformers` Hook | KVarN requires per-token variance calculation *during* generation, which standard `transformers` does not expose. | A post-hoc analysis of saved caches is insufficient for "on-the-fly" compression and error accumulation simulation (FR-003). |
| Multiple Benchmarks | To generalize findings beyond a single dataset type (math vs. code vs. instruction). | Single-dataset results would lack external validity for the "Reasoning Tasks" claim. |
| Statistical Rigor | McNemar + Slope Comparison needed to distinguish signal from noise in binary accuracy and continuous error trends. | Simple "accuracy comparison" ignores the error accumulation hypothesis (US-3, FR-010). |
| **Phi-2 (2.7B) Model** | **LlamaB (GB) exceeds the available RAM limit. Phi-2 FP16 fits within 7GB.** | Using 4-bit weights introduces confounds (FR-002). Phi-2 in FP16 is the only feasible CPU-compatible baseline. |
| **No vLLM** | **vLLM CPU hooks for custom quantization are not feasible/available.** | `transformers` allows direct Python hooks for per-token variance calculation. |
| **No llama-cpp-python** | **Cannot inject custom hooks into C++ backend without rebuild.** | `transformers` is the only path for custom Python logic. |
