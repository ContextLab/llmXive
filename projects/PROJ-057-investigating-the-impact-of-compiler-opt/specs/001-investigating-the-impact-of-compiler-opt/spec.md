# Project Specification: Investigating the Impact of Compiler Optimizations on LLM Inference Latency

## 1. Introduction

This project investigates the impact of compiler optimization flags on the latency and numerical stability of LLM inference kernels. The goal is to provide data-driven insights into the trade-offs between performance and accuracy for different optimization levels.

## 2. User Stories

### US1: Compile and Execute Kernel Benchmarks
As a researcher, I want to compile C++ kernels with varying optimization flags and execute them to measure latency, so that I can establish a baseline performance profile for each configuration.

### US2: Quantify Numerical Stability Drift
As a researcher, I want to compare optimized kernel outputs against a high-precision reference to calculate relative error and max absolute difference, so that I can assess the numerical stability of each optimization level.

### US3: Statistical Significance and Pareto Frontier Analysis
As a researcher, I want to perform statistical tests on block-averaged latency distributions and generate Pareto frontier plots, so that I can identify optimal configurations that balance speed and accuracy.

## 3. Functional Requirements

### FR-001: Compiler Flag Configuration
The system must support dynamic generation of compiler flag combinations from a user-supplied YAML/JSON list.

### FR-002: Deterministic Tensor Generation
The system must generate deterministic synthetic tensors using fixed seeds and varied distributions to ensure construct validity.

### FR-003: High-Precision Reference Engine
The system must implement a high-precision reference engine using Python `decimal` module with 512-bit precision for MatMul, Softmax, and LayerNorm operations.

### FR-004: Statistical Analysis
The system must perform **Welch's Independent Samples t-test** to compare optimization levels (p<0.05 threshold) for independent binaries (different compilers/flags). This statistical method is required because the binaries are independent samples, not paired observations, and Welch's test does not assume equal variances, providing a more robust comparison for performance metrics which often exhibit heteroscedasticity.

### FR-005: Pareto Frontier Visualization
The system must generate Pareto frontier plots including:
- Exploration plot: ALL configurations (stable and unstable), with distinct visual indicators for downsampled and unstable configurations.
- Final plot: Strictly excluding configurations with error > 1e-5 (numerically unstable).

### FR-006: Memory Pressure Handling
The system must implement memory fallback: if 768x768 allocation fails, auto-downsample to 512x512, log 'Memory Pressure' with the new dimension ID, and continue execution.

### FR-007: NaN Detection and Exclusion
The system must detect NaNs in output tensors, log specific flag configurations causing stability failures, and exclude them from statistical analysis while retaining them in raw logs.

## 4. Non-Functional Requirements

### NFR-001: Reproducibility
All experiments must be reproducible with fixed seeds and deterministic execution.

### NFR-002: Performance
The system must complete a full experiment within a 6-hour runtime budget on a CPU-only, multi-core, constrained RAM environment.

### NFR-003: Code Quality
The codebase must adhere to PEP 8 standards, with a maximum cyclomatic complexity of 10 per function.

## 5. Data Model

### Raw Logs
JSONL format with schema:
```json
{
 "config_id": "string",
 "kernel": "string",
 "compiler": "string",
 "flags": ["string"],
 "median_ms": float,
 "p95_ms": float,
 "iterations": int,
 "downsampled": bool,
 "tensor_dim": "string"
}
```

### Stability Metrics
CSV format with columns: `config_id`, `kernel_type`, `l2_error`, `max_diff`, `status`.

### Block-Averaged Data
CSV format containing aggregated latency distributions for statistical testing.

## 6. Edge Cases

### NaN Detection
- Log specific flag configuration
- Exclude from statistical analysis
- Retain in raw logs

### Memory Pressure
- Auto-downsample from 768x768 to 512x512
- Log 'Memory Pressure' event
- Continue execution with downsampled configuration

### Compiler Version Validation
- Fail immediately if GCC < 11 or Clang < 14
- Clear error message citing minimum requirement

## 7. Validation and Verification

### Verification Steps
1. Run `python code/benchmarks/config.py --generate-combinations --input flags.yaml` to verify dynamic flag generation.
2. Run `python code/benchmarks/tensor_generator.py --seed <SEED> --verify-hash` to verify deterministic tensor generation.
3. Run `python code/benchmarks/reference.py --test --verify-hash` to verify high-precision reference engine.
4. Run `python code/benchmarks/executor.py --test` to verify binary execution and latency measurement.
5. Run `python code/analysis/stability_check.py --detect-nan` to verify NaN detection and filtering.
6. Run `python code/analysis/stats.py --t-test` to verify Welch's t-test implementation.
7. Run `python code/analysis/viz.py --plot-exploration` to verify Pareto exploration plot generation.
8. Run `python code/analysis/viz.py --plot-final` to verify Pareto final plot generation.

### Validation Report
Generate `validation_report.json` with pass/fail status for each quickstart step.

## 8. Appendix

### Compiler Flags Reference
- `-O0`: No optimization
- `-O1`: Basic optimization
- `-O2`: Moderate optimization
- `-O3`: Aggressive optimization
- `-Os`: Optimize for size
- `-march=native`: Optimize for native architecture
- `-ffast-math`: Fast but potentially less accurate math
- `-funroll-loops`: Unroll loops for performance

### Statistical Methods
- **Welch's Independent Samples t-test**: Used for comparing independent binaries with potentially unequal variances.
- **Block Averaging**: Aggregating latency measurements into blocks to reduce variance and improve statistical power.