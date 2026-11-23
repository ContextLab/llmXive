# Architecture Overview

## Design Philosophy

This benchmark suite is designed to rigorously evaluate the trade-offs between compiler optimization levels and numerical stability in LLM inference kernels. The architecture follows a modular pipeline:

1. **Data Generation**: Deterministic synthetic tensors are generated to ensure construct validity.
2. **Reference Calculation**: High-precision (512-bit) reference outputs are computed using Python's `decimal` module.
3. **Compilation & Execution**: C++ kernels are compiled with varying optimization flags and executed to measure latency.
4. **Stability Analysis**: Optimized outputs are compared against references to detect numerical drift.
5. **Statistical Analysis**: Latency distributions are analyzed using Welch's t-test to determine significance.
6. **Visualization**: Pareto frontiers and error distributions are plotted to identify optimal configurations.

## Component Breakdown

### Kernels (`code/kernels/`)

- **matmul.cpp**: Implements matrix multiplication using float32.
- **softmax.cpp**: Implements the softmax function.
- **layernorm.cpp**: Implements layer normalization.

All kernels are compiled with C++17 and support dynamic flag injection.

### Benchmarks (`code/benchmarks/`)

- **tensor_generator.py**: Generates deterministic input tensors with fixed seeds.
- **reference.py**: Computes high-precision reference outputs.
- **config.py**: Manages compiler flags and tensor dimensions.
- **compile_runner.py**: Orchestrates compilation and binary hashing.
- **executor.py**: Runs binaries, measures latency, and handles memory pressure.

### Analysis (`code/analysis/`)

- **stability_check.py**: Detects NaNs, calculates L2 error, and flags unstable configurations.
- **stats.py**: Performs block averaging and Welch's t-test.
- **viz.py**: Generates Pareto frontier plots and error distribution charts.
- **aggregator.py**: Aggregates results into final CSVs and reports.

### Utilities (`code/utils/`)

- **logger.py**: Centralized logging for compiler versions, flags, and warnings.
- **manifest_generator.py**: Generates SHA-256 hashes for reproducibility.

## Data Flow

```
[Tensor Generator] --> [Reference Engine] --> [Compiler/Executor] --> [Stability Check] --> [Stats & Viz]
 (data/raw) (data/raw) (data/intermediates) (data/results) (data/results)
```

## Configuration Management

The `ConfigManager` class in `benchmarks/config.py` centralizes all configuration parameters:
- Compiler flags
- Tensor dimensions
- Iteration counts
- Stability thresholds

## Reproducibility

All outputs are hashed and recorded in `data/manifest.json` to ensure reproducibility and auditability.

## Extensibility

New kernels, flags, or analysis methods can be added by extending the respective modules without altering the core pipeline.
